"""Tests for foxit_pr_check.py: commit messages and PR descriptions alone, then whole branches in throwaway git
repositories whose remote points at a fox-it repository. Run: python3 -m unittest discover -s scripts"""

import ast
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foxit_pr_check as check  # noqa: E402


def rules(findings, level=None):
    return {f.rule for f in findings if level is None or f.level == level}


GOOD = """Fix searching a B-tree node without keys

BTree._node_search raised UnboundLocalError on a node with no keys: the
binary search loop never ran. An empty node now returns -1.

Fixes #12
"""


class MessageTests(unittest.TestCase):
    def test_a_good_message_passes(self):
        self.assertEqual(rules(check.check_message(GOOD), "FAIL") | rules(check.check_message(GOOD), "WARN"), set())

    def test_subject_rules(self):
        self.assertIn("commit-capital", rules(check.check_message("fix the parser\n"), "FAIL"))
        self.assertIn("commit-period", rules(check.check_message("Fix the parser.\n"), "FAIL"))
        self.assertIn("commit-subject-length", rules(check.check_message("Fix " + "x" * 50 + "\n"), "WARN"))
        self.assertIn("commit-subject-length", rules(check.check_message("Fix " + "x" * 80 + "\n"), "FAIL"))
        for subject in ("Fixed the parser", "Fixes the parser", "Adding a parser", "Updates the docs"):
            self.assertIn("commit-imperative", rules(check.check_message(subject + "\n"), "WARN"), subject)
        for subject in ("Address a review comment", "Process extents in order", "Bypass the cache", "Fix it"):
            self.assertNotIn("commit-imperative", rules(check.check_message(subject + "\n")), subject)

    def test_body_rules(self):
        self.assertIn("commit-blank-line", rules(check.check_message("Fix a bug\nno blank line\n"), "FAIL"))
        self.assertIn("commit-body-wrap", rules(check.check_message("Fix a bug\n\n" + "word " * 20 + "\n"), "WARN"))
        url = "Fix a bug\n\nSee https://example.com/" + "a" * 80 + "\n"
        self.assertNotIn("commit-body-wrap", rules(check.check_message(url)))

    def test_ai_attribution_is_refused(self):
        for trailer in ("Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>", "Claude-Session: https://x",
                        "🤖 Generated with [Claude Code](https://claude.com/claude-code)"):
            self.assertIn("ai-attribution", rules(check.check_message(GOOD + "\n" + trailer + "\n"), "FAIL"))
        human = GOOD + "\nCo-Authored-By: Jane Doe <jane@example.com>\n"
        self.assertNotIn("ai-attribution", rules(check.check_message(human)))


class PrBodyTests(unittest.TestCase):
    def test_a_good_body(self):
        body = ("An empty node now returns -1, which search() already reports as a missing key.\n\n"
                "How to test: tox -e py3 -- tests/test_btree.py\n\nFixes #12\n")
        self.assertEqual(rules(check.check_pr_body(body), "FAIL") | rules(check.check_pr_body(body), "WARN"), set())

    def test_the_template_comment_alone_is_not_a_description(self):
        body = "<!--\nThank you for submitting a Pull Request. Please: fixes #1 test\n-->\n"
        found = check.check_pr_body(body)
        self.assertIn("pr-description", rules(found, "FAIL"))
        self.assertIn("pr-closing-keyword", rules(found, "WARN"))

    def test_closing_keywords_as_the_template_lists_them(self):
        for keyword in ("close", "closes", "closed", "fix", "fixes", "fixed", "resolve", "resolves", "resolved"):
            self.assertTrue(check.CLOSING.search(f"{keyword} #7"), keyword)
        self.assertTrue(check.CLOSING.search("Fixes fox-it/dissect.apfs#12"))


class AstTests(unittest.TestCase):
    def test_names_hints_and_cstruct(self):
        source = ("def f(a, data: bytes):\n"
                  "    list = [a]\n"
                  "    c_x = cstruct().load('struct x { uint8 y; };')\n"
                  "    return list\n")
        found = check.check_ast("mod.py", ast.parse(source), set(range(1, 5)))
        messages = " ".join(f.message for f in found)
        self.assertIn("type-hints", rules(found))
        self.assertIn("single-character name 'a'", messages)
        self.assertIn("'list' is named after its type", messages)
        self.assertIn("cstruct-split", rules(found))

    def test_only_added_lines_count(self):
        found = check.check_ast("mod.py", ast.parse("def f(a):\n    return a\n"), set())
        self.assertEqual(found, [])

    def test_a_definition_loaded_by_name_is_fine(self):
        found = check.check_ast("mod.py", ast.parse("c_def = 'struct x { uint8 y; };'\nc_x = cs.load(c_def)\n"),
                                {1, 2})
        self.assertNotIn("cstruct-split", rules(found))


