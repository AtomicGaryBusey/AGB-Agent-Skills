#!/usr/bin/env python3
"""Heuristic checker for ASD-STE100 Simplified Technical English (STE).

The checker reads prose files (Markdown, plain text, reStructuredText,
AsciiDoc), removes the text that must stay exact (code, commands, URLs, file
paths, link targets, HTML), and reports possible violations of the writing
rules in Part 1 of ASD-STE100 Issue 9. Rule IDs use the section and rule
numbers of the specification (for example STE-5.1). The general
recommendations of Section 9 have IDs STE-GR-<n>. Checks that belong to no
rule have IDs of the form STE-X-<NAME>.

Vocabulary checks need the dictionary cache that tools/build_dictionary.py
makes from your own copy of the specification. Without the cache, the checker
does all other checks and reports one INFO finding.

This is an aid, not a certified checker. A clean result does not prove
conformance, and some findings are false positives. Judgment decides.

Python 3.9 or later. Standard library only.
"""

import argparse
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

VERSION = "2.2.0"

SEVERITIES = ("info", "warn")
SEV_RANK = {"info": 0, "warn": 1}

PROSE_EXT = {
    ".md": "md", ".markdown": "md", ".mdown": "md", ".mkd": "md", ".mdx": "md",
    ".txt": "txt", ".text": "txt",
    ".rst": "rst", ".rest": "rst",
    ".adoc": "adoc", ".asciidoc": "adoc", ".asc": "adoc",
}
CODE_EXT = {
    ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".c", ".h",
    ".cc", ".cpp", ".hpp", ".cs", ".java", ".kt", ".swift", ".m", ".rb", ".php", ".pl",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".xml", ".html", ".htm", ".css", ".scss", ".sql", ".lua",
    ".r", ".scala", ".dart", ".vue", ".svelte", ".lock", ".csv", ".tsv", ".ipynb",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".zip", ".gz", ".tar",
}
SKIP_DIRS = {"node_modules", "vendor", "venv", "__pycache__", "site-packages", "dist",
             "build", "target", "_build"}

DEFAULT_DICT_REL = os.path.join(".cache", "ste100-dictionary.json")

# --------------------------------------------------------------------------
# Rule catalogue. Titles are short paraphrases. Judgment:
#   objective  - mechanical check
#   heuristic  - pattern-based guess, false positives expected
#   editorial  - needs human judgment; not checked by this script
# --------------------------------------------------------------------------

RULES = OrderedDict()


def _rule(rid, title, judgment, needs_dict=False, checked=True):
    RULES[rid] = OrderedDict([("id", rid), ("title", title), ("judgment", judgment),
                              ("needs_dictionary", needs_dict), ("checked", checked)])


_rule("STE-1.1", "Only approved words, technical nouns, technical verbs", "objective", True)
_rule("STE-1.2", "Approved word in its approved part of speech", "heuristic", True)
_rule("STE-1.3", "Approved word in its approved meaning", "editorial", True, False)
_rule("STE-1.4", "Listed verb and adjective forms only", "objective", True)
_rule("STE-1.5", "Technical noun categories", "editorial", False, False)
_rule("STE-1.6", "Unlisted word only as a technical noun", "heuristic", True)
_rule("STE-1.7", "Technical noun not used as a verb", "heuristic", False)
_rule("STE-1.8", "Technical nouns approved for the field", "editorial", False, False)
_rule("STE-1.9", "Short, clear technical nouns", "editorial", False, False)
_rule("STE-1.10", "No slang or jargon as technical nouns", "editorial", False, False)
_rule("STE-1.11", "One technical noun for one item (term list 'do not use' words)",
      "objective", False)
_rule("STE-1.12", "Technical verb categories", "editorial", False, False)
_rule("STE-1.13", "Technical verb not used as a noun", "heuristic", False)
_rule("STE-1.14", "American English spelling", "objective", False)
_rule("STE-2.1", "Multi-word noun of three words maximum", "heuristic", False)
_rule("STE-2.2", "Long technical noun in full first (abbreviation check)", "heuristic", False)
_rule("STE-3.1", "Verb forms from the dictionary (reported as STE-1.4)", "objective", True,
      False)
_rule("STE-3.2", "Approved tenses only (no progressive)", "heuristic", False)
_rule("STE-3.3", "Past participle as an adjective", "heuristic", False, False)
_rule("STE-3.4", "No complex auxiliary verb constructions", "heuristic", False)
_rule("STE-3.5", "-ing form only in a technical noun", "heuristic", False)
_rule("STE-3.6", "Active voice", "heuristic", False)
_rule("STE-3.7", "Verb, not noun, for an action", "heuristic", True)
_rule("STE-4.1", "Short and clear sentences", "editorial", False, False)
_rule("STE-4.2", "No omitted words, no contractions", "heuristic", False)
_rule("STE-4.3", "Vertical lists for complex text", "heuristic", False)
_rule("STE-4.4", "Connecting words between related sentences", "editorial", False, False)
_rule("STE-4.5", "Article or demonstrative before a noun", "heuristic", True)
_rule("STE-5.1", "Procedural sentence: 20 words maximum", "objective", False)
_rule("STE-5.2", "One instruction per sentence", "heuristic", False)
_rule("STE-5.3", "Instructions in the imperative", "heuristic", False)
_rule("STE-5.4", "Condition first, then comma, then command", "heuristic", False)
_rule("STE-5.5", "Notes give information only", "heuristic", False)
_rule("STE-6.1", "Information given gradually", "editorial", False, False)
_rule("STE-6.2", "Key words for logical structure", "editorial", False, False)
_rule("STE-6.3", "Descriptive sentence: 25 words maximum", "objective", False)
_rule("STE-6.4", "Paragraphs for related information", "editorial", False, False)
_rule("STE-6.5", "One topic per paragraph", "editorial", False, False)
_rule("STE-6.6", "Six sentences per paragraph maximum", "objective", False)
_rule("STE-7.1", "Signal word that shows the risk level", "heuristic", False)
_rule("STE-7.2", "Safety instruction starts with command or condition", "heuristic", False)
_rule("STE-7.3", "Safety instruction explains the risk", "heuristic", False)
_rule("STE-8.1", "No semicolon", "objective", False)
_rule("STE-8.2", "Hyphens for directly related words", "editorial", False, False)
_rule("STE-8.3", "Permitted uses of parentheses", "editorial", False, False)
_rule("STE-8.4", "Word count: list colon ends a sentence", "objective", False, False)
_rule("STE-8.5", "Word count: parenthesized text is one word", "objective", False, False)
_rule("STE-8.6", "Word count: elements that count as one word", "objective", False, False)
_rule("STE-8.7", "Word count: hyphenated group is one word", "objective", False, False)
_rule("STE-9.1", "Different construction when a swap fails", "editorial", False, False)
_rule("STE-9.2", "Each approved word used correctly", "editorial", False, False)
_rule("STE-9.3", "No phrasal verbs", "heuristic", False)
_rule("STE-9.4", "Consistent terminology and wording", "editorial", False, False)
_rule("STE-GR-1", "Keep the conjunction 'that' (recommendation)", "editorial", False, False)
_rule("STE-GR-2", "Reread sentences with 'with' (recommendation)", "editorial", False, False)
_rule("STE-GR-3", "Clear pronouns (recommendation)", "editorial", False, False)
_rule("STE-GR-4", "One clear referent for 'this' (recommendation)", "editorial", False, False)
_rule("STE-GR-5", "False friends (recommendation)", "editorial", False, False)
_rule("STE-GR-6", "No Latin abbreviations (recommendation)", "objective", False)
_rule("STE-GR-7", "Gender-neutral language (recommendation)", "heuristic", False)
_rule("STE-GR-8", "Possessive form with care (recommendation)", "editorial", False, False)
_rule("STE-X-NODICT", "Dictionary cache missing: vocabulary skipped", "objective", False)
_rule("STE-X-OBLIGATION", "'shall'/'should' as obligation (no dictionary only)", "heuristic",
      False)
_rule("STE-X-FIRST-PERSON", "First person singular (checker heuristic)", "heuristic", False)
_rule("STE-X-SLASH", "Slash between words (checker heuristic)", "heuristic", False)

# Word-count rules 8.4 to 8.7 are applied inside the sentence-length checks
# (STE-5.1, STE-6.3); they have no findings of their own.

GROUPABLE = {"STE-1.1", "STE-1.2", "STE-1.4", "STE-1.6", "STE-1.14"}
MAX_LOCATIONS = 5          # locations shown for a group (the count gives the total)

# --------------------------------------------------------------------------
# Word lists (ordinary English grammar words, chosen for this checker)
# --------------------------------------------------------------------------

ARTICLES = {"the", "a", "an"}
DETERMINERS = ARTICLES | {
    "this", "these", "those", "each", "every", "its", "their", "your", "our", "my", "his",
    "her", "some", "any", "no", "another", "either", "neither", "whose", "which", "much",
    "many", "several", "few", "all", "both", "that"}
POS_DETERMINERS = DETERMINERS - {"that", "all", "both", "which", "much", "no"}
SUBJ_PRONOUNS = {"i", "you", "we", "they", "he", "she", "it"}
OBJ_PRONOUNS = {"it", "them", "him", "her", "me", "us", "you", "this", "these", "those",
                "all", "both", "one", "each"}
MODALS = {"can", "cannot", "could", "may", "might", "must", "shall", "should", "will",
          "would", "do", "does", "did"}
BE_FORMS = {"am", "is", "are", "was", "were", "be", "been", "being"}
HAVE_FORMS = {"have", "has", "had"}
GET_FORMS = {"get", "gets", "got", "gotten"}
FINITE = BE_FORMS | HAVE_FORMS | MODALS | {"shows", "gives", "contains", "uses", "makes",
                                             "means", "occurs"}
PREPOSITIONS = {
    "about", "above", "across", "after", "against", "along", "among", "around", "at",
    "before", "behind", "below", "between", "by", "during", "for", "from", "in", "inside",
    "into", "near", "of", "off", "on", "onto", "out", "outside", "over", "through", "to",
    "toward", "towards", "under", "until", "up", "upon", "with", "within", "without", "per",
    "via", "than", "as"}
CONJUNCTIONS = {"and", "or", "but", "nor", "so", "yet", "if", "when", "while", "because",
                "although", "though", "unless", "whether", "then", "that", "where", "after",
                "before", "until", "once", "since"}
ADVERB_PREFIX = {"always", "never", "carefully", "slowly", "fully", "then", "now", "first",
                 "next", "also", "only", "again", "please", "immediately", "finally",
                 "optionally", "manually", "just"}
OTHER_FUNCTION = {"not", "no", "very", "too", "there", "here", "more", "most", "less",
                  "least", "such", "other", "same", "own", "what", "who", "whom", "how",
                  "why", "all", "some", "any", "one", "only", "also", "even", "still",
                  "already", "yes", "i", "me", "my", "we", "us", "our", "you", "your",
                  "they", "them", "their", "he", "him", "his", "she", "her", "it", "its",
                  "itself", "themselves", "yourself", "this", "these", "those"}
FUNCTION_WORDS = (DETERMINERS | SUBJ_PRONOUNS | OBJ_PRONOUNS | MODALS | BE_FORMS
                  | HAVE_FORMS | PREPOSITIONS | CONJUNCTIONS | OTHER_FUNCTION)
CONDITION_STARTERS = {"if", "when", "before", "after", "while", "until", "unless", "once",
                      "during", "to", "for", "in", "on", "at", "from", "with", "without",
                      "as", "because", "where", "whenever", "since", "by", "through",
                      "under"}
PARTICLES = {"up", "out", "off", "down", "away", "back", "over"}
# Verbs that take "up" or "down" as a direction at the end of a clause
# ("the tab points up"), not as a phrasal verb.
DIRECTION_VERBS = {"point", "face", "move", "go", "tilt", "lean", "hang", "slide", "turn",
                   "rotate", "swing", "look"}
NUMBER_WORDS = set("""
zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen
fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty
ninety hundred thousand million billion first second third fourth fifth sixth seventh
eighth ninth tenth half quarter
""".split())
QUANTIFIERS = (NUMBER_WORDS - {"one"}) | {"several", "multiple", "many", "few"}
SINGULAR_DETS = {"a", "an", "this", "that", "each", "every", "another", "either", "neither",
                 "one"}
PRONOUN_DETERMINERS = {"this", "these", "those", "each", "some", "any", "either",
                       "neither", "another", "much", "many"}
KIND_POS = {"plural": {"n", "v"}, "past": {"v"}, "ing": {"v"}, "comparative": {"adj"},
            "superlative": {"adj"}, "adverb": {"adj", "adv"}, "possessive": None}

# Common instruction verbs. They find the imperative when the dictionary
# cache is missing (the cache adds every verb it lists).
BUILTIN_VERBS = set("""
accept activate add adjust align allow apply approve archive assemble attach avoid be
build calculate call cancel change check choose clean clear click clone close collect
commit compare compile configure confirm connect copy create cut deactivate declare
decrease define delete deploy detach disable disassemble discard disconnect do download
drag drain edit enable ensure enter examine exclude execute export extract fill filter
find fix follow format generate get give go hold identify ignore import include increase
insert inspect install invoke keep launch let lift list load lock look lower make mark
measure merge mount move name note obey open paste pause pick place plug point prepare
press prevent provide pull push put raise read record refer release reload remove rename
repeat replace reset restart restore resume return review run save scroll search see
select send set show sign skip sort specify start stop submit switch tag take tap tell
test tighten loosen toggle turn type uninstall unlock unmount unplug update upgrade upload
use validate verify view wait write try lubricate torque enroll
""".split())

IRREGULAR_PP = set("""
arisen awoken been beaten become begun bent bet bid bitten bled blown broken bred brought
built burnt burst bought cast caught chosen clung come cost crept cut dealt dug done drawn
dreamt driven drunk eaten fallen fed felt fought found fled flung flown forbidden forgotten
forgiven frozen gotten given gone ground grown hung heard hidden hit held hurt kept knelt
known laid led leant learnt left lent let lain lit lost made meant met mistaken overcome
overridden overrun overseen overtaken overthrown paid proven put quit read rebuilt redone
rewritten ridden rung risen run said seen sought sold sent set sewn shaken shed shone shot
shown shrunk shut sung sunk sat slain slept slid slung slit smelt sown spoken sped spelt
spent spilt spun spit split spoilt spread sprung stood stolen stuck stung stunk struck
strung sworn swept swollen swum swung taken taught torn told thought thrown thrust trodden
understood undergone undertaken undone upheld upset woken worn woven wed wept won wound
withdrawn withheld withstood written
""".split())
ED_NOT_PP = set("""
need feed speed bed red shed seed bleed breed embed exceed proceed succeed indeed hundred
sacred naked wicked rugged ragged kindred wretched beloved deed weed reed steed creed greed
heed freed agreed shred sled
""".split())
STATE_ADJ = {"based", "concerned", "interested", "involved", "located", "related",
             "supposed", "tired", "pleased", "satisfied", "done", "gone", "finished",
             "detailed", "advanced", "experienced", "limited", "sophisticated", "united",
             "married", "known"}
# Participles that usually tell the condition of a part after 'is' or 'are'
# ("The valve is closed."), like the adjectives open, full, and empty.
STATE_PP = {"closed", "locked", "unlocked", "connected", "disconnected", "engaged",
            "disengaged", "energized", "deenergized", "de-energized", "attached", "sealed",
            "blocked", "clogged", "worn", "broken", "bent", "cracked", "filled", "plugged",
            "unplugged", "installed", "switched", "set", "shut"}
ING_NOT_VERB = set("""
bring cling during everything anything nothing something thing things king ring spring
sing sting string swing wing ceiling evening morning sibling pudding awning herring
lightning offspring inkling earring
""".split())
COMMON_ADJ = {"new", "old", "used", "correct", "incorrect", "applicable", "necessary",
              "different", "same", "other", "clean", "dirty", "spare", "primary",
              "secondary", "main", "auxiliary"}
AGENT_NOT = {"default", "hand", "itself", "themselves", "means", "way", "then", "now",
             "far", "design", "name", "contrast", "comparison", "mistake", "accident",
             "chance", "email", "phone", "mail", "value", "reference"}
RISK_RE = re.compile(
    r"\b(injur(?:y|ies|e|es|ed)|death|kill(?:s|ed)?|damage|burns?|electric shock|shock|"
    r"explosions?|explode|fire|hazards?|dangerous|data loss|lose data|corrupt(?:s|ion)?)\b",
    re.IGNORECASE)
PERSON_RISK_RE = re.compile(r"\b(injur(?:y|ies|e|es|ed)|death|kill(?:s|ed)?|burns?|"
                            r"electric shock|poison(?:ous)?)\b", re.IGNORECASE)
# "You should wear ...": an obligation for the safety of persons.
OBLIGATION_SUBJ_RE = re.compile(
    r"\b(?:you|operators?|persons?|personnel|users?|technicians?|workers?)\s+"
    r"(?:must|should|shall|need to|needs to|have to|has to)\b", re.IGNORECASE)
PPE_RE = re.compile(
    r"\b(?:goggles|gloves|safety glasses|eye protection|ear protection|hearing protection|"
    r"protective|respirator|face shield|helmet|hard hat|apron|safety shoes|safety boots)\b",
    re.IGNORECASE)
SUBORDINATORS = {"because", "that", "if", "when", "so", "until", "unless", "before", "after",
                 "while", "since", "where", "which", "who", "as", "although", "though",
                 "whether", "once", "whenever"}
CAUSE_RE = re.compile(
    r"\b(can|could|will|may)\s+(?:\w+\s+){0,2}(cause|occur|result|kill|injure|damage|"
    r"destroy|lose|corrupt|break)", re.IGNORECASE)
RESULT_RE = re.compile(
    r"\b(can|could|will|may)\s+(?:\w+\s+){0,2}(cause|occur|result|kill|injure|damage|"
    r"destroy|lose|corrupt|break|stop)|\b(injury|injuries|damage|death|result|results|"
    r"because|risk|if you do not|prevent|prevents)\b", re.IGNORECASE)

UNIT_TOKENS = set("""
mm cm m km um nm in inch ft yd mi g kg mg lb lbs oz t s sec secs ms us ns min mins h hr
hrs V mV kV A mA W kW MW Hz kHz MHz GHz ohm ohms C F K psi bar kPa Pa MPa l L ml mL cc gal
B KB MB GB TB KiB MiB GiB kB px pt em rem dpi rpm fps Nm
""".split())
UNIT_WORDS = {"percent", "degree", "degrees", "celsius", "fahrenheit", "second", "seconds",
              "minute", "minutes", "hour", "hours", "day", "days", "byte", "bytes", "bit",
              "bits", "ohms", "inch", "inches", "foot", "feet", "meter", "meters", "kilogram",
              "kilograms", "gram", "grams", "volt", "volts", "ampere", "amperes", "watt",
              "watts", "liter", "liters", "millimeter", "millimeters", "centimeter",
              "centimeters", "kilometer", "kilometers", "pixel", "pixels", "millisecond",
              "milliseconds"}

