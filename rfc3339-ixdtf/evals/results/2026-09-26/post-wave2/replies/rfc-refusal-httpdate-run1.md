Use **`http.TimeFormat`** from `net/http`, and convert the time to UTC before formatting:

```go
import (
    "net/http"
    "time"
)

w.Header().Set("Last-Modified", modTime.UTC().Format(http.TimeFormat))
// e.g. "Sat, 26 Sep 2026 14:03:07 GMT"
```

`http.TimeFormat` is `"Mon, 02 Jan 2006 15:04:05 GMT"`. This is the IMF-fixdate form that RFC 9110 §5.6.7 requires.

- **You must call `.UTC()` yourself.** "GMT" is literal text in the layout, so Go doesn't convert the time. If you pass a local time, you'll get local clock values labelled GMT, which is wrong.
- **Don't use `time.RFC1123`.** It prints the zone abbreviation, so a UTC time comes out as `UTC` instead of the required `GMT`. `time.RFC1123Z` is also wrong because it uses a numeric offset (`+0000`).
- **Parsing:** to read incoming headers like `If-Modified-Since`, use `http.ParseTime`. It also accepts the obsolete RFC 850 and asctime formats that clients are still allowed to send.
- **Serving files:** if you use `http.ServeContent`, it sets `Last-Modified` and handles conditional requests for you, so you don't need to set the header manually.