class BranchTests(unittest.TestCase):
    """Whole branches, in a throwaway repository whose `upstream` remote is a fox-it URL."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.repo = self.dir.name
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write("pkg/mod.py", "def g() -> int:\n    return 1\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "Initial")
        self.git("remote", "add", "upstream", "https://github.com/fox-it/dissect.example.git")
        self.git("update-ref", "refs/remotes/upstream/main", "HEAD")

    def tearDown(self):
        self.dir.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", self.repo, *args], check=True, capture_output=True)

    def write(self, path, text):
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-q", "-m", message)

    def run_check(self, *extra):
        args = check.argparse.Namespace(repo=self.repo, base=None, pr_body=None, pr=None, run_tox=False, tox=None,
                                        check_cla=False, json=False)
        for key, value in extra:
            setattr(args, key, value)
        return check.run(args)

    def test_a_clean_fix_branch(self):
        self.git("checkout", "-q", "-b", "fix/thing")
        self.write("pkg/mod.py", "def g() -> int:\n    return 2\n")
        self.write("tests/test_mod.py", "def test_g() -> None:\n    assert True\n")
        self.commit(GOOD)
        found = self.run_check()
        self.assertEqual(rules(found, "FAIL"), set())
        self.assertEqual(rules(found, "WARN"), set())

    def test_the_branch_the_base_and_missing_tests(self):
        self.write("pkg/mod.py", "def g() -> int:\n    return 3\n")
        self.commit("updated the thing.")
        found = self.run_check()
        self.assertIn("branch-name", rules(found, "FAIL"))           # on main
        self.assertIn("commit-capital", rules(found, "FAIL"))
        self.git("checkout", "-q", "-b", "my-branch")
        found = self.run_check()
        self.assertIn("branch-name", rules(found, "WARN"))
        self.assertIn("tests-added", rules(found, "WARN"))

    def test_not_a_fox_it_repository(self):
        self.git("remote", "remove", "upstream")
        self.assertIn("repo-target", rules(self.run_check(), "FAIL"))

    def test_a_stale_base_and_several_commits(self):
        self.git("checkout", "-q", "-b", "fix/a")
        self.write("pkg/a.py", "x = 1\n")
        self.commit("Add a")
        self.write("pkg/b.py", "y = 2\n")
        self.commit("Add b")
        self.git("checkout", "-q", "main")
        self.write("pkg/c.py", "z = 3\n")
        self.commit("Add c")
        self.git("update-ref", "refs/remotes/upstream/main", "HEAD")
        self.git("checkout", "-q", "fix/a")
        found = self.run_check()
        self.assertIn("base-current", rules(found, "WARN"))
        self.assertIn("one-change", rules(found, "WARN"))

    def test_a_dependency_without_a_reason(self):
        self.git("checkout", "-q", "-b", "feature/dep")
        self.write("pyproject.toml", '[project]\ndependencies = [\n  "requests>=2",\n]\n')
        self.commit("Add an HTTP client")
        self.assertIn("deps-reason", rules(self.run_check(), "WARN"))


class EncodingTests(unittest.TestCase):
    """Windows cp1252 stdout (the repository's ef28398): no UnicodeEncodeError, text or JSON."""

    def test_cp1252_stdout(self):
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "-C", repo, "init", "-q", "-b", "main"], check=True)
            subprocess.run(["git", "-C", repo, "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", repo, "config", "user.name", "T"], check=True)
            subprocess.run(["git", "-C", repo, "commit", "-q", "--allow-empty", "-m", "Initial"], check=True)
            subprocess.run(["git", "-C", repo, "remote", "add", "upstream",
                            "https://github.com/fox-it/dissect.example.git"], check=True)
            subprocess.run(["git", "-C", repo, "update-ref", "refs/remotes/upstream/main", "HEAD"], check=True)
            subprocess.run(["git", "-C", repo, "checkout", "-q", "-b", "fix/caf\u00e9-\u2615"], check=True)
            subprocess.run(["git", "-C", repo, "commit", "-q", "--allow-empty", "-m", "Fix caf\u00e9 \u2615 handling"],
                           check=True)
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foxit_pr_check.py")
            env = dict(os.environ, PYTHONIOENCODING="cp1252")
            for extra in ([], ["--json"]):
                done = subprocess.run([sys.executable, script, repo, *extra], capture_output=True, env=env)
                self.assertNotIn(b"UnicodeEncodeError", done.stderr)
                self.assertIn(done.returncode, (0, 1))
                if extra:
                    self.assertTrue(all(byte < 128 for byte in done.stdout))   # ASCII JSON


if __name__ == "__main__":
    unittest.main()