COMMON_ABBR = set("""
API CLI CPU CSS CSV DNS FAQ GPU GUI HTML HTTP HTTPS ID IDE IP JSON OS PDF RAM README SDK
SQL SSH SSL TLS UI URL URI USB UTF XML YAML PNG JPEG GIF SVG TCP UDP VPN LAN WAN AC DC AM
PM UTC ISO ANSI ASCII NOTE WARNING CAUTION DANGER TIP IMPORTANT ON OFF OK TODO US UK EU
PR CI TV PC IT GB MB KB TB
""".split())

LATIN = OrderedDict([
    ("e.g.", "for example"), ("i.e.", "that is"),
    ("etc.", "give the full list, or rewrite the sentence"),
    ("etc", "give the full list, or rewrite the sentence"),
    ("viz.", "that is"), ("cf.", "compare, or refer to"),
    ("vs.", "against, or compared with"), ("vs", "against, or compared with"),
    ("n.b.", "use a note"), ("et al.", "and others"), ("q.v.", "refer to"),
])

# A capital letter, a hyphen, and a word: "O-ring", "V-belt", "T-handle" (not a name).
LETTER_WORD_RE = re.compile(r"^[A-Z]-[a-z]{2,}")

CONTRACTION_RE = re.compile(
    r"^(?:[a-z]+n['’]t|[a-z]+['’](?:ll|re|ve|d|m)|(?:it|that|there|here|what|who|where|"
    r"let|he|she|how|when|why)['’]s)$", re.IGNORECASE)

# British -> American spelling (a short list plus the -ise/-yse pattern).
BRIT_WORDS = {
    "colour": "color", "favour": "favor", "behaviour": "behavior", "honour": "honor",
    "labour": "labor", "neighbour": "neighbor", "flavour": "flavor", "harbour": "harbor",
    "humour": "humor", "rumour": "rumor", "vapour": "vapor", "armour": "armor",
    "odour": "odor", "endeavour": "endeavor", "savour": "savor", "favourite": "favorite",
    "centre": "center", "metre": "meter", "litre": "liter", "fibre": "fiber",
    "theatre": "theater", "calibre": "caliber", "sabre": "saber", "sombre": "somber",
    "spectre": "specter", "lustre": "luster", "meagre": "meager", "manoeuvre": "maneuver",
    "kilometre": "kilometer", "millimetre": "millimeter", "centimetre": "centimeter",
    "licence": "license", "defence": "defense", "offence": "offense", "pretence": "pretense",
    "grey": "gray", "aluminium": "aluminum", "programme": "program", "catalogue": "catalog",
    "analogue": "analog", "tyre": "tire", "sulphur": "sulfur", "mould": "mold",
    "plough": "plow", "draught": "draft", "ageing": "aging", "judgement": "judgment",
    "acknowledgement": "acknowledgment", "enrolment": "enrollment", "fulfil": "fulfill",
    "instil": "instill", "skilful": "skillful", "wilful": "willful", "whilst": "while",
    "amongst": "among", "learnt": "learned", "spelt": "spelled", "practise": "practice",
    "storey": "story", "artefact": "artifact", "cheque": "check", "jewellery": "jewelry",
    "travelled": "traveled", "travelling": "traveling", "cancelled": "canceled",
    "cancelling": "canceling", "labelled": "labeled", "labelling": "labeling",
    "modelled": "modeled", "modelling": "modeling", "signalled": "signaled",
    "signalling": "signaling", "fuelled": "fueled", "fuelling": "fueling",
    "levelled": "leveled", "levelling": "leveling", "tunnelling": "tunneling",
    "totalled": "totaled", "channelled": "channeled", "marshalling": "marshaling",
    "counsellor": "counselor", "oestrogen": "estrogen", "paediatric": "pediatric",
    "anaesthetic": "anesthetic", "haemoglobin": "hemoglobin", "orientated": "oriented",
}
BRIT_SUFFIXES = ("s", "ed", "ing", "er", "ers", "ful", "less", "ly", "able", "ist")
ISE_EXCEPTIONS = set("""
advertise advise apprise arise chastise circumcise comprise compromise concise demise
despise devise disguise enterprise excise exercise expertise franchise improvise incise
merchandise noise otherwise paradise poise praise precise premise promise raise reprise
revise rise supervise surmise surprise televise treatise wise likewise clockwise
anticlockwise counterclockwise guise mortise porpoise tortoise anise valise vise bruise
cruise braise sunrise upraise
""".split())

# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


class Finding(object):
    __slots__ = ("file", "line", "col", "severity", "rule", "message", "suggestion",
                 "key", "excerpt", "locations", "hint")

    def __init__(self, file, line, col, severity, rule, message, suggestion=None,
                 key=None, excerpt=None):
        self.file = file
        self.line = line
        self.col = col
        self.severity = severity
        self.rule = rule
        self.message = message
        self.suggestion = suggestion
        self.key = key
        self.excerpt = excerpt
        self.locations = [(file, line, col)]
        self.hint = None

    def as_dict(self):
        d = OrderedDict([
            ("file", self.file), ("line", self.line), ("col", self.col),
            ("severity", self.severity), ("rule", self.rule), ("message", self.message),
            ("suggestion", self.suggestion), ("excerpt", self.excerpt),
            ("count", len(self.locations)),
        ])
        locs = self.locations[:MAX_LOCATIONS] if self.rule == "STE-1.6" else self.locations
        d["locations"] = [OrderedDict([("file", f), ("line", l), ("col", c)])
                          for f, l, c in locs]
        return d

    def __repr__(self):
        return "Finding(%s:%d:%d %s %s %r)" % (self.file, self.line, self.col,
                                               self.severity, self.rule, self.message)


# --------------------------------------------------------------------------
# Dictionary cache and term list
# --------------------------------------------------------------------------

POS_NORMAL = {"noun": "n", "verb": "v", "adjective": "adj", "adverb": "adv",
              "preposition": "prep", "conjunction": "conj", "pronoun": "pron",
              "article": "art", "number": "num"}
POS_NAMES = {"n": "noun", "v": "verb", "adj": "adjective", "adv": "adverb",
             "prep": "preposition", "conj": "conjunction", "pron": "pronoun",
             "art": "article", "num": "number", "prefix": "prefix", "TN": "technical noun",
             "TV": "technical verb"}


def _norm_pos(p):
    if p is None:
        return None
    p = str(p).strip()
    if p in ("TN", "TV"):
        return p
    p = p.lower().rstrip(".")
    return POS_NORMAL.get(p, p)


class DictionaryError(Exception):
    pass


class Lexicon(object):
    """Read-only view of the dictionary cache (schema in the wave-1 contract)."""

    def __init__(self, data, path=None):
        if not isinstance(data, dict) or "entries" not in data or "forms" not in data:
            raise DictionaryError("dictionary cache has no 'entries' or 'forms' key")
        self.path = path
        self.meta = data.get("meta", {}) or {}
        self.by_key = defaultdict(list)
        self.tn_alts = set()        # words that an entry gives as a technical noun (TN)
        self.approved_meanings = []  # (word, pos, meaning) of approved entries
        for e in data["entries"]:
            e = dict(e)
            e["word"] = str(e.get("word", "")).lower()
            e["pos"] = _norm_pos(e.get("pos"))
            self.by_key[(e["word"], e["pos"])].append(e)
            if e.get("approved") and e.get("meaning"):
                self.approved_meanings.append((e["word"], e["pos"], str(e["meaning"])))
            for alt in e.get("alternatives") or []:
                if isinstance(alt, dict) and alt.get("kind") == "TN":
                    w = " ".join(str(alt.get("word", "")).lower().split())
                    if w:
                        self.tn_alts.add(w)
        self.forms = {}
        self.phrases = defaultdict(list)
        for surface, items in data["forms"].items():
            s = " ".join(str(surface).lower().split())
            recs = []
            for it in items:
                it = dict(it)
                it["word"] = str(it.get("word", "")).lower()
                it["pos"] = _norm_pos(it.get("pos"))
                recs.append(it)
            self.forms.setdefault(s, []).extend(recs)
            if " " in s:
                parts = tuple(s.split(" "))
                if parts not in self.phrases[parts[0]]:
                    self.phrases[parts[0]].append(parts)
        for k in self.phrases:
            self.phrases[k].sort(key=len, reverse=True)

    @classmethod
    def load(cls, path):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except ValueError as exc:
            raise DictionaryError("cannot parse %s: %s" % (path, exc))
        return cls(data, path)

    def lookup(self, surface):
        return self.forms.get(surface.lower(), [])

    def entries(self, word, pos):
        return self.by_key.get((word, pos), [])

    def alternatives(self, recs, approved_only=False):
        """Alternatives of the not-approved entries in recs.

        Approved words come first, then technical nouns and technical verbs
        (a TN or TV alternative is correct only for the technical item).
        """
        out = []
        tech = []
        seen = set()
        for r in recs:
            for e in self.entries(r["word"], r["pos"]):
                if e.get("approved"):
                    continue
                for alt in e.get("alternatives") or []:
                    if isinstance(alt, str):
                        alt = {"word": alt, "pos": None, "kind": "approved"}
                    w = str(alt.get("word", "")).strip()
                    if not w:
                        continue
                    p = _norm_pos(alt.get("pos"))
                    kind = alt.get("kind") or "approved"
                    label = w.upper() if kind == "approved" else w
                    if p and kind == "approved":
                        label += " (%s)" % p
                    elif kind in ("TN", "TV"):
                        label += " (%s)" % kind
                    if label not in seen:
                        seen.add(label)
                        (out if kind == "approved" else tech).append(label)
        return out if approved_only else out + tech

    def is_tn_alternative(self, w):
        w = w.lower()
        return w in self.tn_alts or singular(w) in self.tn_alts

    def synonyms_by_meaning(self, word, pos="n", limit=3):
        """Approved words of part of speech pos whose short meaning ends with word
        (for example a noun whose meaning is '... near the <word>')."""
        rx = re.compile(r"\b%s\W*$" % re.escape(word.lower()))
        out = []
        for w, p, meaning in self.approved_meanings:
            if p == pos and w != word and rx.search(meaning.lower()):
                label = "%s (%s)" % (w.upper(), p)
                if label not in out:
                    out.append(label)
        return out[:limit]

    def is_verb_base(self, w):
        for r in self.lookup(w):
            if r["pos"] == "v" and r["word"] == w:
                return True
        return False

    def pos_set(self, w):
        return {r["pos"] for r in self.lookup(w)}

    def approved_surface(self, w, pos_filter=None):
        for r in self.lookup(w):
            if r.get("approved") and not r.get("variant"):
                if pos_filter is None or r["pos"] in pos_filter:
                    return True
        return False


TERM_EMPTY = {"", "-", "–", "—", "n/a", "na", "none", "(none)", "no"}
TERM_WORD_RE = re.compile(r"[\w'’]+(?:[-.·][\w'’]+)*")


def _term_words(term):
    return [w.strip(".").lower() for w in TERM_WORD_RE.findall(term) if w.strip(".")]


def _match_word(table, w):
    """Look up w in table, also as a plural, past or -ing form of a key."""
    w = w.lower()
    if w in table:
        return table[w]
    for suffix, repl in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"),
                         ("ing", ""), ("ing", "e"), ("'s", ""), ("’s", "")):
        if w.endswith(suffix) and len(w) > len(suffix) + 1:
            base = w[:-len(suffix)] + repl
            if base in table:
                return table[base]
            if len(base) > 2 and base[-1] == base[-2] and base[:-1] in table:
                return table[base[:-1]]
    return None


class TermList(object):
    """Project term list (DOCS_TERMS.md).

    Two layouts are read:

    * lines: one term per line, with an optional (TN) or (TV) tag, for example
      "- gasket (TN): a seal ring". "Do not use: x, y" at the end of the line
      gives words that the project does not permit for that item.
    * Markdown tables. The header names the columns: the term column
      ("Term", "Technical noun", "Technical verb", "Name", "Word"), an optional
      kind column ("Kind", "Type", "Tag" with TN or TV), an optional definition
      column, and an optional column of words not to use ("Do not use",
      "Avoid", "Not approved"). "-" in a cell means empty. A term column
      named "Technical verb", or a table under a heading about verbs, gives TV.
    """

    LINE_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(?P<body>.+?)\s*$")
    AVOID_LINE_RE = re.compile(r"[\s(;,.]+(?:do not use|don't use|don’t use|avoid|not)\s*:\s*"
                               r"(?P<words>[^)]+)\)?\s*$", re.IGNORECASE)
    TERM_HEADERS = ("term", "terms", "word", "words", "name", "names", "technical noun",
                    "technical nouns", "technical verb", "technical verbs", "technical term",
                    "technical terms", "noun", "nouns", "verb", "verbs", "tn", "tv",
                    "approved term", "approved name", "preferred term")
    KIND_HEADERS = ("kind", "type", "tag", "category", "class", "pos", "tn/tv")
    DEF_HEADERS = ("definition", "definitions", "meaning", "description", "notes")
    AVOID_HINTS = ("do not use", "don't use", "don’t use", "avoid", "not approved",
                   "unapproved", "forbidden", "deprecated", "prohibited", "not permitted",
                   "instead of", "synonym")

    def __init__(self, path=None):
        self.path = path
        self.single = {}
        self.multi = defaultdict(list)
        self.avoid_single = {}          # word -> preferred term
        self.avoid_multi = defaultdict(list)
        self.definitions = {}           # lowercased term -> definition text
        self.expansions = defaultdict(list)  # full forms of abbreviation terms

    def __len__(self):
        return len(self.single) + sum(len(v) for v in self.multi.values())

    def add(self, term, tag="TN", definition=None):
        words = _term_words(term)
        if not words:
            return
        if len(words) == 1:
            self.single[words[0]] = tag
        else:
            self.multi[words[0]].append((tuple(words), tag))
            self.multi[words[0]].sort(key=lambda t: len(t[0]), reverse=True)
        if definition:
            self.definitions[" ".join(words)] = definition
            self._add_expansion(term, definition)

    ABBR_TERM_RE = re.compile(r"^[A-Z][A-Z0-9&-]{1,9}s?$")

    def _add_expansion(self, term, definition):
        """The full form of an abbreviation term (the first sentence of its
        definition, for example 'Quick xfer relay' for 'QXR'). Text that
        uses the full form is the term, not a new noun cluster."""
        first = re.split(r"(?<=[^\s.])\.(?:\s|$)|[;:(]", definition.strip(), maxsplit=1)[0]
        words = _term_words(first)
        if not self.ABBR_TERM_RE.match(term.strip()) or not 2 <= len(words) <= 8:
            return
        entry = (tuple(words), "TN")
        if entry not in self.expansions[words[0]]:
            self.expansions[words[0]].append(entry)
            self.expansions[words[0]].sort(key=lambda t: len(t[0]), reverse=True)

    def add_avoid(self, word, preferred):
        words = _term_words(word)
        if not words or " ".join(words) == " ".join(_term_words(preferred)):
            return
        if len(words) == 1:
            if words[0] not in self.single:
                self.avoid_single[words[0]] = preferred
        else:
            self.avoid_multi[words[0]].append((tuple(words), preferred))
            self.avoid_multi[words[0]].sort(key=lambda t: len(t[0]), reverse=True)

    @staticmethod
    def _clean(cell):
        c = cell.strip().strip("`*_\"'“”").strip()
        return "" if c.lower() in TERM_EMPTY else c

    @classmethod
    def _split_avoid(cls, cell):
        out = []
        for part in re.split(r"\s*(?:[,;/]|\bor\b)\s*", cell):
            part = cls._clean(part)
            if part:
                out.append(part)
        return out

    @classmethod
    def load(cls, path):
        tl = cls(path)
        with open(path, encoding="utf-8", errors="replace") as fh:
            tl.parse(fh.read())
        return tl

    def _header_roles(self, cells, default_tag):
        roles = {}
        tag = default_tag
        for n, c in enumerate(cells):
            h = " ".join(c.strip("`*_ :").lower().split())
            if "term" not in roles and (h in self.TERM_HEADERS or
                                        h.startswith(("technical noun", "technical verb"))):
                roles["term"] = n
                if "verb" in h or h == "tv":
                    tag = "TV"
                elif "noun" in h or h == "tn":
                    tag = "TN"
            elif h in self.KIND_HEADERS and "kind" not in roles:
                roles["kind"] = n
            elif h in self.DEF_HEADERS and "def" not in roles:
                roles["def"] = n
            elif any(x in h for x in self.AVOID_HINTS) and "avoid" not in roles:
                roles["avoid"] = n
        if "term" not in roles:
            return None, tag
        return roles, tag

    def _table_row(self, cells, roles, tag):
        def cell(name):
            n = roles.get(name)
            return cells[n] if n is not None and n < len(cells) else ""
        term = self._clean(cell("term"))
        if not term:
            return
        kind = cell("kind").strip("() `*").upper()
        if kind in ("TN", "TV"):
            tag = kind
        m = re.search(r"\((TN|TV)\)\s*$", term, re.IGNORECASE)
        if m:
            tag = m.group(1).upper()
            term = term[:m.start()].strip()
        self.add(term, tag, self._clean(cell("def")) or None)
        for w in self._split_avoid(cell("avoid")):
            self.add_avoid(w, term)

    def parse(self, text):
        in_fence = False
        lines = text.splitlines()
        heading_tag = "TN"
        roles = None
        table_tag = "TN"
        for idx, raw in enumerate(lines):
            s = raw.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence or not s or s.startswith("<!--"):
                if not s:
                    roles = None
                continue
            if s.startswith("#"):
                h = s.lstrip("#").strip().lower()
                if "verb" in h and "noun" not in h:
                    heading_tag = "TV"
                elif "noun" in h or "term" in h:
                    heading_tag = "TN"
                roles = None
                continue
            if s.startswith("|"):
                cells = [t for _c0, t in split_table_row(s)]
                if not cells or TABLE_SEP_RE.match(s):
                    continue
                nxt = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
                if nxt.startswith("|") and TABLE_SEP_RE.match(nxt):
                    roles, table_tag = self._header_roles(cells, heading_tag)
                    if roles is None:
                        roles = {"term": 0}     # unknown header: first column is the term
                    continue
                r = roles if roles is not None else {"term": 0}
                t = table_tag if roles is not None else heading_tag
                if "kind" not in r:
                    for n, c in enumerate(cells[1:], 1):
                        if c.strip("() `*").upper() in ("TN", "TV"):
                            r = dict(r, kind=n)
                            break
                self._table_row(cells, r, t)
                continue
            roles = None
            m = self.LINE_RE.match(s)
            body = m.group("body") if m else s
            avoid = []
            am = self.AVOID_LINE_RE.search(body)
            if am:
                avoid = self._split_avoid(am.group("words"))
                body = body[:am.start()]
            tag = heading_tag
            t = re.search(r"\((TN|TV)\)", body, re.IGNORECASE)
            if t:
                tag = t.group(1).upper()
                term = body[:t.start()]
            elif not m or m.group(0).strip() == m.group("body") and len(body.split()) > 5:
                continue            # a prose line (introduction), not a term
            else:
                term = re.split(r"\s+[-–—:]\s+|:\s|\s\|\s|\t", body, maxsplit=1)[0]
            term = term.strip().strip("`*_").strip()
            if term:
                self.add(term, tag)
                for w in avoid:
                    self.add_avoid(w, term)
        return self

    def match_single(self, w):
        return _match_word(self.single, w)

    def match_avoid(self, w):
        return _match_word(self.avoid_single, w)


