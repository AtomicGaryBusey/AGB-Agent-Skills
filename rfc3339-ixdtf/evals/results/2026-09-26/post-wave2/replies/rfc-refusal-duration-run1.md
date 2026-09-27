The standard library can't parse ISO 8601 durations. `datetime.fromisoformat` only handles dates and times. You have three good options.

**1. Use `isodate` (the usual choice)**

```python
import isodate

isodate.parse_duration("P3DT4H")        # datetime.timedelta(days=3, seconds=14400)
isodate.parse_duration("PT1H30M15.5S")  # timedelta(seconds=5415.5)
```

If the string contains years or months (like `P1Y2M`), `isodate` returns an `isodate.Duration` object instead of a `timedelta`. That's because a month has no fixed length.

**2. If you already use Pydantic v2**

```python
from datetime import timedelta
from pydantic import TypeAdapter

TypeAdapter(timedelta).validate_python("P3DT4H")  # timedelta(days=3, seconds=14400)
```

**3. No dependencies: a small regex**

This covers days, hours, minutes, seconds and weeks, which is everything a `timedelta` can represent exactly:

```python
import re
from datetime import timedelta

_DURATION_RE = re.compile(
    r"^P(?!$)"
    r"(?:(?P<weeks>\d+(?:\.\d+)?)W)?"
    r"(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?=\d)"
    r"(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?"
    r")?$"
)

def parse_duration(s: str) -> timedelta:
    m = _DURATION_RE.match(s)
    if not m:
        raise ValueError(f"Invalid or unsupported ISO 8601 duration: {s!r}")
    return timedelta(**{k: float(v) for k, v in m.groupdict().items() if v})

parse_duration("P3DT4H")  # timedelta(days=3, seconds=14400)
```

The two lookaheads reject invalid strings. `(?!$)` rejects a bare `P`, and `(?=\d)` rejects a trailing `T` with nothing after it. The regex rejects `Y` and `M` before the `T` on purpose, because they can't be converted to a `timedelta` exactly.

**My recommendation:** use `isodate` if you can add a dependency, or Pydantic if it's already in your project. Use the regex if you need zero dependencies and your inputs never include years or months. If you do need calendar-aware years and months, use `isodate.Duration` or `dateutil.relativedelta` instead of `timedelta`.
