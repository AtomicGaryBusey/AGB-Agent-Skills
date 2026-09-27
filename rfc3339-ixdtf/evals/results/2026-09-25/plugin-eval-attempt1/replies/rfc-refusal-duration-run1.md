The Python standard library has no ISO 8601 duration parser. `datetime.fromisoformat` doesn't accept durations. You have two good options.

### 1. Use a library (recommended if you can add a dependency)

```python
import isodate

isodate.parse_duration("P3DT4H")        # datetime.timedelta(days=3, seconds=14400)
isodate.parse_duration("PT1.5S")        # timedelta(seconds=1, microseconds=500000)
isodate.parse_duration("P1Y2M")        # isodate.Duration(...), not a timedelta
```

`isodate` is small and well tested. It returns a plain `timedelta` unless the input contains years or months. In that case it returns its own `Duration` type, because a month has no fixed length. You can add a `Duration` to a date to resolve it.

### 2. Write a small parser with a regex (no dependencies)

```python
import re
from datetime import timedelta

_DURATION_RE = re.compile(
    r"P(?!$)"
    r"(?:(?P<weeks>\d+(?:[.,]\d+)?)W)?"
    r"(?:(?P<days>\d+(?:[.,]\d+)?)D)?"
    r"(?:T(?=\d)"
    r"(?:(?P<hours>\d+(?:[.,]\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:[.,]\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:[.,]\d+)?)S)?"
    r")?",
)

def parse_duration(s: str) -> timedelta:
    m = _DURATION_RE.fullmatch(s)
    if not m:
        raise ValueError(f"Invalid or unsupported ISO 8601 duration: {s!r}")
    parts = {k: float(v.replace(",", ".")) for k, v in m.groupdict().items() if v}
    return timedelta(**parts)
```

```python
parse_duration("P3DT4H")      # timedelta(days=3, seconds=14400)
parse_duration("PT90M")       # timedelta(seconds=5400)
parse_duration("P2W")         # timedelta(days=14)
parse_duration("PT0.5S")      # timedelta(microseconds=500000)
parse_duration("P")           # ValueError
parse_duration("P1DT")        # ValueError (a T must be followed by a time part)
parse_duration("P1Y")         # ValueError (years can't be converted to a timedelta exactly)
```

How the regex works:
- `(?!$)` after `P` rejects a bare `"P"`.
- `(?=\d)` after `T` rejects a `T` with nothing after it, as in `"P1DT"`.
- `fullmatch` rejects trailing junk.
- `timedelta(**parts)` does the unit conversion, so you don't have to multiply by 3600 yourself.
- It accepts both `.` and `,` as the decimal separator, since ISO 8601 allows either.

**Years and months (`Y`, and `M` before the `T`) are deliberately rejected.** "P1M" can be 28 to 31 days depending on the start date, so it can't become a timedelta without a reference date. If you need them, use `isodate` or `dateutil.relativedelta` instead of guessing "30 days".

Choose `isodate` if you're parsing untrusted or varied input. The regex is fine if you control the format and only need days, hours, minutes and seconds.