# --------------------------------------------------------------------------
# Document model and markup extraction
# --------------------------------------------------------------------------


class Block(object):
    """A unit of prose: paragraph, heading, list item, table cell."""

    def __init__(self, kind, **kw):
        self.kind = kind            # paragraph | heading | list_item | table_cell
        self.segs = []              # (lineno, col0, text)
        self.label = kw.get("label")
        self.ordered = kw.get("ordered", False)
        self.level = kw.get("level", 0)
        self.list_id = kw.get("list_id")
        self.header = kw.get("header", False)
        self.in_list = kw.get("in_list", False)
        self.quote = kw.get("quote", False)
        self.text = ""
        self.masked = ""
        self.pos = []
        self.tokens = []
        self.sentences = []

    def add(self, lineno, col0, text):
        self.segs.append((lineno, col0, text))

    def build(self):
        parts = []
        pos = []
        for idx, (ln, c0, t) in enumerate(self.segs):
            if idx:
                parts.append(" ")
                prev = self.segs[idx - 1]
                pos.append((prev[0], prev[1] + len(prev[2]) + 1))
            parts.append(t)
            pos.extend((ln, c0 + k + 1) for k in range(len(t)))
        self.text = "".join(parts)
        self.pos = pos

    def where(self, index):
        if not self.pos:
            return (self.segs[0][0] if self.segs else 1, 1)
        index = max(0, min(index, len(self.pos) - 1))
        return self.pos[index]


LABEL_WORDS = ("WARNING", "CAUTION", "DANGER", "NOTE", "NOTICE", "IMPORTANT", "ATTENTION",
               "TIP")
_LABEL_ALT = r"(?i:warning|caution|danger|note|notice|important|attention|tip)"
LABEL_RE = re.compile(
    r"^\s*(?:\*\*|__|\*|_)?(?P<label>" + _LABEL_ALT + r")(?:\*\*|__|\*|_)?\s*"
    r"(?::|\s[-–—]\s)\s*(?:\*\*|__)?\s*")
LABEL_ONLY_RE = re.compile(
    r"^\s*(?:\*\*|__|\*|_)?(?P<label>" + _LABEL_ALT + r")(?:\*\*|__|\*|_)?\s*:?\s*"
    r"(?:\*\*|__)?\s*$")
SAFETY_LABELS = {"WARNING", "CAUTION", "DANGER"}
NOTE_LABELS = {"NOTE", "TIP", "IMPORTANT", "NOTICE", "ATTENTION"}

FENCE_RE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})")
ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
HR_RE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
LINKREF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*\S+")
LIST_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>[-*+•]|\d{1,3}[.)]|\(\d{1,3}\)|[A-Za-z][.)]|"
    r"\([A-Za-z]\))(?P<space>[ \t]+)(?P<rest>\S.*)?$")
ADOC_LIST_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>\*{1,5}|\.{1,5}|-|\d{1,3}\.)"
                          r"(?P<space>[ \t]+)(?P<rest>\S.*)?$")
RST_LIST_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>[-*+•]|#\.|\d{1,3}[.)]|\(\d{1,3}\)|[A-Za-z][.)]|"
    r"\([A-Za-z]\))(?P<space>[ \t]+)(?P<rest>\S.*)?$")
TASK_RE = re.compile(r"^\[[ xX]\]\s+")
HTML_BLOCK_RE = re.compile(r"^ {0,3}<(?:/?[A-Za-z][\w-]*(?:[\s>/]|$)|!)")
ALERT_RE = re.compile(r"^\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", re.IGNORECASE)
RST_UNDERLINE_RE = re.compile(r"^([=\-~^\"'`#*+:.<>_])\1{2,}\s*$")
RST_DIRECTIVE_RE = re.compile(r"^(?P<indent>\s*)\.\.\s+(?P<name>[\w:-]+)::\s*(?P<rest>.*)$")
ADOC_DELIM_RE = re.compile(r"^(-{4,}|\.{4,}|\+{4,}|/{4,}|`{3,})\s*$")
ADOC_ATTR_RE = re.compile(r"^\[(?P<body>[^\]]*)\]\s*$")
QUOTE_PREFIX_RE = re.compile(r"^(?: {0,3}>[ ]?)+")


def _indent_width(s):
    e = s.expandtabs(4)
    return len(e) - len(e.lstrip(" "))


def split_table_row(line):
    """Split a table row on unescaped '|' outside code. Return [(col0, text)]."""
    cells = []
    s = line
    i = len(s) - len(s.lstrip())
    if i < len(s) and s[i] == "|":
        i += 1
    start = i
    in_code = False
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        elif ch == "|" and not in_code:
            cells.append((start, s[start:i]))
            start = i + 1
        i += 1
    tail = s[start:]
    if tail.strip():
        cells.append((start, tail))
    out = []
    for c0, t in cells:
        lead = len(t) - len(t.lstrip())
        out.append((c0 + lead, t.strip()))
    return out


class Parser(object):
    """Line-based prose extractor for Markdown, text, reStructuredText, AsciiDoc."""

    def __init__(self, text, flavor):
        self.lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.flavor = flavor
        self.blocks = []
        self.cur = None
        self.pending_label = None
        self.scope_label = None          # label for a quote alert or rst directive
        self.list_stack = []             # (indent, content_col, list_id)
        self.list_counter = 0
        self.blank_before = True

    def flush(self):
        b = self.cur
        self.cur = None
        if b is None or not b.segs:
            return
        if b.kind == "paragraph" and len(b.segs) == 1:
            m = LABEL_ONLY_RE.match(b.segs[0][2])
            if m:
                self.pending_label = m.group("label").upper()
                return
        if b.label is None:
            ln, c0, t = b.segs[0]
            m = LABEL_RE.match(t)
            if m:
                b.label = m.group("label").upper()
                b.segs[0] = (ln, c0, " " * m.end() + t[m.end():])
            elif self.pending_label:
                b.label = self.pending_label
            elif self.scope_label:
                b.label = self.scope_label
        self.pending_label = None
        self.blocks.append(b)

    def new_block(self, kind, **kw):
        self.flush()
        self.cur = Block(kind, **kw)
        return self.cur

    def end_lists(self):
        self.list_stack = []

    def list_item(self, lineno, m, col_base=0, quote=False):
        indent = _indent_width(m.group("indent"))
        marker = m.group("marker")
        rest = m.group("rest") or ""
        content_col = len(m.group("indent")) + len(marker) + len(m.group("space"))
        if self.flavor == "adoc" and marker[0] in "*.":
            ordered = marker[0] == "."
            level = len(marker) - 1
            if not self.list_stack:
                self.list_counter += 1
                self.list_stack.append((0, content_col, self.list_counter))
        else:
            ordered = marker not in ("-", "*", "+", "•")
            while self.list_stack and indent < self.list_stack[-1][0]:
                self.list_stack.pop()
            if not self.list_stack:
                self.list_counter += 1
                self.list_stack.append((indent, content_col, self.list_counter))
            elif indent > self.list_stack[-1][0] and indent >= self.list_stack[-1][1] - 1:
                self.list_stack.append((indent, content_col, self.list_stack[0][2]))
            level = len(self.list_stack) - 1
        list_id = self.list_stack[0][2]
        b = self.new_block("list_item", ordered=ordered, level=level, list_id=list_id,
                           quote=quote)
        col0 = col_base + content_col
        tm = TASK_RE.match(rest)
        if tm:
            col0 += tm.end()
            rest = rest[tm.end():]
        if rest:
            b.add(lineno, col0, rest)
        self.blank_before = False

    def parse(self):
        lines = self.lines
        n = len(lines)
        i = 0
        fl = self.flavor
        if fl in ("md", "adoc", "txt") and n and lines[0].strip() in ("---", "+++"):
            closing = lines[0].strip()
            j = 1
            while j < n and lines[j].strip() not in (closing, "..."):
                j += 1
            if j < n:
                i = j + 1
        rst_literal_indent = None
        rst_scope_indent = None
        while i < n:
            raw = lines[i]
            lineno = i + 1
            line = raw
            col_base = 0
            quote = False
            if fl in ("md", "txt"):
                m = QUOTE_PREFIX_RE.match(line)
                if m:
                    quote = True
                    col_base = m.end()
                    line = line[m.end():]
                    am = ALERT_RE.match(line)
                    if am:
                        self.flush()
                        self.scope_label = am.group(1).upper()
                        i += 1
                        continue
                elif self.scope_label and line.strip():
                    self.flush()
                    self.scope_label = None
            stripped = line.strip()

            if fl == "rst":
                if rst_literal_indent is not None:
                    if not stripped or _indent_width(line) > rst_literal_indent:
                        i += 1
                        continue
                    rst_literal_indent = None
                if rst_scope_indent is not None and stripped and \
                        _indent_width(line) <= rst_scope_indent:
                    self.flush()
                    self.scope_label = None
                    rst_scope_indent = None
                dm = RST_DIRECTIVE_RE.match(line)
                if dm:
                    self.flush()
                    name = dm.group("name").upper()
                    ind = _indent_width(dm.group("indent"))
                    if name in LABEL_WORDS:
                        self.scope_label = name
                        rst_scope_indent = ind
                        rest = dm.group("rest")
                        if rest:
                            b = self.new_block("paragraph", label=name)
                            b.add(lineno, raw.index(rest), rest)
                    else:
                        rst_literal_indent = ind
                    i += 1
                    continue
                if stripped.startswith(".. ") or stripped == "..":
                    self.flush()
                    rst_literal_indent = _indent_width(line)
                    i += 1
                    continue
                if re.match(r"^\s*:[\w -]+:(\s|$)", line):
                    self.flush()
                    i += 1
                    continue

            fm = FENCE_RE.match(line) if fl in ("md", "txt", "rst") else None
            if fm:
                self.flush()
                fence = fm.group("fence")
                j = i + 1
                while j < n:
                    l2 = QUOTE_PREFIX_RE.sub("", lines[j]) if quote else lines[j]
                    s2 = l2.strip()
                    if s2.startswith(fence[0] * len(fence)) and set(s2) <= {fence[0]}:
                        break
                    j += 1
                i = j + 1
                self.blank_before = True
                continue
            if fl == "adoc":
                dm = ADOC_DELIM_RE.match(stripped)
                if dm:
                    self.flush()
                    delim = dm.group(1)
                    j = i + 1
                    while j < n and lines[j].strip() != delim:
                        j += 1
                    i = j + 1
                    continue
                if stripped.startswith("|==="):
                    self.flush()
                    j = i + 1
                    while j < n and not lines[j].strip().startswith("|==="):
                        row = lines[j]
                        if row.strip().startswith("|"):
                            for c0, cell in split_table_row(row):
                                if cell:
                                    b = self.new_block("table_cell")
                                    b.add(j + 1, c0, cell)
                                    self.flush()
                        j += 1
                    i = j + 1
                    continue
                am = ADOC_ATTR_RE.match(stripped)
                if am:
                    self.flush()
                    body = am.group("body").strip().upper()
                    if body in LABEL_WORDS:
                        self.pending_label = body
                    i += 1
                    continue
                if re.match(r"^:[\w-]+:", stripped) or stripped.startswith("//"):
                    i += 1
                    continue
                hm = re.match(r"^(=+)\s+(.*)$", line)
                if hm:
                    self.end_lists()
                    b = self.new_block("heading")
                    b.add(lineno, hm.start(2), hm.group(2))
                    self.flush()
                    i += 1
                    continue
                tm = re.match(r"^\.([A-Za-z].*)$", line)
                if tm:
                    b = self.new_block("heading")
                    b.add(lineno, 1, tm.group(1))
                    self.flush()
                    i += 1
                    continue

            if not stripped:
                self.flush()
                self.blank_before = True
                i += 1
                continue

            if fl in ("md", "txt") and stripped.startswith("<!--"):
                self.flush()
                j = i
                while j < n and "-->" not in lines[j]:
                    j += 1
                i = j + 1
                continue
            if fl == "md" and self.cur is None and HTML_BLOCK_RE.match(line):
                j = i
                while j < n and lines[j].strip():
                    j += 1
                i = j
                continue
            if fl == "md" and LINKREF_RE.match(line):
                self.flush()
                i += 1
                continue
            is_setext = (self.cur is not None and self.cur.kind == "paragraph" and
                         len(self.cur.segs) == 1 and fl in ("md", "txt") and
                         SETEXT_RE.match(line))
            if fl in ("md", "txt") and HR_RE.match(line) and not is_setext:
                self.flush()
                self.end_lists()
                i += 1
                continue
            if fl == "md":
                hm = ATX_RE.match(line)
                if hm:
                    self.end_lists()
                    b = self.new_block("heading")
                    if hm.group(2):
                        b.add(lineno, col_base + hm.start(2), hm.group(2))
                    self.flush()
                    i += 1
                    continue
            if is_setext or (fl == "rst" and self.cur is not None and
                             self.cur.kind == "paragraph" and len(self.cur.segs) == 1 and
                             RST_UNDERLINE_RE.match(stripped)):
                self.cur.kind = "heading"
                self.end_lists()
                self.flush()
                i += 1
                continue
            if fl == "rst" and RST_UNDERLINE_RE.match(stripped) and self.cur is None:
                i += 1   # overline of a title
                continue
            if fl == "md" and "|" in line and i + 1 < n and "-" in lines[i + 1] and \
                    TABLE_SEP_RE.match(QUOTE_PREFIX_RE.sub("", lines[i + 1])):
                self.flush()
                self.end_lists()
                for c0, cell in split_table_row(line):
                    if cell:
                        b = self.new_block("table_cell", header=True)
                        b.add(lineno, col_base + c0, cell)
                        self.flush()
                j = i + 2
                while j < n:
                    row = QUOTE_PREFIX_RE.sub("", lines[j]) if quote else lines[j]
                    off = len(lines[j]) - len(row)
                    if not row.strip() or "|" not in row:
                        break
                    for c0, cell in split_table_row(row):
                        if cell:
                            b = self.new_block("table_cell")
                            b.add(j + 1, off + c0, cell)
                            self.flush()
                    j += 1
                i = j
                continue
            ind = _indent_width(line)
            if fl == "md" and ind >= 4 and self.cur is None:
                if not self.list_stack or ind >= self.list_stack[-1][1] + 4:
                    i += 1       # indented code block
                    continue
            lre = {"adoc": ADOC_LIST_RE, "rst": RST_LIST_RE}.get(fl, LIST_RE)
            lm = lre.match(line)
            if lm and lm.group("rest"):
                interrupting = (self.cur is not None and self.cur.kind == "paragraph" and
                                not self.blank_before and
                                not re.match(r"^(?:[-*+•]|1[.)])$", lm.group("marker")))
                if not interrupting:
                    self.list_item(lineno, lm, col_base, quote)
                    i += 1
                    continue
            text_col = col_base + (len(line) - len(line.lstrip()))
            text = stripped
            if fl == "rst" and text.endswith("::"):
                text = text[:-3] if text.endswith(" ::") else text[:-1]
                rst_literal_indent = _indent_width(line)
            if self.cur is not None:
                self.cur.add(lineno, text_col, text)
                self.blank_before = False
                i += 1
                continue
            in_list = False
            if self.list_stack:
                if self.blank_before and ind < self.list_stack[0][1]:
                    self.end_lists()
                else:
                    in_list = True
            b = self.new_block("paragraph", in_list=in_list, quote=quote,
                               list_id=self.list_stack[0][2] if in_list else None)
            b.add(lineno, text_col, text)
            self.blank_before = False
            i += 1
        self.flush()
        return self.blocks


# --------------------------------------------------------------------------
# Masking of text that must stay exact
# --------------------------------------------------------------------------

MASK = ""      # code, URL, path, identifier: one word, never checked
QMASK = ""     # quoted text: one word, never checked


def _fill(ch):
    return lambda m: ch * len(m.group(0))


def _blank(m):
    return " " * len(m.group(0))


URL_RE = re.compile(r"\b(?:https?|ftp|file|ssh|git)://[^\s<>\"'`]+|\bwww\.[^\s<>\"'`]+|"
                    r"\bmailto:[^\s<>]+|\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
INLINE_CODE_RE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")
RST_ROLE_RE = re.compile(r":[\w:.-]+:`[^`]*`")
RST_LINK_RE = re.compile(r"`([^`<]+?)\s*<[^>`]+>`_{1,2}")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->")
AUTOLINK_RE = re.compile(r"<(?:https?|ftp|mailto|file):[^>\s]+>")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s+[^<>]*)?/?>")
IMAGE_RE = re.compile(r"!\[[^\]]*\](?:\([^)]*\)|\[[^\]]*\])")
LINK_RE = re.compile(r"\[(?P<text>[^\]\n]+)\](?P<target>\((?:[^()\s]+|\([^)]*\))*"
                     r"(?:\s+\"[^\"]*\")?\)|\[[^\]]*\])")
FOOTNOTE_RE = re.compile(r"\[\^[^\]]+\]")
ADOC_LINK_RE = re.compile(r"\b(?:link|xref|https?|mailto):[^\s\[]*\[(?P<text>[^\]]*)\]")
ADOC_XREF_RE = re.compile(r"<<[^>]*>>")
QUOTE_RE = re.compile(r"\"[^\"\n]{1,200}?\"|“[^”\n]{1,200}?”|‘[^’\n]{1,200}?’(?![a-z])")
ESCAPE_RE = re.compile(r"\\(?=[\\`*_{}\[\]()#+\-.!|<>])")
EMPH_OPEN_RE = re.compile(r"(?<![\w*~\\])(\*{1,3}|_{1,3}|~~)(?=[^\s*_~])")
EMPH_CLOSE_RE = re.compile(r"(?<=[^\s*_~])(\*{1,3}|_{1,3}|~~)(?![\w*~])")
SPACE_TOKEN_RE = re.compile(r"\S+")
TRAIL_PUNCT = ".,;:!?)]}\"'”’»*_~"
LEAD_PUNCT = "([{\"'“‘«*_~"


def _code_like(core):
    """True if a whitespace-delimited token (edge punctuation removed) is code."""
    if not core:
        return False
    if MASK in core:
        return True
    if re.match(r"^(?:/|\./|\.\./|~/|[A-Za-z]:\\|\\\\)", core):
        return len(core) > 1
    if "/" in core or "\\" in core:
        parts = re.split(r"[/\\]", core)
        if any(re.search(r"\.[A-Za-z0-9]{1,6}$", p) for p in parts):
            return True
        return len(parts) >= 3 or core.endswith("/")
    if re.match(r"^--?[A-Za-z][\w-]*(?:=\S*)?$", core):
        return True
    if "_" in core.strip("_") or re.search(r"[=$@#{}<>|^~]|::|->|\(\)|\[\]", core):
        return True
    if re.search(r"[a-z][A-Z]", core) or re.match(r"^[A-Z]{2,}[a-z]+[A-Z]", core):
        return True
    if re.match(r"^[A-Za-z]+-\d+(?:[.-]\d+)+$", core):
        return True                      # identifier such as ABC-1.2
    if "." in core.strip("."):
        segs = core.strip(".").split(".")
        if all(len(s) <= 1 for s in segs):
            return False                 # a.m., i.e.
        if all(s.isdigit() for s in segs):
            return False                 # decimal number
        if re.match(r"^[vV]?\d+(?:\.\d+)+(?:[-+][\w.]+)?$", core):
            return True                  # version
        if all(re.match(r"^\w+$", s) for s in segs):
            return True                  # dotted.name, file.ext
    return False


