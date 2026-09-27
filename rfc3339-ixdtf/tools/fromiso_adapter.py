import sys, json, datetime
s = sys.stdin.read()
try: datetime.datetime.fromisoformat(s); print(json.dumps({"ok": True}))
except Exception as e: print(json.dumps({"ok": False, "error": str(e)}))
