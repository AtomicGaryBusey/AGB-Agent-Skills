Use **`http.TimeFormat`** from `net/http`, and convert the time to UTC first:

```go
import (
	"net/http"
	"time"
)

w.Header().Set("Last-Modified", modTime.UTC().Format(http.TimeFormat))
// e.g. "Fri, 25 Sep 2026 14:03:07 GMT"
```

- `http.TimeFormat` is `"Mon, 02 Jan 2006 15:04:05 GMT"`. This is the IMF-fixdate form that RFC 9110 §5.6.7 requires.
- **Call `.UTC()` before formatting.** The `GMT` in the layout is literal text, not a timezone directive. If you format a local time, Go prints the local clock time with "GMT" after it, so the header is wrong.
- **Don't use `time.RFC1123`.** It formats the zone from the time value, so you can get `EST` or similar. It also gives `UTC` instead of `GMT` for UTC times, which the HTTP spec doesn't allow. `time.RFC1123Z` uses a numeric offset, which isn't allowed either.

Related:
- To parse incoming dates such as `If-Modified-Since`, use `http.ParseTime`. It accepts IMF-fixdate plus the obsolete RFC 850 and asctime formats, as the spec requires.
- If you serve content with `http.ServeContent`, pass it the `modtime`. It sets `Last-Modified` and handles conditional requests for you.