def mask_block(text, flavor):
    """Return a string of the same length with the non-prose parts masked."""
    s = HTML_COMMENT_RE.sub(_blank, text)
    s = AUTOLINK_RE.sub(_fill(MASK), s)
    if flavor == "rst":
        s = RST_LINK_RE.sub(
            lambda m: " " + m.group(1) + " " * (len(m.group(0)) - len(m.group(1)) - 1), s)
        s = RST_ROLE_RE.sub(_fill(MASK), s)
    s = INLINE_CODE_RE.sub(_fill(MASK), s)
    if flavor == "adoc":
        s = re.sub(r"(?<![\w+])\+[^+\n]+\+(?![\w+])", _fill(MASK), s)
        s = ADOC_LINK_RE.sub(
            lambda m: MASK * (m.start("text") - m.start() - 1) + " " + m.group("text") + " ", s)
        s = ADOC_XREF_RE.sub(_fill(MASK), s)
    if flavor in ("md", "txt"):
        s = IMAGE_RE.sub(_fill(MASK), s)
        s = FOOTNOTE_RE.sub(_blank, s)

        def _link(m):
            t = m.group("text")
            return " " + t + " " * (len(m.group(0)) - len(t) - 1)
        s = LINK_RE.sub(_link, s)
    if flavor in ("md", "txt", "adoc"):
        s = HTML_TAG_RE.sub(_blank, s)
    s = ESCAPE_RE.sub(" ", s)

    def _url(m):
        u = m.group(0)
        core = u.rstrip(TRAIL_PUNCT)
        return MASK * len(core) + u[len(core):]
    s = URL_RE.sub(_url, s)

    def _tok(m):
        t = m.group(0)
        lead = len(t) - len(t.lstrip(LEAD_PUNCT))
        core = t[lead:].rstrip(TRAIL_PUNCT)
        if core and _code_like(core):
            return t[:lead] + MASK * len(core) + t[lead + len(core):]
        return t
    s = SPACE_TOKEN_RE.sub(_tok, s)
    if flavor in ("md", "txt", "adoc"):
        s = EMPH_OPEN_RE.sub(_blank, s)
        s = EMPH_CLOSE_RE.sub(_blank, s)
    s = QUOTE_RE.sub(_fill(QMASK), s)
    return s


# --------------------------------------------------------------------------
# Tokens, sentences, word count
# --------------------------------------------------------------------------

TOKEN_RE = re.compile(
    r"(?P<code>[" + MASK + r"]+(?:[\w.\-]*[" + MASK + r"]+)*[\w]*)"
    r"|(?P<quote>[" + QMASK + r"]+)"
    r"|(?P<abbr>(?:[A-Za-z]\.){2,}|(?i:etc|vs|approx|viz|cf|al)\.|"
    r"(?:No|no|Fig|fig|Ref|ref|pp|p)\.(?=\s*\d))"
    r"|(?P<num>\d\w*(?:[.,:]\d+\w*)*(?:-\w+)*)"
    r"|(?P<word>[^\W\d_](?:[\w'’]|-(?=\w))*)"
    r"|(?P<punct>[^\s\w" + MASK + QMASK + r"])")


class Token(object):
    __slots__ = ("type", "text", "start", "end", "lower", "is_caps", "is_cap",
                 "sent_initial", "skip_vocab", "term", "noun_guess", "avoid", "expansion",
                 "term_end")

    def __init__(self, typ, text, start, end):
        self.type = typ
        self.text = text
        self.start = start
        self.end = end
        self.lower = text.lower()
        letters = [c for c in text if c.isalpha()]
        self.is_caps = typ == "word" and len(letters) >= 2 and all(c.isupper() for c in letters)
        self.is_cap = typ == "word" and text[:1].isupper()
        self.sent_initial = False
        self.skip_vocab = False
        self.term = None          # TN or TV from the term list, X for a word not to use
        self.noun_guess = False   # the vocabulary check thinks this is an unlisted noun
        self.avoid = None         # (surface, preferred term) on the first token of a match
        self.expansion = False    # part of the full form of a term-list abbreviation
        self.term_end = None      # on the first token of a multi-word term: end index

    def __repr__(self):
        return "Token(%s,%r)" % (self.type, self.text)


def tokenize(masked):
    toks = []
    for m in TOKEN_RE.finditer(masked):
        typ = m.lastgroup
        text = m.group(0)
        if typ == "word" and any(c.isdigit() for c in text):
            typ = "alnum"
        elif typ == "num" and re.search(r"[A-Za-z]", text) and \
                not re.match(r"^\d+(?:st|nd|rd|th)$", text):
            typ = "alnum"
        toks.append(Token(typ, text, m.start(), m.end()))
    return toks


class Sentence(object):
    def __init__(self, block, tokens):
        self.block = block
        self.tokens = tokens
        self.start = tokens[0].start if tokens else 0
        self.end = tokens[-1].end if tokens else 0
        self.upper = False
        self.imperative = False
        self.main = None          # token index of the main verb position
        self.procedural = False
        self.words = 0
        self.in_note = False
        self.index = 0

    def text(self):
        return self.block.text[self.start:self.end]


def split_sentences(block):
    toks = block.tokens
    groups = []
    cur = []
    depth = 0
    for idx, t in enumerate(toks):
        cur.append(t)
        if t.type == "punct" and t.text in "([":
            depth += 1
        elif t.type == "punct" and t.text in ")]":
            depth = max(0, depth - 1)
        nxt = toks[idx + 1] if idx + 1 < len(toks) else None
        end = False
        if depth == 0 and t.type == "punct" and t.text in ".!?":
            if nxt is None:
                end = True
            elif not (nxt.type == "punct" and nxt.text in ".!?)\"'”’"):
                end = block.masked[t.end:nxt.start].strip() == "" and nxt.start > t.end
        elif depth == 0 and t.type == "punct" and t.text in ")\"'”’" and cur and \
                len(cur) >= 2 and cur[-2].type == "punct" and cur[-2].text in ".!?":
            end = nxt is None or nxt.start > t.end
        elif depth == 0 and t.type == "abbr" and t.lower == "etc." and nxt is not None and \
                (nxt.is_cap or nxt.type in ("code", "quote")):
            end = True
        if end:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return [Sentence(block, g) for g in groups
            if any(t.type in ("word", "alnum", "num", "code", "quote", "abbr") for t in g)]


def is_upper_sentence(tokens):
    words = [t for t in tokens if t.type == "word" and len(t.text) >= 2]
    if len(words) < 3:
        return False
    return sum(1 for t in words if t.is_caps) >= 0.7 * len(words)


def _is_unit(tok):
    if tok.type == "abbr" and tok.lower in ("a.m.", "p.m."):
        return True
    if tok.type == "punct":
        return tok.text in ("%", "°")
    if tok.type != "word":
        return False
    return tok.text in UNIT_TOKENS or tok.lower in UNIT_WORDS


sc_is_unit = _is_unit


def count_words(tokens, upper=False):
    """Count the words of a sentence as Section 8 describes.

    One word each: a number with its unit, an abbreviation, an alphanumeric
    identifier, quoted text, code, a hyphenated group, text in parentheses
    (rule 8.5), a run of capitalized words inside the sentence (proper
    nouns, titles), and a run of uppercase words (labels, screen text).
    """
    n = 0
    i = 0
    L = len(tokens)
    first_word = next((k for k, t in enumerate(tokens) if t.type != "punct"), None)
    while i < L:
        t = tokens[i]
        if t.type == "punct":
            if t.text in "([":
                depth = 1
                j = i + 1
                has = False
                while j < L and depth:
                    tj = tokens[j]
                    if tj.type == "punct" and tj.text in "([":
                        depth += 1
                    elif tj.type == "punct" and tj.text in ")]":
                        depth -= 1
                    elif tj.type != "punct":
                        has = True
                    j += 1
                if has:
                    n += 1
                i = j
                continue
            i += 1
            continue
        if t.type == "num":
            n += 1
            j = i + 1
            if j < L and tokens[j].type == "punct" and tokens[j].text == "°":
                j += 1
            if j < L and _is_unit(tokens[j]):
                j += 1
                if j < L and tokens[j - 1].lower in ("degrees", "degree") and \
                        tokens[j].lower in ("celsius", "fahrenheit", "c", "f"):
                    j += 1
            i = j
            continue
        if t.type == "word" and not upper and i != first_word:
            if t.is_caps:
                j = i + 1
                while j < L and tokens[j].type in ("word", "alnum") and tokens[j].is_caps:
                    j += 1
                n += 1
                i = j
                continue
            if t.is_cap:
                j = i + 1
                last = i
                while j < L:
                    tj = tokens[j]
                    if tj.type == "word" and tj.is_cap:
                        last = j
                        j += 1
                    elif tj.type == "word" and tj.lower in ("of", "and", "the", "for", "de") \
                            and j + 1 < L and tokens[j + 1].type == "word" and \
                            tokens[j + 1].is_cap:
                        j += 1
                    else:
                        break
                n += 1
                i = last + 1
                continue
        n += 1
        i += 1
    return n


# --------------------------------------------------------------------------
# Morphology helpers
# --------------------------------------------------------------------------


def lemma_candidates(w):
    """Possible (lemma, kind) pairs for an inflected surface form."""
    out = []

    def add(b, k):
        if b and len(b) >= 2 and (b, k) not in out:
            out.append((b, k))
    for ap in ("'s", "’s"):
        if w.endswith(ap):
            add(w[:-2], "possessive")
    if w.endswith("s'") or w.endswith("s’"):
        add(w[:-1], "possessive")
    if w.endswith("ies") and len(w) > 4:
        add(w[:-3] + "y", "plural")
    if w.endswith("es") and len(w) > 3:
        add(w[:-2], "plural")
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        add(w[:-1], "plural")
    if w.endswith("ied") and len(w) > 4:
        add(w[:-3] + "y", "past")
    if w.endswith("ed") and len(w) > 4:
        add(w[:-2], "past")
        add(w[:-1], "past")
        if w[-3] == w[-4]:
            add(w[:-3], "past")
    if w.endswith("ing") and len(w) > 4:
        stem = w[:-3]
        add(stem, "ing")
        add(stem + "e", "ing")
        if len(stem) > 2 and stem[-1] == stem[-2]:
            add(stem[:-1], "ing")
        if stem.endswith("y"):
            add(stem[:-1] + "ie", "ing")
    if w.endswith("iest") and len(w) > 5:
        add(w[:-4] + "y", "superlative")
    if w.endswith("est") and len(w) > 5:
        add(w[:-3], "superlative")
        add(w[:-2], "superlative")
        if w[-4] == w[-5]:
            add(w[:-4], "superlative")
    if w.endswith("ier") and len(w) > 4:
        add(w[:-3] + "y", "comparative")
    if w.endswith("er") and len(w) > 4:
        add(w[:-2], "comparative")
        add(w[:-1], "comparative")
        if w[-3] == w[-4]:
            add(w[:-3], "comparative")
    if w.endswith("ly") and len(w) > 4:
        add(w[:-2], "adverb")
        if w.endswith("ily"):
            add(w[:-3] + "y", "adverb")
    return out


def singular(w):
    """A simple singular form of a plural word, for grouping (valves -> valve)."""
    if len(w) <= 3 or w.endswith(("ss", "us", "is")) or not w.endswith("s"):
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("ches", "shes", "xes", "sses", "zes")):
        return w[:-2]
    return w[:-1]


def looks_pp(w, lex=None):
    """True if w can be a past participle."""
    if w in IRREGULAR_PP:
        return True
    if lex is not None:
        for r in lex.lookup(w):
            if r["pos"] == "v" and r["word"] != w and (w.endswith("ed") or w.endswith("en")
                                                        or w.endswith("t")):
                return True
    return w.endswith("ed") and len(w) > 4 and w not in ED_NOT_PP


def verb_base(w, lex=None):
    if lex is not None and lex.is_verb_base(w):
        return True
    return w in BUILTIN_VERBS


def ing_is_verb(w, lex, terms):
    """True if w is an -ing form of a verb (and not an approved -ing word)."""
    if not w.endswith("ing") or len(w) <= 4 or w in ING_NOT_VERB:
        return False
    if terms is not None and terms.match_single(w):
        return False
    cands = [c for c, kind in lemma_candidates(w) if kind == "ing"]
    if lex is not None:
        if any(r["pos"] in ("n", "adj", "prep", "pron", "adv", "conj") and
               not r.get("variant") for r in lex.lookup(w)):
            return False          # listed as a noun or adjective: STE-1.1 decides
        if any(lex.is_verb_base(c) or c in BUILTIN_VERBS for c in cands):
            return True
        if lex.lookup(w):
            return False
        return any(lex.lookup(c) for c in cands)
    if any(c in BUILTIN_VERBS for c in cands):
        return True
    return len(w) > 5


def british(w):
    """Return the American spelling if w looks British, else None."""
    lw = w.lower()
    if lw in BRIT_WORDS:
        return BRIT_WORDS[lw]
    for suf in BRIT_SUFFIXES:
        base = lw[:-len(suf)]
        if lw.endswith(suf) and base in BRIT_WORDS:
            if base.endswith("re") and suf in ("ed", "ing", "er", "ers"):
                continue
            return BRIT_WORDS[base] + suf
        if lw.endswith(suf) and base + "e" in BRIT_WORDS and base.endswith("r") and \
                suf in ("ed", "ing"):
            return None
    m = re.match(r"^([a-z]{2,})(is|ys)(e|es|ed|ing|er|ers|ation|ations|able)$", lw)
    if m:
        stem, mid, suf = m.groups()
        base = stem + mid + "e"
        if base in ISE_EXCEPTIONS or base.endswith(("wise", "cise", "vise", "prise", "guise",
                                                    "noise", "poise")):
            return None
        if mid == "is" and not re.search(
                r"(?:al|ar|an|en|on|iz|ot|at|og|om|im|er|or|ur|ic|it|ag|ad|ph|iv|ul|ev|"
                r"ut|in|il|ol|ym|am|em|et|ab|ob|ub|ip|ap|pt|ct|nt|rt|st|gn)$", stem):
            return None
        return stem + ("iz" if mid == "is" else "yz") + suf
    return None


# --------------------------------------------------------------------------
# The checker
# --------------------------------------------------------------------------


def _art(word):
    return "an" if word[:1] in "aeiou" else "a"


ADJ_SUFFIX_RE = re.compile(r"(?:al|ic|ive|ous|ful|able|ible|less|ary|ory|ant|ent)$")


class Context(object):
    def __init__(self, lexicon=None, terms=None, profile="auto"):
        self.lex = lexicon
        self.terms = terms if terms is not None else TermList()
        self.profile = profile


