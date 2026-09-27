Use **`http.TimeFormat`** from `net/http`, not a `time` package constant:

```go
import (
    "net/http"
    "time"
)

w.Header().Set("Last-Modified", modTime.UTC().Format(http.TimeFormat))
// e.g. "Fri, 25 Sep 2026 14:03:07 GMT"
```

`http.TimeFormat` is `"Mon, 02 Jan 2006 15:04:05 GMT"`. It matches the IMF-fixdate format that RFC 9110 requires.

- **Call `.UTC()` first.** The layout writes the literal text `GMT` and doesn't convert the time. If you pass a local time, you get the local clock reading labeled as GMT, which is wrong.
- **Don't use `time.RFC1123`.** Its `MST` placeholder prints the zone abbreviation, so a UTC time comes out as `UTC` instead of `GMT`. HTTP requires `GMT`. `time.RFC1123Z` is also wrong because it writes a numeric offset like `+0000`.
- **Parsing:** use `http.ParseTime(s)` to read `If-Modified-Since` and similar headers. It also accepts the older RFC 850 and asctime formats.
- **Serving files:** if you use `http.ServeContent` or `http.FileServer`, they set `Last-Modified` and handle conditional requests for you.
