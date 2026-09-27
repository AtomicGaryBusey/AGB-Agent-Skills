// RFC 3339 / RFC 9557 conformance probe for java.time (JDK 25).
// Usage: TZ=America/New_York java -Dprobe.dir=probes probes/Probe.java [probe] > results/java.jsonl
//        java probes/Probe.java list            (adapter keys: <key>\t<target-kind>)
//        java probes/Probe.java adapter <key>   (scripts/run_vectors.py adapter; per-process + batch)
// Reads probes/inputs.json schema 2 (inputs + legacy) or the old list form: the hand
// parser below picks every {"id": ..., "s": ...} pair, which covers both.
import java.nio.file.*;
import java.text.SimpleDateFormat;
import java.time.*;
import java.time.format.*;
import java.time.temporal.*;
import java.util.*;
import java.util.function.Function;
import java.util.regex.*;

public class Probe {
    record In(String id, String s) {}
    static List<In> INPUTS = new ArrayList<>();

    static String unesc(String s) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\\') {
                char n = s.charAt(++i);
                switch (n) {
                    case 'n' -> b.append('\n');
                    case 'r' -> b.append('\r');
                    case 't' -> b.append('\t');
                    case 'b' -> b.append('\b');
                    case 'f' -> b.append('\f');
                    case 'u' -> { b.append((char) Integer.parseInt(s.substring(i + 1, i + 5), 16)); i += 4; }
                    default -> b.append(n);
                }
            } else b.append(c);
        }
        return b.toString();
    }
    static String j(String s) {
        if (s == null) return "null";
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
    static void emit(String kind, String api, String mode, In in, boolean ok, String out, String utc, String err) {
        System.out.println("{\"lang\":\"java\",\"kind\":" + j(kind) + ",\"api\":" + j(api) + ",\"mode\":" + j(mode)
            + (in != null ? ",\"id\":" + j(in.id) + ",\"input\":" + j(in.s) : "")
            + ",\"ok\":" + ok + ",\"out\":" + j(out) + ",\"utc\":" + j(utc) + ",\"err\":" + j(err) + "}");
    }
    static String utc(Instant i) {
        return DateTimeFormatter.ISO_INSTANT.format(i);
    }
    interface P { Object apply(String s) throws Exception; }
    record Api(String key, String name, String mode, String kind, P fn) {}
    static final DateTimeFormatter P1 = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX");
    static final DateTimeFormatter P2 = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss[.SSSSSSSSS]XXX").withResolverStyle(ResolverStyle.STRICT);
    static final DateTimeFormatter P3 = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'");
    static final List<Api> APIS = List.of(
        new Api("offsetdatetime", "OffsetDateTime.parse (ISO_OFFSET_DATE_TIME)", "3339", "rfc3339", OffsetDateTime::parse),
        new Api("zoneddatetime", "ZonedDateTime.parse (ISO_ZONED_DATE_TIME)", "ixdtf", "ixdtf", ZonedDateTime::parse),
        new Api("instant", "Instant.parse (ISO_INSTANT)", "3339", "rfc3339", Instant::parse),
        new Api("iso-date-time", "DateTimeFormatter.ISO_DATE_TIME -> Instant.from", "ixdtf", "ixdtf",
            s -> { var t = DateTimeFormatter.ISO_DATE_TIME.parse(s); Instant.from(t); return t; }),
        new Api("pattern-smart", "ofPattern(\"yyyy-MM-dd'T'HH:mm:ssXXX\") [SMART]", "3339", "rfc3339", s -> OffsetDateTime.parse(s, P1)),
        new Api("pattern-strict", "ofPattern(\"uuuu-MM-dd'T'HH:mm:ss[.SSSSSSSSS]XXX\").STRICT", "3339", "rfc3339", s -> OffsetDateTime.parse(s, P2)),
        new Api("pattern-literal-z", "ofPattern(\"yyyy-MM-dd'T'HH:mm:ss'Z'\") -> LocalDateTime", "3339", "rfc3339", s -> LocalDateTime.parse(s, P3)),
        new Api("sdf-lenient", "SimpleDateFormat(\"yyyy-MM-dd'T'HH:mm:ssXXX\") [lenient default]", "3339", "rfc3339", s -> {
            try { return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX").parse(s); }
            catch (java.text.ParseException e) { throw new RuntimeException(e.getMessage()); } }),
        new Api("sdf-strict-pos", "SimpleDateFormat.parse, then check ParsePosition==len", "3339", "rfc3339", s -> {
            var f = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX"); f.setLenient(false); var pp = new java.text.ParsePosition(0);
            var d = f.parse(s, pp); if (d == null || pp.getIndex() != s.length()) throw new RuntimeException("unparsed at " + pp.getIndex() + "/" + pp.getErrorIndex());
            return d; }));

    /** [out, utc] for the legacy probe rows (same values as before the API table). */
    static Object[] outUtc(Object r) {
        if (r instanceof OffsetDateTime o) return new Object[]{o, utc(o.toInstant())};
        if (r instanceof ZonedDateTime z) return new Object[]{z, utc(z.toInstant())};
        if (r instanceof Instant i) return new Object[]{i, utc(i)};
        if (r instanceof LocalDateTime l) return new Object[]{l, "naive:" + l};
        if (r instanceof Date d) return new Object[]{d, utc(d.toInstant())};
        if (r instanceof TemporalAccessor t) return new Object[]{t, utc(Instant.from(t))};
        return new Object[]{r, null};
    }
    static void parse(Api api) {
        for (In in : INPUTS) {
            try {
                Object[] r = outUtc(api.fn.apply(in.s));
                emit("parse", api.name, api.mode, in, true, String.valueOf(r[0]), (String) r[1], null);
            } catch (Exception e) {
                String m = e.getClass().getSimpleName() + ": " + e.getMessage();
                emit("parse", api.name, api.mode, in, false, null, null, m.length() > 160 ? m.substring(0, 160) : m);
            }
        }
    }

    // ---------------- run_vectors.py adapter ----------------
    static String localFields(LocalDateTime l, Integer offSec) {
        StringBuilder b = new StringBuilder("{\"year\":" + l.getYear() + ",\"month\":" + l.getMonthValue()
            + ",\"day\":" + l.getDayOfMonth() + ",\"hour\":" + l.getHour() + ",\"minute\":" + l.getMinute()
            + ",\"second\":" + l.getSecond() + ",\"leap_second\":false");
        if (l.getNano() != 0) b.append(",\"secfrac\":").append(j(String.format("%09d", l.getNano())));
        if (offSec != null) b.append(",\"offset_minutes\":").append(Math.floorDiv(offSec, 60));
        return b.toString();
    }
    /** Fields the result exposes (null = none: Instant and Date keep no offset). */
    static String fields(Object r) {
        if (r instanceof OffsetDateTime o) return localFields(o.toLocalDateTime(), o.getOffset().getTotalSeconds()) + "}";
        if (r instanceof ZonedDateTime z) return localFields(z.toLocalDateTime(), z.getOffset().getTotalSeconds())
            + (z.getZone() instanceof ZoneOffset ? "" : ",\"time_zone\":{\"name\":" + j(z.getZone().getId()) + "}") + "}";
        if (r instanceof LocalDateTime l) return localFields(l, null) + "}";
        if (r instanceof TemporalAccessor t && !(r instanceof Instant)) {
            LocalDateTime l = LocalDateTime.from(t);
            Integer off = t.isSupported(ChronoField.OFFSET_SECONDS) ? t.get(ChronoField.OFFSET_SECONDS) : null;
            ZoneId zid = t.query(TemporalQueries.zoneId());
            return localFields(l, off) + (zid == null || zid instanceof ZoneOffset ? "" : ",\"time_zone\":{\"name\":" + j(zid.getId()) + "}") + "}";
        }
        return null;
    }
    static String answer(Api api, String s) {
        try {
            Object r = api.fn.apply(s);
            String f = null;
            try { f = fields(r); } catch (Exception e) { /* no fields */ }
            return "\"ok\":true" + (f != null ? ",\"fields\":" + f : "") + ",\"utc\":" + j((String) outUtc(r)[1]);
        } catch (Exception e) {
            String m = e.getClass().getSimpleName() + ": " + e.getMessage();
            return "\"ok\":false,\"error\":" + j(m.length() > 200 ? m.substring(0, 200) : m);
        }
    }
    /** The JSON string value after the first "key": at or after from (a regex overflows the stack on
     *  the 5000-bracket vectors).  Returns {raw value, end index} or null. */
    static String[] strAfter(String src, String key, int from) {
        int k = src.indexOf("\"" + key + "\":", from);
        if (k < 0) return null;
        int i = k + key.length() + 3;
        while (i < src.length() && Character.isWhitespace(src.charAt(i))) i++;
        if (i >= src.length() || src.charAt(i) != '"') return null;
        int st = ++i;
        while (i < src.length() && src.charAt(i) != '"') i += src.charAt(i) == '\\' ? 2 : 1;
        return new String[]{src.substring(st, i), String.valueOf(i + 1)};
    }
    static int adapter(String key) throws Exception {
        Api api = APIS.stream().filter(x -> x.key.equals(key)).findFirst().orElse(null);
        if (api == null) { System.err.println("unknown adapter key " + key + "; see: Probe list"); return 2; }
        var out = new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), false, "UTF-8");
        String all = new String(System.in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        if ("1".equals(System.getenv("RFCDT_BATCH"))) {
            for (String line : all.split("\n")) {
                if (line.isBlank()) continue;
                String[] id = strAfter(line, "id", 0), in = id == null ? null : strAfter(line, "input", Integer.parseInt(id[1]));
                if (in == null) { out.println("{\"ok\":false,\"error\":\"bad request line\"}"); continue; }
                out.println("{\"id\":" + j(unesc(id[0])) + "," + answer(api, unesc(in[0])) + "}");
            }
        } else out.println("{" + answer(api, all) + "}");
        out.flush();
        return 0;
    }

    static void fmt(String api, java.util.concurrent.Callable<String> c) {
        try { emit("format", api, null, null, true, c.call(), null, null); }
        catch (Exception e) { emit("format", api, null, null, false, null, null, e.toString()); }
    }

    public static void main(String[] a) throws Exception {
        if (a.length > 0 && a[0].equals("list")) { for (Api x : APIS) System.out.println(x.key + "\t" + x.kind); return; }
        if (a.length > 0 && a[0].equals("adapter")) System.exit(adapter(a.length > 1 ? a[1] : ""));
        if (a.length > 0 && !a[0].equals("probe")) { System.err.println("usage: Probe [probe] | list | adapter <key>"); System.exit(2); }
        String here = Path.of(System.getProperty("probe.dir", ".")).toString();
        String json = Files.readString(Path.of(here, "inputs.json"));
        // every {"id": ..., "s": ...} pair (schema 2 inputs + legacy, or the old list)
        for (String[] id = strAfter(json, "id", 0); id != null; id = strAfter(json, "id", Integer.parseInt(id[1]))) {
            int e = Integer.parseInt(id[1]);
            String rest = json.substring(e, Math.min(json.length(), e + 16)).replaceAll("\\s", "");
            if (!rest.startsWith(",\"s\":")) continue;
            String[] v = strAfter(json, "s", e);
            INPUTS.add(new In(unesc(id[0]), unesc(v[0])));
        }

        for (Api x : APIS) parse(x);

        var paris = ZoneId.of("Europe/Paris");
        fmt("OffsetDateTime.toString() [:00 seconds]", () -> OffsetDateTime.of(2026, 9, 24, 12, 0, 0, 0, ZoneOffset.UTC).toString());
        fmt("OffsetDateTime.toString() [120ms]", () -> OffsetDateTime.of(2026, 9, 24, 12, 0, 5, 120_000_000, ZoneOffset.UTC).toString());
        fmt("ZonedDateTime.toString() [Europe/Paris, :00 seconds]", () -> ZonedDateTime.of(2026, 9, 24, 14, 0, 0, 0, paris).toString());
        fmt("ZonedDateTime.toString() [ZoneId.of(\"UTC\")]", () -> ZonedDateTime.of(2026, 9, 24, 12, 0, 0, 0, ZoneId.of("UTC")).toString());
        fmt("ZonedDateTime.toString() [ZoneOffset.UTC]", () -> ZonedDateTime.of(2026, 9, 24, 12, 0, 0, 0, ZoneOffset.UTC).toString());
        fmt("ZonedDateTime.toString() [1850 Europe/Paris, LMT]", () -> ZonedDateTime.of(1850, 1, 1, 0, 0, 0, 0, paris).toString());
        fmt("ISO_OFFSET_DATE_TIME.format(1850 Paris LMT)", () -> DateTimeFormatter.ISO_OFFSET_DATE_TIME.format(ZonedDateTime.of(1850, 1, 1, 0, 0, 0, 0, paris)));
        fmt("ISO_ZONED_DATE_TIME.format(ZDT Paris)", () -> DateTimeFormatter.ISO_ZONED_DATE_TIME.format(ZonedDateTime.of(2026, 9, 24, 14, 0, 0, 0, paris)));
        fmt("ISO_OFFSET_DATE_TIME.format(ODT UTC)", () -> DateTimeFormatter.ISO_OFFSET_DATE_TIME.format(OffsetDateTime.of(2026, 9, 24, 12, 0, 0, 0, ZoneOffset.UTC)));
        fmt("ISO_DATE_TIME.format(LocalDateTime) [no offset]", () -> DateTimeFormatter.ISO_DATE_TIME.format(LocalDateTime.of(2026, 9, 24, 12, 0)));
        fmt("Instant.toString()", () -> Instant.parse("2026-09-24T12:00:00Z").toString());
        fmt("Instant.toString() [year 10000]", () -> Instant.parse("+10000-01-01T00:00:00Z").toString());
        fmt("Instant.toString() [year -1]", () -> OffsetDateTime.of(-1, 1, 1, 0, 0, 0, 0, ZoneOffset.UTC).toInstant().toString());
        fmt("java.util.Date.toString()", () -> Date.from(Instant.parse("2026-09-24T12:00:00Z")).toString());
        fmt("SimpleDateFormat(\"yyyy-MM-dd'T'HH:mm:ssZ\")", () -> { var f = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ"); f.setTimeZone(TimeZone.getTimeZone("UTC")); return f.format(Date.from(Instant.parse("2026-09-24T12:00:00Z"))); });
        fmt("SimpleDateFormat(\"yyyy-MM-dd'T'HH:mm:ss'Z'\") [default TZ!]", () -> new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'").format(Date.from(Instant.parse("2026-09-24T12:00:00Z"))));
        fmt("SimpleDateFormat(\"YYYY-MM-dd'T'HH:mm:ssXXX\") [week-year YYYY, 2026-12-28]", () -> { var f = new SimpleDateFormat("YYYY-MM-dd'T'HH:mm:ssXXX"); f.setTimeZone(TimeZone.getTimeZone("UTC")); return f.format(Date.from(Instant.parse("2026-12-28T12:00:00Z"))); });
        fmt("ofPattern(\"YYYY-MM-dd'T'HH:mm:ssXXX\") [week-based-year, 2026-12-28]", () -> DateTimeFormatter.ofPattern("YYYY-MM-dd'T'HH:mm:ssXXX").format(OffsetDateTime.of(2026, 12, 28, 12, 0, 0, 0, ZoneOffset.UTC)));
    }
}