class DocChecker(object):
    def __init__(self, path, text, flavor, ctx):
        self.path = path
        self.flavor = flavor
        self.ctx = ctx
        self.lex = ctx.lex
        self.terms = ctx.terms
        self.findings = []
        self.blocks = Parser(text, flavor).parse()
        self.abbr_defined = set()
        self.abbr_seen = set()

    def add(self, block, index, sev, rule, msg, suggestion=None, key=None, sent=None):
        line, col = block.where(index)
        excerpt = None
        if sent is not None:
            excerpt = " ".join(block.text[sent.start:sent.end].split())
            if len(excerpt) > 100:
                excerpt = excerpt[:97] + "..."
        self.findings.append(Finding(self.path, line, col, sev, rule, msg, suggestion, key,
                                     excerpt))

    # -- preparation
    def prepare(self):
        for b in self.blocks:
            b.build()
            b.masked = mask_block(b.text, self.flavor)
            b.tokens = tokenize(b.masked)
            b.sentences = split_sentences(b)
            for k, s in enumerate(b.sentences):
                s.index = k
                s.upper = is_upper_sentence(s.tokens)
                for t in s.tokens:
                    if t.type != "punct":
                        t.sent_initial = True
                        break
                self.mark_terms(s)
                s.in_note = b.label in NOTE_LABELS
                self.classify(s)

    def _match_multi(self, toks, i, table):
        """Longest multi-word entry of table that starts at token i: (end, value)."""
        for words, value in table.get(toks[i].lower, []):
            j = i
            for k, target in enumerate(words):
                if j >= len(toks) or toks[j].type not in ("word", "alnum", "num"):
                    break
                w = toks[j].lower
                if not (w == target or (k == len(words) - 1 and
                                        _match_word({target: 1}, w))):
                    break
                j += 1
            else:
                return j, value
        return None, None

    def mark_terms(self, s):
        toks = s.tokens
        terms = self.terms
        i = 0
        while i < len(toks):
            t = toks[i]
            if t.type not in ("word", "alnum"):
                i += 1
                continue
            end_e, _tag = self._match_multi(toks, i, terms.expansions)
            if end_e is not None:
                for x in range(i, end_e):
                    toks[x].term = "TN"
                    toks[x].skip_vocab = True
                    toks[x].expansion = True
                i = end_e
                continue
            end_t, tag = self._match_multi(toks, i, terms.multi)
            end_a, pref = self._match_multi(toks, i, terms.avoid_multi)
            if end_a is not None and (end_t is None or end_a > end_t):
                for x in range(i, end_a):
                    toks[x].term = "X"
                    toks[x].skip_vocab = True
                t.avoid = (s.block.text[t.start:toks[end_a - 1].end], pref)
                i = end_a
                continue
            if end_t is not None:
                for x in range(i, end_t):
                    toks[x].term = tag
                    toks[x].skip_vocab = True
                t.term_end = end_t
                i = end_t
                continue
            if t.type == "word":
                tag = terms.match_single(t.lower)
                if tag is None and "-" in t.lower:
                    tag = terms.match_single(t.lower.replace("-", ""))
                if tag:
                    t.term = tag
                    t.skip_vocab = True
                else:
                    pref = terms.match_avoid(t.lower)
                    if pref:
                        t.term = "X"
                        t.skip_vocab = True
                        t.avoid = (t.text, pref)
            i += 1

    def main_start(self, s):
        """Token index of the first word after a leading condition clause."""
        toks = s.tokens
        k = next((j for j, t in enumerate(toks) if t.type != "punct"), None)
        if k is None:
            return None
        first = toks[k]
        if first.type == "word" and first.lower in CONDITION_STARTERS:
            depth = 0
            comma = None
            for j in range(k + 1, len(toks)):
                t = toks[j]
                if t.type == "punct" and t.text in "([":
                    depth += 1
                elif t.type == "punct" and t.text in ")]":
                    depth -= 1
                elif depth == 0 and t.type == "punct" and t.text == ",":
                    comma = j
                    break
            if comma is None:
                return None
            k = comma + 1
            while k < len(toks) and toks[k].type == "punct":
                k += 1
            if k >= len(toks):
                return None
        while k < len(toks) and toks[k].type == "word" and (
                toks[k].lower in ADVERB_PREFIX or (toks[k].lower.endswith("ly") and
                                                   len(toks[k].lower) > 4 and
                                                   not verb_base(toks[k].lower, self.lex))):
            k += 1
            while k < len(toks) and toks[k].type == "punct" and toks[k].text == ",":
                k += 1
        return k if k < len(toks) else None

    def is_imperative_at(self, s, k):
        toks = s.tokens
        if k is None or k >= len(toks):
            return False
        t = toks[k]
        if t.type != "word":
            return False
        w = t.lower
        if w in ("don't", "don’t"):
            return True
        if w == "do" and k + 1 < len(toks) and toks[k + 1].lower == "not":
            return True
        if w in FUNCTION_WORDS and w not in ("do", "be"):
            return False
        if not (t.term == "TV" or verb_base(w, self.lex)):
            return False
        if t.is_cap and not t.sent_initial and not s.upper:
            return False
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if nxt is not None and nxt.type in ("num", "alnum") and self.lex is not None and \
                self.lex.approved_surface(w, {"n"}) and not self.lex.approved_surface(w, {"v"}):
            return False          # a label such as "Part 2" or "Step 4"
        if nxt is not None and nxt.type == "word":
            if nxt.lower in FINITE:
                return False
            if nxt.lower.endswith("s") and k + 2 < len(toks) and toks[k + 2].lower in FINITE:
                return False
        return True

    def classify(self, s):
        b = s.block
        k = self.main_start(s)
        s.main = k
        s.imperative = b.kind != "heading" and not b.header and self.is_imperative_at(s, k)
        s.words = count_words(s.tokens, s.upper)
        prof = self.ctx.profile
        if b.label in SAFETY_LABELS:
            s.procedural = True
        elif s.in_note:
            s.procedural = False
        elif prof == "procedure":
            s.procedural = True
        elif prof == "description":
            s.procedural = False
        elif b.kind == "list_item" and b.ordered:
            s.procedural = True
        else:
            s.procedural = s.imperative

    # -- run
    def run(self):
        self.prepare()
        self.collect_abbr_definitions()
        for b in self.blocks:
            for s in b.sentences:
                self.check_sentence(s)
            self.check_block(b)
        self.check_lists()
        return one_vocabulary_finding_per_token(self.findings)

    def check_sentence(self, s):
        b = s.block
        heading = b.kind == "heading" or b.header
        self.rule_punctuation(s)
        self.rule_contractions(s)
        self.rule_latin(s)
        self.rule_spelling(s, heading)
        self.rule_pronouns(s)
        self.rule_abbrev(s)
        self.rule_avoid(s)
        if self.lex is not None:
            self.rule_vocabulary(s, heading)
        else:
            self.rule_obligation(s)
        self.rule_noun_clusters(s)
        self.rule_term_variants(s)
        if heading:
            return
        self.rule_terms_pos(s)
        self.rule_length(s)
        consumed = self.rule_verb_constructions(s)
        self.rule_ing(s, consumed)
        self.rule_omission(s)
        self.rule_articles(s)
        self.rule_nominalization(s)
        self.rule_phrasal(s)
        self.rule_procedural(s)
        self.rule_series(s)

    # -- sentence rules
    def rule_length(self, s):
        b = s.block
        if s.procedural and not s.in_note:
            limit, rule, kind = 20, "STE-5.1", "procedural"
        else:
            limit, rule, kind = 25, "STE-6.3", "descriptive"
        if b.label in SAFETY_LABELS:
            kind = "safety instruction"
        elif s.in_note:
            kind = "note"
        if s.words > limit:
            self.add(b, s.start, "warn", rule,
                     "%s sentence has %d words (maximum %d)" % (kind, s.words, limit),
                     "Divide the sentence, or use a vertical list.", sent=s)

    def rule_punctuation(self, s):
        toks = s.tokens
        for t in toks:
            if t.type == "punct" and t.text == ";":
                self.add(s.block, t.start, "warn", "STE-8.1", "semicolon",
                         "Write two sentences.", sent=s)
        for k in range(1, len(toks) - 1):
            t = toks[k]
            if not (t.type == "punct" and t.text == "/"):
                continue
            a, c = toks[k - 1], toks[k + 1]
            if a.type != "word" or c.type != "word" or a.end != t.start or t.end != c.start:
                continue
            if a.is_caps or c.is_caps or len(a.text) < 2 or len(c.text) < 2:
                continue            # abbreviation such as B/C
            if k >= 2 and toks[k - 2].type == "num":
                continue            # unit such as cc/minute
            self.add(s.block, a.start, "info", "STE-X-SLASH",
                     "slash between words '%s/%s'" % (a.text, c.text),
                     "Write 'or' or 'and', or give the two items in full.", sent=s)

    def rule_contractions(self, s):
        for t in s.tokens:
            if t.type == "word" and CONTRACTION_RE.match(t.text):
                self.add(s.block, t.start, "warn", "STE-4.2",
                         "contraction '%s'" % t.text, "Write the words in full.", sent=s)

    def rule_latin(self, s):
        toks = s.tokens
        for k, t in enumerate(toks):
            key = None
            if t.type == "abbr" and t.lower in LATIN:
                key = t.lower
            elif t.type == "word" and t.lower in ("etc", "vs"):
                key = t.lower
            elif t.type == "word" and t.lower == "et" and k + 1 < len(toks) and \
                    toks[k + 1].lower in ("al", "al."):
                key = "et al."
            if key:
                self.add(s.block, t.start, "warn", "STE-GR-6",
                         "Latin abbreviation '%s'" % t.text, "Write: %s." % LATIN[key], sent=s)

    def rule_spelling(self, s, heading):
        for t in s.tokens:
            if t.type != "word" or t.skip_vocab:
                continue
            if t.is_cap and not t.sent_initial and not heading and not s.upper:
                continue
            am = british(t.text)
            if am:
                if t.text.isupper():
                    am = am.upper()
                elif t.text[:1].isupper():
                    am = am.capitalize()
                self.add(s.block, t.start, "warn", "STE-1.14",
                         "British spelling '%s'" % t.text, self._spelling_suggestion(am),
                         key=t.lower, sent=s)

    def _spelling_suggestion(self, am):
        """Suggest the American spelling only if it is an approved word, a term in
        the term list, or a word that the dictionary does not list (a possible
        technical noun). If the dictionary has it only as a word that is not
        approved (or only as a TN alternative), suggest approved words."""
        lex = self.lex
        low = am.lower()
        if lex is None or not lex.lookup(low) or lex.approved_surface(low) or \
                self.terms.match_single(low):
            return "Write '%s'." % am
        recs = lex.lookup(low)
        alts = lex.alternatives(recs, approved_only=True)
        tn_only = lex.is_tn_alternative(low)
        if not alts and tn_only:
            alts = lex.synonyms_by_meaning(next((r["word"] for r in recs), low), "n")
        why = "is only a technical noun in the dictionary" if tn_only else \
            "is not an approved word"
        sugg = "The American spelling '%s' %s." % (am, why)
        if alts:
            sugg += " Use an approved word, for example %s." % ", ".join(alts)
        else:
            sugg += " Rewrite with approved words."
        if tn_only:
            sugg += " Write '%s' only for a technical noun in your term list." % am
        return sugg

    def rule_pronouns(self, s):
        for t in s.tokens:
            if t.type != "word":
                continue
            if t.text == "I" and not s.upper or \
                    (t.lower in ("me", "my", "mine", "myself") and not t.is_caps):
                self.add(s.block, t.start, "info", "STE-X-FIRST-PERSON",
                         "first person '%s'" % t.text,
                         "Write 'you' for the reader, or 'we' for your organization.", sent=s)
            elif t.lower in ("he", "she", "him", "her", "his", "hers", "himself", "herself"):
                if t.is_caps and not s.upper:
                    continue
                self.add(s.block, t.start, "warn", "STE-GR-7",
                         "gender-specific pronoun '%s'" % t.text,
                         "Use a neutral noun, 'you', or 'they'.", sent=s)

    def rule_obligation(self, s):
        """Without the dictionary, report 'shall' and 'should' directly."""
        for t in s.tokens:
            if t.type == "word" and t.lower in ("shall", "should"):
                self.add(s.block, t.start, "warn", "STE-X-OBLIGATION",
                         "'%s' for an obligation" % t.text,
                         "Write 'must' for an obligation, or use the imperative.", sent=s)

    def rule_avoid(self, s):
        """Rule 1.11: a word that the term list says not to use for an item."""
        for t in s.tokens:
            if t.avoid:
                surface, pref = t.avoid
                self.add(s.block, t.start, "warn", "STE-1.11",
                         "'%s' is not the project term: use '%s' instead" % (surface, pref),
                         "One item has one name. The term list gives '%s'." % pref, sent=s)

    def _variant_extra(self, s, x):
        """True if token x can be an extra word before or after a term: a noun or
        an unlisted word, not a grammar word, an adjective, a name, or a term."""
        t = s.tokens[x]
        if t.type != "word" or t.term or t.lower in FUNCTION_WORDS or \
                t.lower in NUMBER_WORDS or (t.is_cap and not t.sent_initial):
            return False
        if s.imperative and s.main == x:
            return False          # the verb of a command
        if self._plain_adjective(t) or (t.lower.endswith("ly") and len(t.lower) > 4):
            return False
        if self.lex is None:
            return t.lower not in COMMON_ADJ and not verb_base(t.lower)
        pos = self.lex.pos_set(t.lower)
        if pos and "n" not in pos and "v" in pos and not pos & {"adj", "adv", "prep"}:
            # Only an unapproved verb in the dictionary: can be a noun ("pump").
            return not self.lex.approved_surface(t.lower) and \
                not t.lower.endswith(("ed", "ing"))
        return not pos or "n" in pos

    def rule_term_variants(self, s):
        """Rule 1.11: a multi-word term with more nouns before it ('fan inlet flow
        probe' for the term 'inlet flow probe') can be a second name for the same
        item. Words after the term are not reported: they usually name a
        different item ('... probe cable')."""
        toks = s.tokens
        for i, t in enumerate(toks):
            if t.term_end is None or t.term != "TN":
                continue
            end = t.term_end
            a = i
            while a > 0 and a > i - 2 and self._variant_extra(s, a - 1):
                a -= 1
            if a == i:
                continue
            term = s.block.text[t.start:toks[end - 1].end]
            span = s.block.text[toks[a].start:toks[end - 1].end]
            self.add(s.block, t.start, "info", "STE-1.11",
                     "'%s' is a variant of the project term '%s'" % (span, term.lower()),
                     "One item has one name. If this is the same item, write '%s'. If it is "
                     "a different item, add its name to the term list." % term.lower(),
                     sent=s)

    # -- abbreviations (rule 2.2 method: full term first, then short form)
    def _abbr_token(self, t, s):
        if t.type != "word" or s.upper or t.avoid:
            return None           # a term-list abbreviation still needs its definition
        core = t.text[:-1] if t.text.endswith("s") and t.text[:-1].isupper() else t.text
        if not (2 <= len(core) <= 6 and core.isupper() and core.isalpha()):
            return None
        return core

    def collect_abbr_definitions(self):
        for b in self.blocks:
            for s in b.sentences:
                toks = s.tokens
                for k, t in enumerate(toks):
                    core = self._abbr_token(t, s)
                    if core and k > 0 and toks[k - 1].text == "(" and k + 1 < len(toks) \
                            and toks[k + 1].text == ")":
                        self.abbr_defined.add(core)

    def rule_abbrev(self, s):
        toks = s.tokens
        for k, t in enumerate(toks):
            core = self._abbr_token(t, s)
            if not core or core in COMMON_ABBR or core in self.abbr_seen:
                continue
            low = core.lower()
            if (self.lex is not None and self.lex.lookup(low)) or low in FUNCTION_WORDS or \
                    low in BUILTIN_VERBS:
                continue          # an ordinary word in capitals, such as a label
            self.abbr_seen.add(core)
            if (k > 0 and toks[k - 1].text == "(") or (k + 1 < len(toks) and
                                                       toks[k + 1].text == "("):
                continue          # "Full Term (ABBR)" or "ABBR (full term)"
            full = self.terms.definitions.get(low)
            sugg = "At the first use, write the full term and then the abbreviation in " \
                   "parentheses."
            if full:
                sugg += " The term list gives: %s" % full.split(". ")[0].rstrip(".")
            if core in self.abbr_defined:
                self.add(s.block, t.start, "warn", "STE-2.2",
                         "abbreviation '%s' is used before its definition" % core, sugg,
                         sent=s)
            elif t.term:
                self.add(s.block, t.start, "info", "STE-2.2",
                         "abbreviation '%s' has no definition in this document (the term "
                         "list is not a definition for the reader)" % core, sugg, sent=s)
            else:
                self.add(s.block, t.start, "info", "STE-2.2",
                         "abbreviation '%s' has no definition" % core,
                         sugg, sent=s)

    # -- vocabulary
    def _vocab_candidates(self, s, heading):
        for k, t in enumerate(s.tokens):
            if t.type != "word" or t.skip_vocab or CONTRACTION_RE.match(t.text):
                continue
            if len(t.text) == 1 and t.lower != "a":
                continue
            if k > 0 and s.tokens[k - 1].type == "num" and sc_is_unit(t):
                continue          # unit of measurement after a number
            if not s.upper:
                if t.is_caps:
                    continue
                if t.is_cap and not t.sent_initial and not heading and \
                        not LETTER_WORD_RE.match(t.text):
                    continue
            yield k, t

    def _alts_msg(self, alts):
        if alts:
            return "Approved alternatives: " + ", ".join(alts)
        return "Rewrite with approved words."

    def rule_vocabulary(self, s, heading):
        lex = self.lex
        toks = s.tokens
        consumed = set()
        for k, t in self._vocab_candidates(s, heading):
            if k in consumed:
                continue
            for phrase in lex.phrases.get(t.lower, []):
                span = []
                j = k
                for w in phrase:
                    if j < len(toks) and toks[j].type == "word" and toks[j].lower == w and \
                            not toks[j].skip_vocab:
                        span.append(j)
                        j += 1
                    else:
                        span = None
                        break
                if not span:
                    continue
                recs = lex.lookup(" ".join(phrase))
                consumed.update(span)
                if not any(r.get("approved") and not r.get("variant") for r in recs):
                    surface = s.block.text[toks[span[0]].start:toks[span[-1]].end]
                    self.add(s.block, t.start, "warn", "STE-1.1",
                             "'%s' is not approved" % surface,
                             self._alts_msg(lex.alternatives(recs)), key=" ".join(phrase),
                             sent=s)
                break
        for k, t in self._vocab_candidates(s, heading):
            if k in consumed:
                continue
            if "-" in t.lower and not lex.lookup(t.lower):
                self._check_hyphenated(s, t)
            else:
                self._check_word(s, k, t, heading)

    def _check_hyphenated(self, s, t):
        lex = self.lex
        unknown = False
        for p in [p for p in t.lower.split("-") if p]:
            recs = lex.lookup(p)
            if not recs:
                cands = [c for c, _kind in lemma_candidates(p) if lex.lookup(c)]
                if not cands:
                    unknown = True
                    continue
                recs = lex.lookup(cands[0])
            if not any(r.get("approved") and not r.get("variant") for r in recs):
                self.add(s.block, t.start, "warn", "STE-1.1",
                         "'%s' (in '%s') is not approved" % (p, t.text),
                         self._alts_msg(lex.alternatives(recs)), key=p, sent=s)
        if unknown:
            self._unknown(s, t)

    def _unknown(self, s, t, note="", as_noun=None):
        """Report a word that the dictionary does not list (rule 1.6).

        as_noun: the parts of speech of the unapproved entries of a word that
        is used here as a noun.
        """
        letter = bool(LETTER_WORD_RE.match(t.text))
        if s.upper or (t.is_cap and not letter) or t.lower in FUNCTION_WORDS or \
                british(t.text):
            return                # proper name, grammar word, or reported as spelling
        k = next((n for n, x in enumerate(s.tokens) if x is t), None)
        hint = "TN"
        if k is not None and not t.noun_guess:
            guess, conf = self.guess_pos(s, k)
            if (guess == {"v"} and conf) or (s.imperative and s.main == k):
                hint = "TV"
        if as_noun:
            names = " or ".join(sorted(_art(POS_NAMES.get(p, p)) + " " + POS_NAMES.get(p, p)
                                       for p in as_noun))
            msg = ("'%s' is not in the dictionary as a noun: the dictionary lists it only "
                   "as %s that is not approved; as a noun it is a possible technical noun. "
                   "Add it to the term list" % (t.text, names))
        else:
            msg = ("'%s' is not in the dictionary%s: technical noun? Add it to the term list"
                   % (t.text, note))
        key = singular(t.lower)
        if letter:
            key = t.text[:2] + key[2:]      # keep "O-ring", "V-belt"
        self.add(s.block, t.start, "info", "STE-1.6", msg, key=key, sent=s)
        self.findings[-1].hint = hint

    # -- unlisted nouns (rule 1.6) that have the spelling of an unapproved verb
    def _modifier_like(self, t):
        if t.type == "alnum":
            return True
        if t.type != "word" or t.lower in FUNCTION_WORDS:
            return False
        if t.term in ("TN", "X") or t.noun_guess:
            return True
        if self.lex is None:
            return False
        pos = self.lex.pos_set(t.lower)
        return not pos or bool(pos & {"adj", "n"})

    def _plain_adjective(self, t):
        """True for a word that is only an adjective ('new', 'used'), not a noun."""
        if t.type != "word" or t.term or t.noun_guess:
            return False
        if self.lex is None:
            return t.lower in COMMON_ADJ
        pos = self.lex.pos_set(t.lower)
        return bool(pos) and "adj" in pos and "n" not in pos

    def _head_position(self, s, k):
        toks = s.tokens
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if nxt is None or nxt.type == "punct":
            return True
        nw = nxt.lower if nxt.type == "word" else None
        if nw == "to" and k + 2 < len(toks) and toks[k + 2].type == "word" and \
                verb_base(toks[k + 2].lower, self.lex):
            return False          # "... happen to end": a verb before an infinitive
        return nw is not None and (nw in PREPOSITIONS or nw in CONJUNCTIONS or
                                   nw in BE_FORMS or nw in MODALS)

    def _object_next(self, s, k):
        toks = s.tokens
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if nxt is None:
            return False
        if nxt.type in ("num", "code", "quote", "alnum"):
            return True
        return nxt.type == "word" and (nxt.lower in POS_DETERMINERS or
                                       nxt.lower in OBJ_PRONOUNS)

    def _noun_opener(self, s, j, strong_only=False):
        """True if token j can come directly before a noun phrase.

        Strong openers (determiners, numbers, quantifiers) always start a noun
        phrase. Weak openers (a preposition, the verb of an imperative) can
        also come before an adjective or an -ing form.
        """
        toks = s.tokens
        p = toks[j]
        if p.type == "num":
            return True
        if p.type != "word":
            return False
        pw = p.lower
        if pw in POS_DETERMINERS or pw in QUANTIFIERS:
            return True
        if strong_only:
            return False
        if pw in PREPOSITIONS and pw not in ("to", "than", "as"):
            return True
        return bool(s.imperative and s.main == j and
                    pw not in ("do", "be", "make", "let", "don't", "don’t"))

    def noun_context(self, s, k, immediate=False):
        """True if token k is probably a noun (or the noun part of a technical noun).

        Contexts: after a determiner, a number, a preposition, or the verb of an
        imperative ("Remove cover from ..."); after adjectives or nouns that
        follow one of these, when k ends the noun phrase; or the subject before
        a form of 'be' or a modal verb.
        """
        toks = s.tokens
        if k == 0 or toks[k].sent_initial:
            nxt = toks[k + 1] if k + 1 < len(toks) else None
            return nxt is not None and nxt.type == "word" and (
                nxt.lower in BE_FORMS or (nxt.lower in MODALS and
                                          nxt.lower not in ("do", "does", "did")))
        prev = toks[k - 1]
        if prev.type == "word" and prev.lower in PRONOUN_DETERMINERS and \
                self._object_next(s, k):
            return False          # "these make the ...": a verb
        if self._noun_opener(s, k - 1, strong_only=True):
            return True
        if self._noun_opener(s, k - 1):
            # "Remove cover from ...": a weak opener needs the end of the noun phrase.
            nxt = toks[k + 1] if k + 1 < len(toks) else None
            return self._head_position(s, k) or (nxt is not None and nxt.term == "TN")
        if prev.type == "punct" and prev.text in ",(:" and self._head_position(s, k) and \
                k + 1 < len(toks) and toks[k + 1].lower in BE_FORMS:
            return True
        if immediate or toks[k].lower in MODALS:
            return False
        j = k - 1
        hops = 0
        adj_only = True
        while j >= 0 and hops < 3 and self._modifier_like(toks[j]):
            if self.lex is None or not (self.lex.pos_set(toks[j].lower) and
                                        self.lex.pos_set(toks[j].lower) <= {"adj", "adv"}):
                adj_only = False
            j -= 1
            hops += 1
        if not (hops > 0 and j >= 0 and self._noun_opener(s, j)):
            return False
        if self._head_position(s, k):
            return True
        # "the electric motor turns": adjectives, the noun, then an approved verb.
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        return adj_only and nxt is not None and nxt.type == "word" and \
            self.lex is not None and self.lex.approved_surface(nxt.lower, {"v"})

    def _names_noun(self, recs):
        """True if an unapproved entry itself points to a noun of the same spelling."""
        for r in recs:
            for e in self.lex.entries(r["word"], r["pos"]):
                w = e["word"]
                for alt in e.get("alternatives") or []:
                    if not isinstance(alt, dict):
                        continue
                    if alt.get("kind") == "TN" and str(alt.get("word", "")).lower() == w:
                        return True
                    ctx = str(alt.get("context") or "").lower()
                    if ctx and re.search(r"\b%s(?:e?s)?\b" % re.escape(w), ctx):
                        return True
        return False

    def probable_noun(self, s, k, recs, upos, guess, conf):
        """Decide if an unapproved verb or adjective entry is used as a noun here."""
        if guess == {"v"} and conf:
            return False
        if (s.imperative and s.main == k) or (s.tokens[k].sent_initial and
                                               not self.noun_context(s, k)):
            return False          # the verb of a command, or the first word
        if not upos <= {"v", "adj", "adv"} or not upos & {"v", "adj"}:
            return False
        if all(r.get("variant") for r in recs):
            # An inflected form: "two fittings", "a fitting". Not "before acting",
            # not "this depends".
            toks = s.tokens
            prev = toks[k - 1] if k > 0 else None
            if prev is not None and prev.type == "word" and prev.lower in SINGULAR_DETS and \
                    toks[k].lower.endswith("s"):
                return False
            return self.plural_noun_context(s, k) or (
                k > 0 and self._noun_opener(s, k - 1, strong_only=True) and
                self._head_position(s, k))
        if "adj" in upos:         # an adjective: a noun only at the end of a noun phrase
            return self._head_position(s, k) and self.noun_context(s, k)
        if guess and conf and "n" in guess and not (guess & upos):
            return True
        if self.noun_context(s, k):
            return True
        if self._object_next(s, k):
            return False
        return self._names_noun(recs)

    def _check_word(self, s, k, t, heading):
        lex = self.lex
        w = t.lower
        if w in NUMBER_WORDS and not lex.lookup(w):
            return
        recs = lex.lookup(w)
        if recs:
            approved = [r for r in recs if r.get("approved") and not r.get("variant")]
            if approved:
                if not heading:
                    self._check_pos(s, k, t, recs, approved)
                return
            use = recs
            guess, conf = self.guess_pos(s, k)
            upos = {r["pos"] for r in recs}
            if self.probable_noun(s, k, recs, upos, guess, conf):
                # Not approved as a verb, but used as a noun: the noun is unlisted
                # (a probable technical noun), so rule 1.6 applies, not rule 1.1.
                t.noun_guess = True
                self._unknown(s, t, as_noun=upos)
                return
            if self._dictionary_tn(s, k, t, guess, conf):
                # The dictionary gives this word as a technical noun (TN) in the
                # alternatives of an entry ("<verb> (v)" -> "<verb>ing (TN)").
                t.term = "TN"
                t.skip_vocab = True
                return
            if guess and len(upos) > 1:
                use = [r for r in recs if r["pos"] in guess] or recs
            self.add(s.block, t.start, "warn", "STE-1.1", "'%s' is not approved" % t.text,
                     self._alts_msg(lex.alternatives(use)), key=w, sent=s)
            return
        for lemma, kind in lemma_candidates(w):
            want = KIND_POS.get(kind)
            lrecs = [r for r in lex.lookup(lemma) if want is None or r["pos"] in want]
            if not lrecs:
                continue
            approved = [r for r in lrecs if r.get("approved") and not r.get("variant")]
            if not approved:
                if kind == "adverb":
                    continue
                guess, conf = self.guess_pos(s, k)
                if kind == "plural" and not any(r["pos"] == "n" for r in lrecs) and (
                        (guess and conf and "n" in guess) or
                        self.plural_noun_context(s, k) or
                        (not (guess == {"v"} and conf) and self._head_position(s, k) and
                         self.noun_context(s, k))):
                    t.noun_guess = True
                    self._unknown(s, t, as_noun={r["pos"] for r in lrecs})
                    return
                self.add(s.block, t.start, "warn", "STE-1.1",
                         "'%s' (form of '%s') is not approved" % (t.text, lemma),
                         self._alts_msg(lex.alternatives(lrecs)), key=w, sent=s)
                return
            apos = {r["pos"] for r in approved}
            if kind in ("possessive", "plural", "ing"):
                return            # plural nouns pass; STE-3.5 reports -ing forms
            if kind == "past":
                self.add(s.block, t.start, "info", "STE-1.4",
                         "'%s' is not a listed form of the verb '%s'" % (t.text, lemma),
                         "Use a verb form that the dictionary lists.", key=w, sent=s)
                return
            if kind in ("comparative", "superlative") and "adj" in apos:
                self.add(s.block, t.start, "info", "STE-1.4",
                         "'%s' is not a listed form of the adjective '%s'" % (t.text, lemma),
                         "Write 'more %s' or 'most %s', or rewrite." % (lemma, lemma),
                         key=w, sent=s)
                return
            if kind == "adverb":
                break
        self._unknown(s, t)

    def _dictionary_tn(self, s, k, t, guess, conf):
        """True if the dictionary lists this word as a technical noun alternative
        and it is not used as a verb here (a heading, a name, 'the <word>')."""
        recs = self.lex.lookup(t.lower)
        if any(r["pos"] == "n" and not r.get("variant") for r in recs):
            return False          # the noun itself is not approved: STE-1.1
        toks = s.tokens
        prev = toks[k - 1] if k > 0 else None
        if t.lower not in self.lex.tn_alts:
            # A plural ("labels"): also the -s form of a verb ("the list covers").
            if not self.lex.is_tn_alternative(t.lower) or not (
                    prev is None or prev.type in ("punct", "num") or
                    (prev.type == "word" and (prev.lower in POS_DETERMINERS or
                                              prev.lower in QUANTIFIERS or
                                              prev.lower in PREPOSITIONS))):
                return False
        if (s.imperative and s.main == k) or (guess == {"v"} and conf):
            return False
        if self._object_next(s, k) and not (
                prev is not None and prev.type == "word" and prev.lower in POS_DETERMINERS):
            return False          # "before defrosting the unit": a verb with an object
        return True

    def guess_pos(self, s, k):
        """Guess the part of speech of token k from its context.

        Returns (set_of_pos, confident) or (None, False).
        """
        toks = s.tokens
        prev = toks[k - 1] if k > 0 else None
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        pw = prev.lower if prev is not None and prev.type == "word" else None
        nw = nxt.lower if nxt is not None and nxt.type == "word" else None
        obj_next = nxt is not None and (
            (nw is not None and (nw in POS_DETERMINERS or nw in OBJ_PRONOUNS))
            or nxt.type in ("num", "code", "quote", "alnum"))
        if pw in MODALS and pw not in ("do", "does", "did"):
            return {"v"}, True
        if pw in ("do", "does", "did"):
            return {"v"}, True
        if pw == "not" and k >= 2 and toks[k - 2].lower in MODALS:
            return {"v"}, True
        if pw in ("you", "we", "they"):
            return {"v"}, True
        if pw == "to":
            return ({"v"}, True) if obj_next else (None, False)
        w = toks[k].lower
        verbish = self.lex is not None and any(r["pos"] == "v" for r in self.lex.lookup(w))
        if pw in PRONOUN_DETERMINERS or (prev is not None and prev.type == "num") or \
                pw in QUANTIFIERS:
            if verbish:
                return None, False    # "these make ...", "Section 4 holds ..."
            return {"n", "adj"}, False
        if pw in POS_DETERMINERS:
            if w.endswith(("ed", "ing")):
                return {"adj", "n"}, False
            return {"n", "adj"}, True
        if nw in BE_FORMS or (nw in MODALS and nw not in ("do", "does", "did")):
            if toks[k].sent_initial or (prev is not None and prev.type == "punct"):
                return {"n", "pron"}, True
        if s.main == k and s.imperative and obj_next:
            return {"v"}, True
        if pw in BE_FORMS:
            return {"adj", "n", "adv"}, False
        if pw in PREPOSITIONS:
            return {"n", "adj"}, False
        return None, False

    def plural_noun_context(self, s, k):
        """True if an -s word looks like a plural noun: 'the log files (...)'."""
        toks = s.tokens
        w = toks[k].lower
        prev = toks[k - 1] if k > 0 else None
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        nw = nxt.lower if nxt is not None and nxt.type == "word" else None
        return (w.endswith("s") and not w.endswith("ss") and prev is not None and
                prev.type == "word" and prev.lower not in FUNCTION_WORDS and
                (nxt is None or nxt.type == "punct" or nw in PREPOSITIONS or
                 nw in CONJUNCTIONS or nw in BE_FORMS))

    def _check_pos(self, s, k, t, recs, approved):
        lex = self.lex
        w = t.lower
        apos = {r["pos"] for r in approved}
        if w in FUNCTION_WORDS or not apos & {"n", "v", "adj", "adv"}:
            return
        guess, confident = self.guess_pos(s, k)
        if not guess or guess & apos:
            return
        if "adj" in guess and "v" in apos and looks_pp(w, lex):
            return                # rule 3.3: participle used as an adjective
        unapproved = [r for r in recs if (not r.get("approved") or r.get("variant"))
                      and r["pos"] in guess]
        names = "/".join(sorted(POS_NAMES.get(p, p) for p in apos))
        gname = "/".join(sorted(POS_NAMES.get(p, p) for p in guess))
        alts = lex.alternatives(unapproved) if unapproved else []
        sugg = ("Approved alternatives: %s" % ", ".join(alts)) if alts else \
            "Use '%s' only as a %s, or rewrite." % (w, names)
        self.add(s.block, t.start, "warn" if confident else "info", "STE-1.2",
                 "'%s' is approved as %s %s, not as %s %s%s" %
                 (t.text, _art(names), names, _art(gname), gname,
                  "" if confident else " (heuristic guess)"),
                 sugg, key="%s|%s" % (w, gname), sent=s)

    def rule_terms_pos(self, s):
        for k, t in enumerate(s.tokens):
            if t.term not in ("TN", "TV") or t.type != "word":
                continue
            guess, confident = self.guess_pos(s, k)
            if not guess or not confident:
                continue
            if t.term == "TN" and guess == {"v"}:
                self.add(s.block, t.start, "info", "STE-1.7",
                         "technical noun '%s' used as a verb" % t.text,
                         "Use an approved verb with the technical noun.", sent=s)
            elif t.term == "TV" and "v" not in guess and "n" in guess and \
                    not t.lower.endswith("ed"):
                self.add(s.block, t.start, "info", "STE-1.13",
                         "technical verb '%s' used as a noun" % t.text,
                         "Use the technical verb as a verb.", sent=s)

    # -- verbs
    def _skip_adverbs(self, toks, j, limit=2):
        n = 0
        while j < len(toks) and n < limit and toks[j].type == "word" and (
                toks[j].lower in ("not", "also", "always", "never", "then", "now", "only",
                                  "still", "already", "all", "both", "usually", "often",
                                  "sometimes", "first", "again", "just", "each")
                or (toks[j].lower.endswith("ly") and len(toks[j].lower) > 4)):
            j += 1
            n += 1
        return j

    def _pp_adjectival(self, w):
        if w in STATE_ADJ:
            return True
        return self.lex is not None and self.lex.approved_surface(w, {"adj"})

    def _stative(self, s, k, j):
        """'The valve is closed.': 'is'/'are' + a participle that tells a
        condition (no agent, no adverb of time or manner between them)."""
        toks = s.tokens
        if toks[k].lower not in ("is", "are") or toks[j].lower not in STATE_PP:
            return False
        if any(toks[x].lower != "not" for x in range(k + 1, j)):
            return False          # "is then removed", "is quickly closed": an action
        nxt = toks[j + 1] if j + 1 < len(toks) else None
        return nxt is None or nxt.type == "punct" or (
            nxt.type == "word" and (nxt.lower in PREPOSITIONS or nxt.lower in CONJUNCTIONS)
            and nxt.lower not in ("by", "with"))

    def rule_verb_constructions(self, s):
        """Passive voice, perfect and progressive tenses, complex constructions."""
        toks = s.tokens
        consumed = set()
        lex = self.lex
        k = 0
        while k < len(toks):
            t = toks[k]
            if t.type != "word":
                k += 1
                continue
            w = t.lower
            if w in HAVE_FORMS:
                j = self._skip_adverbs(toks, k + 1)
                if j < len(toks) and toks[j].type == "word":
                    x = toks[j].lower
                    if x == "been":
                        j2 = self._skip_adverbs(toks, j + 1)
                        what = "perfect tense"
                        end = j
                        if j2 < len(toks) and toks[j2].type == "word":
                            y = toks[j2].lower
                            if looks_pp(y, lex):
                                what, end = "perfect passive", j2
                            elif y.endswith("ing"):
                                what, end = "perfect progressive", j2
                            consumed.add(j2)
                        self.add(s.block, t.start, "warn", "STE-3.4",
                                 "complex verb construction (%s) '%s'" %
                                 (what, s.block.text[t.start:toks[end].end]),
                                 "Use the simple past or the simple present tense.", sent=s)
                        k = end + 1
                        continue
                    if looks_pp(x, lex) and x != "got":
                        after = toks[j + 1] if j + 1 < len(toks) else None
                        verbal = after is None or after.type in ("punct", "num", "code",
                                                                 "quote") or \
                            (after.type == "word" and (after.lower in POS_DETERMINERS or
                                                       after.lower in OBJ_PRONOUNS or
                                                       after.lower in PREPOSITIONS or
                                                       after.lower in CONJUNCTIONS))
                        if verbal or not self._pp_adjectival(x):
                            consumed.add(j)
                            self.add(s.block, t.start, "warn" if verbal else "info",
                                     "STE-3.4",
                                     "perfect tense '%s %s'" % (t.text, toks[j].text),
                                     "Use the simple past tense.", sent=s)
                            k = j + 1
                            continue
            if w in BE_FORMS or w in GET_FORMS:
                j = self._skip_adverbs(toks, k + 1)
                if j >= len(toks) or toks[j].type != "word" or toks[j].skip_vocab:
                    k += 1
                    continue
                x = toks[j].lower
                if w in BE_FORMS and x.endswith("ing") and ing_is_verb(x, lex, self.terms):
                    consumed.add(j)
                    self.add(s.block, t.start, "warn", "STE-3.2",
                             "progressive tense '%s %s'" % (t.text, toks[j].text),
                             "Use the simple present, simple past, or simple future tense.",
                             sent=s)
                    k = j + 1
                    continue
                if not looks_pp(x, lex):
                    k += 1
                    continue
                prevw = toks[k - 1].lower if k > 0 and toks[k - 1].type == "word" else None
                prev2 = toks[k - 2].lower if k > 1 and toks[k - 2].type == "word" else None
                agent = False
                q = j + 1
                while q < len(toks) and q <= j + 6:
                    if toks[q].type == "word" and toks[q].lower == "by":
                        a = toks[q + 1] if q + 1 < len(toks) else None
                        agent = a is not None and not (a.type == "word" and (
                            a.lower in AGENT_NOT or a.lower.endswith("ing")))
                        break
                    if toks[q].type == "punct" and toks[q].text in ",;:":
                        break
                    q += 1
                complex_ = w == "be" and (prevw in MODALS or prevw == "to" or
                                          (prevw == "not" and prev2 in MODALS))
                span = s.block.text[(toks[k - 1].start if complex_ else t.start):toks[j].end]
                consumed.add(j)
                if complex_:
                    self.add(s.block, t.start, "warn", "STE-3.4",
                             "complex passive construction '%s'" % span,
                             "Use the active voice, or the imperative in a procedure.", sent=s)
                elif agent:
                    self.add(s.block, t.start, "warn", "STE-3.6",
                             "passive voice with an agent ('%s ... by')" % span,
                             "Make the agent the subject of an active sentence.", sent=s)
                elif w in GET_FORMS:
                    self.add(s.block, t.start, "info", "STE-3.6",
                             "possible passive voice '%s'" % span, "Use the active voice.",
                             sent=s)
                elif not self._pp_adjectival(x) and not self._stative(s, k, j):
                    self.add(s.block, t.start, "warn" if s.procedural else "info", "STE-3.6",
                             "possible passive voice '%s'" % span,
                             "Prefer the active voice. A description can keep the passive "
                             "if nobody knows who or what did the action. A participle that "
                             "describes a state is not passive.", sent=s)
                k = j + 1
                continue
            k += 1
        return consumed

    def _ing_noun_use(self, s, k):
        """True if the -ing word k is the head noun of a noun phrase: after a
        determiner, a number, or a quantifier (with adjectives between), and
        before a preposition, a conjunction, a verb 'be', or the end."""
        toks = s.tokens
        if not self._head_position(s, k):
            return False
        j = k - 1
        while j >= 0 and j >= k - 3 and self._plain_adjective(toks[j]):
            j -= 1
        return j >= 0 and j < k and self._noun_opener(s, j, strong_only=True)

    def rule_ing(self, s, consumed):
        toks = s.tokens
        for k, t in enumerate(toks):
            if k in consumed or t.type != "word" or t.skip_vocab:
                continue
            if (t.is_caps or (t.is_cap and not t.sent_initial)) and not s.upper:
                continue
            if not ing_is_verb(t.lower, self.lex, self.terms):
                continue
            if self._ing_noun_use(s, k):
                continue          # "a fitting", "the three new fittings": a technical noun
            prev = toks[k - 1] if k > 0 else None
            pw = prev.lower if prev is not None and prev.type == "word" else None
            nxt = toks[k + 1] if k + 1 < len(toks) else None
            nw = nxt.lower if nxt is not None and nxt.type == "word" else None
            if t.sent_initial or (prev is not None and prev.type == "punct" and
                                  prev.text == ","):
                sev, why = "warn", "starts a clause"
            elif pw in PREPOSITIONS or pw in CONJUNCTIONS:
                sev, why = "warn", "after '%s'" % prev.text
            elif pw in POS_DETERMINERS or pw in QUANTIFIERS:
                sev, why = "info", "noun or modifier: acceptable only inside a technical noun"
            else:
                sev, why = "info", "verb use"
            self.add(s.block, t.start, sev, "STE-3.5",
                     "-ing form '%s' (%s)" % (t.text, why),
                     "Use a different construction, for example 'when you <verb>' or "
                     "'to <verb>'. For a technical noun, record the full noun in the term "
                     "list.", sent=s)

    def rule_omission(self, s):
        toks = [t for t in s.tokens if t.type != "punct" or t.text == ","]
        if len(toks) < 2 or toks[0].type != "word":
            return
        first = toks[0].lower
        if first in ("if", "when", "unless", "once", "where") and len(toks) >= 3:
            x = toks[1]
            if x.type == "word" and (x.lower == "not" or (looks_pp(x.lower, self.lex) and
                                                          toks[2].text == ",")):
                self.add(s.block, toks[0].start, "info", "STE-4.2",
                         "possible omitted subject in '%s %s'" % (toks[0].text, x.text),
                         "Write the subject and the verb in full, for example 'If the part "
                         "is installed'.", sent=s)
        elif first in ("can", "must", "will", "may", "should") and toks[0].is_cap and \
                toks[1].type == "word" and toks[1].lower in {"be"} | BUILTIN_VERBS and \
                not s.text().rstrip().endswith("?"):
            self.add(s.block, toks[0].start, "info", "STE-4.2",
                     "possible omitted subject ('%s %s')" % (toks[0].text, toks[1].text),
                     "Write the subject of the sentence.", sent=s)

    def rule_articles(self, s):
        toks = s.tokens
        if self._list_fragment(s):
            return                # "Hex key, 4 mm": an item of a parts list
        # "the" + noun + alphanumeric identifier: no article.
        for k in range(len(toks) - 2):
            if toks[k].type == "word" and toks[k].lower == "the":
                nxt = toks[k + 1]
                if nxt.type == "word" and nxt.is_cap and not nxt.sent_initial and \
                        not s.upper:
                    continue      # a product name: "the Zorbex QX-7"
                j = k + 1
                while j < len(toks) and j <= k + 2 and toks[j].type == "word" and \
                        not toks[j].is_caps and toks[j].lower not in FUNCTION_WORDS:
                    j += 1
                if k + 1 < j < len(toks) and toks[j].type == "alnum" and \
                        (j + 1 >= len(toks) or toks[j + 1].type == "punct" or
                         toks[j + 1].lower in FUNCTION_WORDS):
                    self.add(s.block, toks[k].start, "info", "STE-4.5",
                             "article before a noun with an identifier ('%s')" %
                             s.block.text[toks[k].start:toks[j].end],
                             "Omit 'the' when an identifier follows the noun.", sent=s)
        self._bare_noun_after_preposition(s)
        if not s.imperative or self.lex is None or s.main is None:
            return
        k = s.main
        if toks[k].lower in ("do", "don't", "don’t", "make", "be"):
            return
        j = k + 1
        if j >= len(toks) or toks[j].type != "word":
            return
        t = toks[j]
        w = t.lower
        if t.is_cap or t.is_caps or w in FUNCTION_WORDS or w.endswith("ly") or \
                w in PARTICLES or (w.endswith("s") and not w.endswith("ss")):
            return
        pos = self.lex.pos_set(w)
        if not pos:
            nxt = toks[j + 1] if j + 1 < len(toks) else None
            if w.endswith(("ed", "ing")) or ADJ_SUFFIX_RE.search(w) or \
                    any(self.lex.lookup(c) for c, _k in lemma_candidates(w)) or \
                    not (nxt is None or nxt.type == "punct" or nxt.lower in PREPOSITIONS
                         or nxt.lower in CONJUNCTIONS):
                return            # an unlisted word followed by more words: maybe a modifier
        elif t.term != "TN" and not t.noun_guess and \
                ("n" not in pos or pos & {"adj", "adv", "prep", "v"}):
            return
        q = j + 1
        while q < len(toks) and q <= j + 4:
            if toks[q].type in ("alnum", "num", "code", "quote") or toks[q].is_caps:
                return            # a noun with an identifier takes no article
            if toks[q].type == "punct" or toks[q].lower in PREPOSITIONS:
                break
            q += 1
        self.add(s.block, t.start, "info", "STE-4.5",
                 "no article before the noun '%s'" % t.text,
                 "Use 'the', 'a', 'an', 'this', or 'these' where applicable.", sent=s)

    def _list_fragment(self, s):
        """True for an item of a bulleted list that is a name, not a sentence:
        no end period and no finite verb ("Hex key, 4 mm")."""
        b = s.block
        if b.kind != "list_item" or b.ordered:
            return False
        if b.masked.rstrip()[-1:] in (".", "!", "?"):
            return False
        return not any(t.type == "word" and (t.lower in FINITE or t.lower in MODALS)
                       for t in s.tokens)

    def _bare_noun_after_preposition(self, s):
        """'... from reservoir.': a singular technical noun with no article."""
        toks = s.tokens
        for k in range(1, len(toks)):
            t, p = toks[k], toks[k - 1]
            if t.type != "word" or p.type != "word" or t.is_cap or t.is_caps:
                continue
            if p.lower not in ("from", "in", "into", "on", "onto", "to", "with", "below",
                               "above", "under", "near", "behind", "through", "for"):
                continue
            if not (t.term == "TN" or t.noun_guess) or t.avoid:
                continue
            if k >= 2 and toks[k - 2].type == "word" and toks[k - 2].term == t.term and \
                    toks[k - 2].skip_vocab and t.term == "TN" and p.skip_vocab:
                continue          # inside a multi-word term such as "unit under test"
            if t.lower != singular(t.lower) or t.lower.endswith("ing"):
                continue          # plural or -ing: no article needed
            j = k
            while j + 1 < len(toks) and toks[j + 1].type == "word" and \
                    toks[j + 1].term == "TN" and toks[j + 1].skip_vocab and \
                    toks[j].term == "TN":
                j += 1            # the rest of a multi-word technical noun
            if not self._head_position(s, j):
                continue
            self.add(s.block, t.start, "info", "STE-4.5",
                     "no article before the noun '%s'" % s.block.text[t.start:toks[j].end],
                     "Use 'the', 'a', 'an', 'this', or 'these' where applicable.", sent=s)

    def rule_nominalization(self, s):
        """Rule 3.7: 'the removal of' where an approved verb exists."""
        if self.lex is None:
            return
        toks = s.tokens
        for k in range(len(toks) - 2):
            a, n, o = toks[k], toks[k + 1], toks[k + 2]
            if a.type != "word" or n.type != "word" or o.type != "word":
                continue
            if a.lower not in ("the", "a", "an") or o.lower != "of":
                continue
            m = re.match(r"^(.{3,}?)(ation|ition|tion|sion|ment|al|ance|ence)$", n.lower)
            if not m:
                continue
            stem = m.group(1)
            for cand in (stem, stem + "e", stem + "ate", stem[:-1] if stem.endswith("i")
                         else stem, stem + "t"):
                if cand != n.lower and self.lex.is_verb_base(cand) and \
                        self.lex.approved_surface(cand, {"v"}):
                    self.add(s.block, n.start, "info", "STE-3.7",
                             "noun '%s' describes an action" % n.text,
                             "Use the approved verb '%s' (for example 'before you %s ...')."
                             % (cand, cand), sent=s)
                    break

    def rule_phrasal(self, s):
        toks = s.tokens
        lex = self.lex
        for k in range(len(toks) - 1):
            t, p = toks[k], toks[k + 1]
            if t.type != "word" or p.type != "word" or p.lower not in PARTICLES:
                continue
            if t.skip_vocab or p.skip_vocab:
                continue
            w = t.lower
            lemma = w if verb_base(w, lex) else None
            if lemma is None:
                for c, kind in lemma_candidates(w):
                    if kind in ("past", "plural", "ing") and verb_base(c, lex):
                        lemma = c
                        break
            if lemma is None and lex is not None:
                lemma = next((r["word"] for r in lex.lookup(w) if r["pos"] == "v"), None)
            if lemma is None:
                continue
            if k > 0 and toks[k - 1].type == "word" and toks[k - 1].lower in POS_DETERMINERS:
                continue
            after = toks[k + 2] if k + 2 < len(toks) else None
            if after is not None and after.type == "word" and after.lower in (
                    "of", "from", "to", "into", "onto", "through"):
                continue            # movement: "out of", "down to"
            if lemma in DIRECTION_VERBS and p.lower in ("up", "down") and (
                    after is None or after.type == "punct" or
                    (after.type == "word" and (after.lower in CONJUNCTIONS or
                                               after.lower in ("toward", "towards")))):
                continue            # a direction: "the tab points up."
            if lex is not None and (lex.lookup("%s %s" % (lemma, p.lower)) or
                                    lex.lookup("%s %s" % (w, p.lower))):
                continue            # listed entry: STE-1.1 decides
            self.add(s.block, t.start, "info", "STE-9.3",
                     "possible phrasal verb '%s %s'" % (t.text, p.text),
                     "Use one approved verb with its approved meaning.", sent=s)

    def rule_noun_clusters(self, s):
        toks = s.tokens
        lex = self.lex

        def nounish(t):
            if t.type == "alnum":
                return True
            if t.type != "word":
                return False
            if t.term:
                return True
            w = t.lower
            if w in FUNCTION_WORDS or (w.endswith("ly") and len(w) > 4):
                return False
            if lex is not None:
                pos = lex.pos_set(w)
                if pos:
                    if pos & {"prep", "conj", "pron", "art", "adv"}:
                        return False
                    if "v" in pos and not pos & {"n", "adj"}:
                        # A word listed only as a verb that is not approved can be a
                        # noun in a technical noun ("power", "alert").
                        return not lex.approved_surface(w) and not w.endswith(("ed", "s"))
                    return True
                for lemma, kind in lemma_candidates(w):
                    want = KIND_POS.get(kind)
                    lp = {p for p in lex.pos_set(lemma) if want is None or p in want}
                    if lp:
                        if kind in ("past", "ing") and "v" in lp:
                            return kind == "ing"
                        if kind == "plural":
                            return "n" in lp
                        return bool(lp & {"n", "adj"})
                return True
            if w in IRREGULAR_PP:
                return False
            for lemma, kind in lemma_candidates(w):
                if kind in ("past", "plural") and lemma in BUILTIN_VERBS:
                    return False
            return True

        L = len(toks)
        k = 0
        while k < L:
            t = toks[k]
            prev = toks[k - 1] if k > 0 else None
            starts = prev is None or prev.type == "num" or \
                (prev.type == "word" and (prev.lower in POS_DETERMINERS or
                                          prev.lower in PREPOSITIONS)) or \
                (prev.type == "punct" and prev.text in ",(:")
            if t.sent_initial and t.type == "word" and s.block.kind != "heading" and \
                    not s.block.header and (
                        s.imperative or verb_base(t.lower, lex) or lex is None or
                        not lex.pos_set(t.lower) or "v" in lex.pos_set(t.lower)):
                starts = False    # the first word of a sentence is often its verb
            if not starts or not nounish(t) or (t.is_cap and not t.is_caps and
                                                not s.upper and not t.sent_initial):
                k += 1
                continue
            def verb_s(tok):
                w = tok.lower
                if tok.type != "word" or not w.endswith("s") or w.endswith("ss"):
                    return False
                base = w[:-2] if w.endswith("es") and not verb_base(w[:-1], lex) else w[:-1]
                if lex is not None:
                    return any(r["pos"] == "v" for r in lex.lookup(w)) or \
                        verb_base(w[:-1], lex) or verb_base(base, lex)
                return w[:-1] in BUILTIN_VERBS or base in BUILTIN_VERBS

            j = k
            while j < L and nounish(toks[j]) and not (
                    j > k and toks[j].is_cap and not toks[j].is_caps and not s.upper):
                if j + 1 < L and nounish(toks[j + 1]) and verb_s(toks[j]) and \
                        not (toks[j + 1].is_cap and not toks[j + 1].is_caps):
                    break         # "the tool uses power ...": a verb, not a modifier
                if j > k and toks[j].lower.endswith("ing") and \
                        toks[j - 1].lower.endswith("s"):
                    break         # "... parts holding ...": a participle clause
                j += 1
            # Adjectives before the nouns ("new", "used") are not part of the noun.
            k0 = k
            while k0 < j and self._plain_adjective(toks[k0]):
                k0 += 1
            units = j - k0
            if any(toks[x].expansion for x in range(k0, j)):
                units = 0         # the full form of a term-list abbreviation
            if units >= 4 and toks[j - 1].type == "word":
                span = s.block.text[toks[k0].start:toks[j - 1].end]
                self.add(s.block, toks[k0].start, "info", "STE-2.1",
                         "possible multi-word noun of %d words '%s'" % (units, span),
                         "Use three words or fewer, or use prepositions ('the X of the Y').",
                         sent=s)
            k = max(j, k + 1)

    # -- procedures, notes, safety
    def _obligation_clause(self, s):
        """Index of 'must'/'should'/'shall' in a main clause '<subject> must <verb>'
        (not in a clause after 'because', 'that', 'if', ...), else None."""
        toks = s.tokens
        for m, t in enumerate(toks):
            if t.type != "word" or t.lower not in ("must", "should", "shall"):
                continue
            v = self._skip_adverbs(toks, m + 1)
            if v >= len(toks) or toks[v].type != "word" or not (
                    toks[v].lower == "be" or verb_base(toks[v].lower, self.lex)):
                continue
            start = m
            while start > 0 and not (toks[start - 1].type == "punct" and
                                     toks[start - 1].text in ";:"):
                start -= 1
            clause = toks[start:m]
            if not any(x.type in ("word", "alnum", "code") for x in clause):
                continue          # no subject
            if start == 0 and s.imperative:
                continue          # "Make sure that ... must": part of the command
            if any(x.type == "word" and x.lower in SUBORDINATORS for x in clause):
                continue          # "because the pump must start": a reason
            return m
        return None

    def rule_procedural(self, s):
        b = s.block
        toks = s.tokens
        words = [t for t in toks if t.type == "word"]
        lw = [t.lower for t in words]
        if s.in_note:
            if s.imperative:
                self.add(b, s.start, "warn", "STE-5.5", "instruction in a note",
                         "Put the instruction in a work step. A note gives information "
                         "only.", sent=s)
            if RISK_RE.search(s.text()):
                self.add(b, s.start, "info", "STE-7.1", "note tells about a risk",
                         "Persons can get hurt: write a WARNING. Equipment can break: "
                         "write a CAUTION.", sent=s)
            return
        if b.label == "CAUTION" and PERSON_RISK_RE.search(s.text()):
            self.add(b, s.start, "info", "STE-7.1",
                     "CAUTION tells about a risk to persons",
                     "Persons can get hurt: use WARNING.", sent=s)
        if b.label is None and (s.imperative or "not" in lw) and RISK_RE.search(s.text()) \
                and CAUSE_RE.search(s.text()):
            self.add(b, s.start, "info", "STE-7.1",
                     "possible safety instruction without a WARNING or CAUTION label",
                     "Identify the level of risk with WARNING (injury) or CAUTION (damage).",
                     sent=s)
        elif b.label is None and not s.upper and OBLIGATION_SUBJ_RE.search(s.text()) and \
                (PPE_RE.search(s.text()) or PERSON_RISK_RE.search(s.text())):
            self.add(b, s.start, "info", "STE-7.1",
                     "obligation for the safety of persons without a WARNING or CAUTION "
                     "label",
                     "If persons can get hurt, write a WARNING that starts with the command "
                     "(for example 'WARNING: WEAR ...') and tells the risk.", sent=s)
        if not s.procedural:
            return
        # Rule 5.3: instructions in the imperative.
        in_steps = b.kind == "list_item" or self.ctx.profile == "procedure"
        done = False
        if not s.imperative and not s.upper and b.label is None and s.index == 0 and \
                in_steps:
            subj = any(lw[i] in ("you", "user", "users", "operator", "reader") and
                       lw[i + 1] in ("must", "should", "shall", "need", "needs", "have",
                                     "has", "will", "can")
                       for i in range(len(lw) - 1))
            if subj or (lw and lw[0] in ARTICLES and
                        any(x in ("should", "shall", "must", "will") for x in lw[:6])):
                done = True
                self.add(b, s.start, "info", "STE-5.3",
                         "step is not written as a command",
                         "Start the instruction with the verb, for example 'Open the "
                         "cover.'", sent=s)
        if not done and not s.upper and b.label is None and in_steps:
            m = self._obligation_clause(s)
            if m is not None:
                self.add(b, toks[m].start, "info", "STE-5.3",
                         "statement with '%s' in a step: write it as a command" %
                         toks[m].text,
                         "Write the instruction as a command, for example 'Make sure that "
                         "the lid is closed.'", sent=s)
        if not s.imperative:
            return
        # Rule 5.2: one instruction per sentence.
        main = s.main or 0
        verbs = set()
        second = None
        for k in range(main + 2, len(toks) - 1):
            t = toks[k]
            if not ((t.type == "word" and t.lower in ("and", "then")) or
                    (t.type == "punct" and t.text == ",")):
                continue
            j = k + 1
            if j < len(toks) and toks[j].type == "word" and toks[j].lower == "then":
                j += 1
            if j >= len(toks) or toks[j].type != "word":
                continue
            v = toks[j]
            if j in verbs or v.is_cap or not (verb_base(v.lower, self.lex) or v.term == "TV"):
                continue
            nxt = toks[j + 1] if j + 1 < len(toks) else None
            if nxt is not None and ((nxt.type == "word" and (
                    nxt.lower in POS_DETERMINERS or nxt.lower in OBJ_PRONOUNS or
                    nxt.lower == "sure")) or nxt.type in ("num", "code", "quote", "alnum")):
                verbs.add(j)
                second = second or v
        count = 1 + len(verbs)
        if count >= 2:
            self.add(b, second.start, "warn" if count >= 3 else "info", "STE-5.2",
                     "%d instructions in one sentence" % count,
                     "Give each instruction its own sentence (simultaneous actions are "
                     "the exception).", sent=s)
        # Rule 5.4: condition after the command.
        if s.main is not None and toks[s.main].sent_initial and \
                toks[s.main].lower not in ("make", "do"):
            for k in range(s.main + 2, len(toks)):
                t = toks[k]
                if t.type != "word" or t.lower not in ("when", "if", "unless", "once"):
                    continue
                prev = toks[k - 1]
                nxt = toks[k + 1] if k + 1 < len(toks) else None
                if nxt is not None and nxt.type == "word" and nxt.lower in (
                        "necessary", "applicable", "required", "needed", "possible", "any"):
                    break
                if prev.type == "word" and prev.lower in ("sure", "that", "whether"):
                    break
                self.add(b, t.start, "info", "STE-5.4",
                         "condition after the command ('%s ...')" % t.text,
                         "Put the condition first, then a comma, then the command.", sent=s)
                break

    def rule_series(self, s):
        commas = 0
        depth = 0
        for t in s.tokens:
            if t.type == "punct" and t.text in "([":
                depth += 1
            elif t.type == "punct" and t.text in ")]":
                depth -= 1
            elif depth == 0 and t.type == "punct" and t.text == ",":
                commas += 1
        if commas >= 3 and s.words >= 15 and s.block.kind != "list_item" and \
                re.search(r"\s(?:and|or)\s", s.block.masked[s.start:s.end]):
            self.add(s.block, s.start, "info", "STE-4.3",
                     "series of items in one sentence (%d commas)" % commas,
                     "Put the items in a vertical list.", sent=s)

    def check_block(self, b):
        if b.kind == "paragraph" and not b.label and len(b.sentences) > 6:
            self.add(b, b.sentences[0].start, "warn", "STE-6.6",
                     "paragraph has %d sentences (maximum 6)" % len(b.sentences),
                     "Divide the paragraph.")
        if b.label in ("DANGER", "NOTICE", "ATTENTION"):
            self.add(b, 0, "info", "STE-7.1",
                     "signal word '%s'" % b.label,
                     "Use WARNING (persons can get hurt) or CAUTION (equipment can "
                     "break), unless your industry standard specifies this word.")
        if b.label in SAFETY_LABELS and b.sentences:
            s0 = b.sentences[0]
            words = [t for t in s0.tokens if t.type == "word"]
            first = words[0].lower if words else ""
            ok = s0.imperative or first in ("if", "when", "while", "before", "after",
                                            "during", "until", "unless", "always", "never",
                                            "do", "don't", "don’t")
            if not ok:
                self.add(b, s0.start, "warn", "STE-7.2",
                         "safety instruction does not start with a command or a condition",
                         "Start with the command (for example 'Do not ...') or with the "
                         "condition ('When you ...').", sent=s0)
            rest = " ".join(s.text() for s in b.sentences[1:])
            if len(b.sentences) == 1 or not RESULT_RE.search(rest):
                if not RESULT_RE.search(" ".join(s.text() for s in b.sentences)) or \
                        len(b.sentences) == 1:
                    self.add(b, s0.start, "info", "STE-7.3",
                             "safety instruction does not explain the risk",
                             "Add a sentence that tells the possible result, for example "
                             "'... can cause injury.'", sent=s0)

    def check_lists(self):
        groups = OrderedDict()
        lead_of = {}
        last = None
        for b in self.blocks:
            if b.kind == "list_item":
                if b.list_id not in groups:
                    groups[b.list_id] = []
                    lead_of[b.list_id] = last
                groups[b.list_id].append(b)
            if not (b.kind == "paragraph" and b.in_list) and b.kind != "list_item":
                last = b
            elif b.kind == "list_item":
                last = None
        for lid, items in groups.items():
            lead = lead_of.get(lid)
            if lead is not None and lead.kind == "paragraph" and not lead.label and \
                    lead.sentences and len(items) >= 2 and \
                    items[0].segs and lead.segs[-1][0] >= items[0].segs[0][0] - 2:
                txt = lead.masked.rstrip()
                if txt and not txt.endswith(":"):
                    self.add(lead, len(lead.text.rstrip()) - 1, "info", "STE-4.3",
                             "text before a vertical list does not end with a colon",
                             "End the introductory sentence with ':'.")
            nested = False
            for b in items:
                if not b.segs:
                    continue
                if b.masked.rstrip().endswith(","):
                    self.add(b, len(b.text.rstrip()) - 1, "warn", "STE-4.3",
                             "list item ends with a comma",
                             "End a list item without a comma or semicolon.")
                first = next((t for t in b.tokens if t.type != "punct"), None)
                if first is not None and first.type == "word" and first.text[:1].islower():
                    self.add(b, first.start, "info", "STE-4.3",
                             "list item starts with a lowercase letter",
                             "Start each list item with an uppercase letter.")
                if b.level > 0 and not nested:
                    nested = True
                    self.add(b, 0, "info", "STE-4.3", "nested vertical list",
                             "Keep all items at the same level where possible.")
            real = [b for b in items if b.segs and b.sentences]
            if len(real) >= 2 and all(self._has_verb(b) for b in real):
                end = real[-1].masked.rstrip()
                if end and end[-1] not in ".!?:,;":
                    self.add(real[-1], len(real[-1].text.rstrip()) - 1, "info", "STE-4.3",
                             "last item of a vertical list of sentences has no period",
                             "End each list item that is a sentence with a period.")

    def _has_verb(self, b):
        """True if a list item is a sentence: a command, or a finite verb."""
        for s in b.sentences:
            if s.imperative:
                return True
            for k, t in enumerate(s.tokens):
                if t.type != "word":
                    continue
                if t.lower in BE_FORMS or t.lower in HAVE_FORMS or \
                        (t.lower in MODALS and t.lower not in ("do", "does", "did")):
                    return True
                if k > 0 and t.lower.endswith(("s", "ed")) and self.lex is not None and \
                        s.tokens[k - 1].lower not in DETERMINERS and \
                        any(r["pos"] == "v" and r["word"] != t.lower and r.get("approved")
                            for r in self.lex.lookup(t.lower)):
                    return True
        return False


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def flavor_for(path):
    return PROSE_EXT.get(os.path.splitext(path)[1].lower(), "md")


