Python's standard library has no ISO 8601 duration parser. `datetime.fromisoformat` only handles dates and times, not durations. You can use a small library or write a short regex.

**Option 1: `isodate` (the simplest if you can add a dependency)**

```python
import isodate

isodate.parse_duration("P3DT4H")   # datetime.timedelta(days=3, seconds=14400)
```

If the string contains years or months (e.g. `P1Y2M`), it returns an `isodate.Duration` instead of a `timedelta`. That's because a month has no fixed length.

**Option 2: no dependencies, using a regex**

```python
import re
from datetime import timedelta

_DURATION_RE = re.compile(
    r"P(?!$)"
    r"(?:(?P<weeks>\d+(?:\.\d+)?)W)?"
    r"(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?=\d)"
    r"(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?"
    r")?$"
)

def parse_duration(s: str) -> timedelta:
    m = _DURATION_RE.fullmatch(s)
    if not m:
        raise ValueError(f"Invalid or unsupported ISO 8601 duration: {s!r}")
    return timedelta(**{k: float(v) for k, v in m.groupdict().items() if v})

parse_duration("P3DT4H")      # timedelta(days=3, seconds=14400)
parse_duration("PT1M30.5S")   # timedelta(seconds=90, microseconds=500000)
parse_duration("P2W")         # timedelta(days=14)
```

How the regex works:
- `(?!$)` after `P` rejects a bare `P`.
- `(?=\d)` after `T` rejects a trailing `T` with nothing after it, as in `P1DT`.
- `groupdict()` names match `timedelta`'s keyword arguments, so the matches pass straight through.
- It deliberately rejects `Y` and `M` in the date part (years and months). Those can't become a `timedelta` without a reference date, so failing loudly is better than guessing "30 days".
- It doesn't handle a negative sign (`-P1D`, a common extension) or a comma as the decimal separator. Add them if your inputs use them.

**Recommendation:** If your inputs only use days, hours, minutes and seconds (as in `P3DT4H`), the regex version is clean and needs nothing extra. If you need to handle arbitrary ISO 8601 input, including years and months, use `isodate`.