def iter_files(paths, errors):
    """Yield (path, flavor) for each prose file. Explicit code files are skipped."""
    for p in paths:
        if p == "-":
            yield p, "md"
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
                for f in sorted(files):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in PROSE_EXT and not f.startswith("."):
                        yield os.path.join(root, f), PROSE_EXT[ext]
        elif os.path.isfile(p):
            if os.path.splitext(p)[1].lower() in CODE_EXT:
                errors.append("%s: skipped (code or data file)" % p)
                continue
            yield p, flavor_for(p)
        else:
            errors.append("%s: no such file or directory" % p)


def find_default_dictionary():
    env = os.environ.get("STE100_DICTIONARY")
    if env:
        return env
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base in (skill_dir, os.getcwd()):
        cand = os.path.join(base, DEFAULT_DICT_REL)
        if os.path.isfile(cand):
            return cand
    return os.path.join(skill_dir, DEFAULT_DICT_REL)


def find_default_terms(paths):
    seen = set()
    starts = [os.getcwd()]
    for p in paths:
        if p != "-":
            ap = os.path.abspath(p)
            starts.insert(0, ap if os.path.isdir(ap) else os.path.dirname(ap))
    for d in starts:
        while d and d not in seen:
            seen.add(d)
            cand = os.path.join(d, "DOCS_TERMS.md")
            if os.path.isfile(cand):
                return cand
            if os.path.isdir(os.path.join(d, ".git")):
                break
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    return None


def group_findings(findings):
    """Group repeated vocabulary findings across all files of the run.

    STE-1.6 findings are grouped by the word (singular form) alone; the other
    groupable rules by word and message.
    """
    out = []
    groups = {}
    for f in findings:
        if f.rule in GROUPABLE and f.key:
            gk = (f.rule, f.key) if f.rule == "STE-1.6" else (f.rule, f.key,
                                                               f.message.lower())
            if gk in groups:
                groups[gk].locations.append((f.file, f.line, f.col))
                continue
            groups[gk] = f
        out.append(f)
    return out


# One vocabulary finding per token: the most specific rule wins.
VOCAB_PRIORITY = {"STE-1.11": 0, "STE-1.1": 1, "STE-1.2": 2, "STE-1.4": 3, "STE-1.7": 4,
                  "STE-1.13": 4, "STE-1.6": 5}


def one_vocabulary_finding_per_token(findings):
    best = {}
    for f in findings:
        if f.rule in VOCAB_PRIORITY:
            k = (f.file, f.line, f.col)
            best[k] = min(best.get(k, 99), VOCAB_PRIORITY[f.rule])
    return [f for f in findings if f.rule not in VOCAB_PRIORITY or
            VOCAB_PRIORITY[f.rule] == best[(f.file, f.line, f.col)]]


def unknown_words(findings):
    """Candidate entries for the term list from STE-1.6 findings.

    Return a list of dicts (word, count, tag, files), most frequent first.
    The tag is a guess: TV if most uses look like verbs, else TN.
    """
    rows = OrderedDict()
    for f in findings:
        if f.rule != "STE-1.6" or not f.key:
            continue
        r = rows.setdefault(f.key, {"word": f.key, "count": 0, "tn": 0, "tv": 0,
                                    "files": []})
        n = len(f.locations)
        r["count"] += n
        r["tv" if f.hint == "TV" else "tn"] += n
        for loc in f.locations:
            if loc[0] not in r["files"]:
                r["files"].append(loc[0])
    out = []
    for r in rows.values():
        out.append(OrderedDict([("word", r["word"]), ("count", r["count"]),
                                ("tag", "TV" if r["tv"] > r["tn"] else "TN"),
                                ("files", r["files"])]))
    out.sort(key=lambda r: (-r["count"], r["word"]))
    return out


def check_text(text, flavor="md", path="<text>", lexicon=None, terms=None, profile="auto"):
    """Check a string. Return the list of Finding objects (not grouped)."""
    return DocChecker(path, text, flavor, Context(lexicon, terms, profile)).run()


TERMS_BASENAME = "DOCS_TERMS.md"


def is_term_list_file(path, terms_path=None):
    """True for the term list itself: it is a glossary, not prose to check."""
    if path == "-":
        return False
    if os.path.basename(path).lower() == TERMS_BASENAME.lower():
        return True
    return bool(terms_path) and os.path.realpath(path) == os.path.realpath(terms_path)


def run(paths, lexicon, terms, profile, min_sev, dict_path, dict_error=None, terms_path=None,
        skipped=None):
    errors = []
    findings = []
    files = []
    if terms_path is None and terms is not None:
        terms_path = terms.path
    for path, flavor in iter_files(paths, errors):
        if is_term_list_file(path, terms_path):
            if skipped is not None:
                skipped.append(path)
            continue
        try:
            if path == "-":
                text = sys.stdin.read()
            else:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
        except OSError as exc:
            errors.append("%s: %s" % (path, exc))
            continue
        files.append(path)
        findings.extend(check_text(text, flavor, path, lexicon, terms, profile))
    findings.sort(key=lambda f: (f.file, f.line, f.col, f.rule))
    if lexicon is None:
        why = dict_error or "no dictionary cache at %s" % dict_path
        findings.insert(0, Finding(dict_path, 0, 0, "info", "STE-X-NODICT",
                                   "vocabulary checks skipped (%s) — run "
                                   "tools/build_dictionary.py" % why))
    findings = [f for f in findings if SEV_RANK[f.severity] >= SEV_RANK[min_sev]]
    return files, group_findings(findings), errors


def format_text(f):
    out = "%s:%d:%d %s %s %s" % (f.file, f.line, f.col, f.severity.upper(), f.rule, f.message)
    if len(f.locations) > 1:
        more = ["%s:%d:%d" % loc for loc in f.locations[1:MAX_LOCATIONS]]
        extra = len(f.locations) - MAX_LOCATIONS
        out += " [%d occurrences; also at %s%s]" % (
            len(f.locations), ", ".join(more), (", +%d more" % extra) if extra > 0 else "")
    if f.suggestion:
        out += "\n    suggestion: %s" % f.suggestion
    return out


def list_rules_text():
    rows = [("ID", "TITLE", "JUDGMENT", "DICTIONARY", "CHECKED")]
    for r in RULES.values():
        rows.append((r["id"], r["title"], r["judgment"], "yes" if r["needs_dictionary"] else "no",
                     "yes" if r["checked"] else "no"))
    widths = [max(len(row[i]) for row in rows) for i in range(5)]
    lines = []
    for n, row in enumerate(rows):
        lines.append("  ".join(c.ljust(widths[i]) for i, c in enumerate(row)).rstrip())
        if n == 0:
            lines.append("  ".join("-" * w for w in widths))
    lines.append("")
    lines.append("Rules 8.4 to 8.7 (word count) are applied inside STE-5.1 and STE-6.3.")
    lines.append("The script does not check 'editorial' rules. They need a human reviewer.")
    return "\n".join(lines)


def build_parser():
    p = argparse.ArgumentParser(
        prog="ste_check.py",
        description="Check prose files against the ASD-STE100 Simplified Technical English "
                    "writing rules. This is a heuristic aid, not a certified checker.",
        epilog="Output: file:line:col SEVERITY RULE message. Exit status: 0 if there are no "
               "WARN findings, 1 if there are WARN findings, 2 for a usage error.")
    p.add_argument("paths", nargs="*", metavar="PATH",
                   help="file or directory to check (.md, .txt, .rst, .adoc); '-' reads "
                        "standard input as Markdown")
    p.add_argument("--dictionary", metavar="FILE",
                   help="dictionary cache from tools/build_dictionary.py (default: "
                        "$STE100_DICTIONARY, or .cache/ste100-dictionary.json in the skill "
                        "directory or the current directory)")
    p.add_argument("--terms", metavar="FILE",
                   help="project term list (default: the nearest DOCS_TERMS.md): one term per "
                        "line with an optional (TN) or (TV) tag, or Markdown tables with "
                        "the columns 'Technical noun' or 'Technical verb' (or 'Term'), "
                        "'Definition', and 'Do not use'. The term list file itself and any "
                        "DOCS_TERMS.md are never checked as prose")
    p.add_argument("--json", action="store_true",
                   help="write JSON with the keys meta, summary, findings")
    p.add_argument("--min-severity", choices=SEVERITIES, default="info",
                   help="do not report findings below this severity (default: info)")
    p.add_argument("--profile", choices=("auto", "procedure", "description"), default="auto",
                   help="sentence-length profile: procedure (20 words), description (25 "
                        "words), or auto (decide for each sentence; default)")
    p.add_argument("--unknown-words", action="store_true",
                   help="print only the words that the dictionary and the term list do not "
                        "have (STE-1.6), one line each with the count and a TN or TV guess, "
                        "as candidates for DOCS_TERMS.md; with --json, write a list")
    p.add_argument("--list-rules", action="store_true",
                   help="list the rule IDs and what the script checks, then stop")
    p.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    return p


# Output encoding. On Windows a redirected or piped stdout uses the ANSI code page
# (often cp1252). When stdout is not UTF-8, JSON is written ASCII-only (\uXXXX
# escapes: valid and lossless) and text output uses backslashreplace, so printing
# never raises UnicodeEncodeError.
_JSON_ASCII = False


def _is_utf8(stream):
    enc = (getattr(stream, "encoding", None) or "").lower().replace("-", "").replace("_", "")
    return enc in ("utf8", "utf8sig")


def _safe_stdio():
    global _JSON_ASCII
    _JSON_ASCII = not _is_utf8(sys.stdout)
    for stream in (sys.stdout, sys.stderr):
        if not _is_utf8(stream) and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="backslashreplace")
            except (ValueError, OSError):
                pass


def main(argv=None):
    _safe_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_rules:
        if args.json:
            print(json.dumps(list(RULES.values()), indent=2))
        else:
            print(list_rules_text())
        return 0
    if not args.paths:
        parser.print_usage(sys.stderr)
        print("ste_check.py: error: give one or more files or directories", file=sys.stderr)
        return 2
    dict_path = args.dictionary or find_default_dictionary()
    lexicon = None
    dict_error = None
    if os.path.isfile(dict_path):
        try:
            lexicon = Lexicon.load(dict_path)
        except (DictionaryError, OSError) as exc:
            if args.dictionary:
                print("ste_check.py: error: %s" % exc, file=sys.stderr)
                return 2
            dict_error = str(exc)
    elif args.dictionary:
        print("ste_check.py: error: dictionary not found: %s" % dict_path, file=sys.stderr)
        return 2
    terms_path = args.terms or find_default_terms(args.paths)
    terms = TermList()
    if terms_path:
        if not os.path.isfile(terms_path):
            print("ste_check.py: error: term list not found: %s" % terms_path, file=sys.stderr)
            return 2
        terms = TermList.load(terms_path)
    skipped = []
    files, findings, errors = run(args.paths, lexicon, terms, args.profile,
                                  "info" if args.unknown_words else args.min_severity,
                                  dict_path, dict_error, terms_path, skipped)
    for e in errors:
        print("ste_check.py: %s" % e, file=sys.stderr)
    for sk in skipped:
        print("ste_check.py: note: %s: not checked (term list, not prose)" % sk,
              file=sys.stderr)
    if args.unknown_words:
        rows = unknown_words(findings)
        if lexicon is None:
            print("ste_check.py: note: no dictionary cache; the list is empty. Run "
                  "tools/build_dictionary.py", file=sys.stderr)
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=_JSON_ASCII))
        else:
            print("# Candidates for DOCS_TERMS.md (word, count, TN/TV guess). "
                  "Review each one.")
            for r in rows:
                print("%s (%s)  # %d use(s)" % (r["word"], r["tag"], r["count"]))
        return 2 if errors and not files else 0
    n_warn = sum(len(f.locations) for f in findings if f.severity == "warn")
    n_info = sum(len(f.locations) for f in findings if f.severity == "info")
    if args.json:
        by_rule = OrderedDict()
        for f in findings:
            by_rule[f.rule] = by_rule.get(f.rule, 0) + len(f.locations)
        meta = OrderedDict([
            ("tool", "ste_check.py"), ("version", VERSION),
            ("dictionary", OrderedDict([
                ("path", dict_path), ("loaded", lexicon is not None),
                ("source", lexicon.meta.get("source") if lexicon else None),
                ("issue_date", lexicon.meta.get("issue_date") if lexicon else None),
                ("counts", lexicon.meta.get("counts") if lexicon else None)])),
            ("terms", OrderedDict([("path", terms_path), ("count", len(terms))])),
            ("profile", args.profile), ("min_severity", args.min_severity),
            ("files", files), ("skipped", skipped), ("errors", errors),
        ])
        groups_by_rule = OrderedDict()
        for f in findings:
            groups_by_rule[f.rule] = groups_by_rule.get(f.rule, 0) + 1
        summary = OrderedDict([
            ("files", len(files)), ("findings", n_warn + n_info), ("groups", len(findings)),
            ("by_severity", OrderedDict([("warn", n_warn), ("info", n_info)])),
            ("by_rule", by_rule), ("groups_by_rule", groups_by_rule),
        ])
        print(json.dumps(OrderedDict([("meta", meta), ("summary", summary),
                                      ("findings", [f.as_dict() for f in findings])]),
                         indent=2, ensure_ascii=_JSON_ASCII))
    else:
        if lexicon is None:
            print("ste_check.py: note: vocabulary checks skipped; run "
                  "tools/build_dictionary.py", file=sys.stderr)
        for f in findings:
            print(format_text(f))
        print("%d finding(s): %d warn, %d info in %d file(s)" % (
            n_warn + n_info, n_warn, n_info, len(files)))
    if errors and not files:
        return 2
    return 1 if n_warn else 0


if __name__ == "__main__":
    sys.exit(main())
