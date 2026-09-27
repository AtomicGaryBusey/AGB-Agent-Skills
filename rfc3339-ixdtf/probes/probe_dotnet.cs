#:property PublishAot=false
// RFC 3339 / RFC 9557 conformance probe for .NET 10 (file-based app).
// Usage: TZ=America/New_York dotnet run probe_dotnet.cs -- [probe] <dir-with-inputs.json> > results/dotnet.jsonl
//        dotnet run probe_dotnet.cs -- list            (adapter keys: <key>\t<target-kind>)
//        dotnet run probe_dotnet.cs -- adapter <key>   (scripts/run_vectors.py adapter; per-process + batch)
// Build once for adapters: dotnet build probe_dotnet.cs -c Release -o "$BUILD/dotnet"
//   then: dotnet "$BUILD/dotnet/probe_dotnet.dll" adapter <key>
// Reads inputs.json schema 2 ({"inputs", "legacy"}; tools/gen_probe_inputs.py) or the old list.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Xml;

var inv = CultureInfo.InvariantCulture;
string U(DateTimeOffset d) => d.UtcDateTime.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff", inv);
string UD(DateTime d) => d.Kind switch {
    DateTimeKind.Utc => d.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff", inv),
    DateTimeKind.Local => d.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff", inv),
    _ => "naive:" + d.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff", inv) };
(string, string) OU(object r) => r switch {
    DateTimeOffset d => (d.ToString("o", inv), U(d)),
    DateTime d => (d.ToString("o", inv) + " Kind=" + d.Kind, UD(d)),
    _ => (r.ToString() ?? "", "") };

// key, probe API name, target kind, parse function (returns DateTime or DateTimeOffset)
var apis = new List<(string key, string name, string kind, Func<string, object> fn)> {
    ("datetime-parse", "DateTime.Parse(s, Invariant)", "rfc3339", s => DateTime.Parse(s, inv)),
    ("datetime-parse-roundtrip", "DateTime.Parse(s, Invariant, RoundtripKind)", "rfc3339", s => DateTime.Parse(s, inv, DateTimeStyles.RoundtripKind)),
    ("dto-parse", "DateTimeOffset.Parse(s, Invariant)", "rfc3339", s => DateTimeOffset.Parse(s, inv)),
    ("dto-parseexact-o", "DateTimeOffset.ParseExact(s, \"o\")", "rfc3339", s => DateTimeOffset.ParseExact(s, "o", inv)),
    ("dto-parseexact-ssK", "DateTimeOffset.ParseExact(s, \"yyyy-MM-dd'T'HH:mm:ssK\")", "rfc3339", s => DateTimeOffset.ParseExact(s, "yyyy-MM-dd'T'HH:mm:ssK", inv)),
    ("dto-parseexact-FFFFFFFK", "DateTimeOffset.ParseExact(s, \"yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK\")", "rfc3339", s => DateTimeOffset.ParseExact(s, "yyyy-MM-dd'T'HH:mm:ss.FFFFFFFK", inv)),
    ("stj-dto", "JsonSerializer.Deserialize<DateTimeOffset>", "rfc3339", s => JsonSerializer.Deserialize<DateTimeOffset>(JsonSerializer.Serialize(s))),
    ("stj-datetime", "JsonSerializer.Deserialize<DateTime>", "rfc3339", s => JsonSerializer.Deserialize<DateTime>(JsonSerializer.Serialize(s))),
    ("xmlconvert-dto", "XmlConvert.ToDateTimeOffset (xsd:dateTime)", "rfc3339", s => XmlConvert.ToDateTimeOffset(s)),
};

var jopt = new JsonSerializerOptions { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
string Ser(object o) => JsonSerializer.Serialize(o, jopt);

// run_vectors.py answer: ok + the fields the result exposes.  DateTimeOffset keeps the
// as-written offset; a DateTime of Kind Utc/Local lost it (converted), so it reports no
// fields; Kind Unspecified reports its wall clock without an offset.
Dictionary<string, object?> Answer(Func<string, object> fn, string s) {
    object r;
    try { r = fn(s); }
    catch (Exception e) { var m = e.GetType().Name + ": " + e.Message; return new() { ["ok"] = false, ["error"] = m.Length > 200 ? m[..200] : m }; }
    Dictionary<string, object?> Wall(DateTime w) {
        var f = new Dictionary<string, object?> { ["year"] = w.Year, ["month"] = w.Month, ["day"] = w.Day, ["hour"] = w.Hour,
            ["minute"] = w.Minute, ["second"] = w.Second, ["leap_second"] = false };
        var t = w.Ticks % TimeSpan.TicksPerSecond;
        if (t != 0) f["secfrac"] = t.ToString("D7", inv);
        return f;
    }
    var res = new Dictionary<string, object?> { ["ok"] = true };
    if (r is DateTimeOffset d) { var f = Wall(d.DateTime); f["offset_minutes"] = (int)d.Offset.TotalMinutes; res["fields"] = f; }
    else if (r is DateTime dt && dt.Kind == DateTimeKind.Unspecified) res["fields"] = Wall(dt);
    res["utc"] = OU(r).Item2;
    return res;
}

int Adapter(string key) {
    var api = apis.FirstOrDefault(a => a.key == key);
    if (api.fn == null) { Console.Error.WriteLine($"unknown adapter key {key}; see: probe_dotnet list"); return 2; }
    var stdin = new StreamReader(Console.OpenStandardInput(), new UTF8Encoding(false)).ReadToEnd();
    var o = new StreamWriter(Console.OpenStandardOutput(), new UTF8Encoding(false));
    if (Environment.GetEnvironmentVariable("RFCDT_BATCH") == "1") {
        foreach (var line in stdin.Split('\n')) {
            if (string.IsNullOrWhiteSpace(line)) continue;
            var req = JsonDocument.Parse(line).RootElement;
            var ans = new Dictionary<string, object?> { ["id"] = req.GetProperty("id").GetString() };
            foreach (var kv in Answer(api.fn, req.GetProperty("input").GetString()!)) ans[kv.Key] = kv.Value;
            o.Write(Ser(ans) + "\n");
        }
    } else o.Write(Ser(Answer(api.fn, stdin)) + "\n");
    o.Flush();
    return 0;
}

if (args.Length > 0 && args[0] == "list") { foreach (var a in apis) Console.WriteLine($"{a.key}\t{a.kind}"); return 0; }
if (args.Length > 0 && args[0] == "adapter") return Adapter(args.Length > 1 ? args[1] : "");
var pargs = args.Length > 0 && args[0] == "probe" ? args[1..] : args;
var dir = pargs.Length > 0 ? pargs[0] : ".";
var root = JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "inputs.json"))).RootElement;
var inputs = root.ValueKind == JsonValueKind.Array ? root.EnumerateArray().ToList()
    : root.GetProperty("inputs").EnumerateArray().Concat(root.TryGetProperty("legacy", out var lg) ? lg.EnumerateArray() : Enumerable.Empty<JsonElement>()).ToList();

void Emit(object o) => Console.WriteLine(JsonSerializer.Serialize(o));
void P(string api, Func<string, (string outp, string utc)> f, string mode = "3339") {
    foreach (var rec in inputs) {
        var id = rec.GetProperty("id").GetString(); var s = rec.GetProperty("s").GetString()!;
        try { var (o, u) = f(s); Emit(new { lang = "dotnet", kind = "parse", api, mode, id, input = s, ok = true, @out = o, utc = u }); }
        catch (Exception e) { var m = e.GetType().Name + ": " + e.Message; Emit(new { lang = "dotnet", kind = "parse", api, mode, id, input = s, ok = false, err = m.Length > 160 ? m[..160] : m }); }
    }
}
void F(string api, Func<string> f) {
    try { Emit(new { lang = "dotnet", kind = "format", api, @out = f() }); }
    catch (Exception e) { Emit(new { lang = "dotnet", kind = "format", api, @out = (string?)null, err = e.Message }); }
}

foreach (var x in apis) { var fn = x.fn; P(x.name, s => OU(fn(s))); }

var utc = new DateTime(2026, 9, 24, 12, 0, 0, DateTimeKind.Utc);
var unsp = new DateTime(2026, 9, 24, 12, 0, 0, DateTimeKind.Unspecified);
var loc = utc.ToLocalTime();
var dto = new DateTimeOffset(2026, 9, 24, 14, 0, 0, TimeSpan.FromHours(2));
F("DateTime(Utc).ToString(\"o\")", () => utc.ToString("o", inv));
F("DateTime(Unspecified).ToString(\"o\")", () => unsp.ToString("o", inv));
F("DateTime(Local).ToString(\"o\")", () => loc.ToString("o", inv));
F("DateTime.ToString(\"s\")", () => utc.ToString("s", inv));
F("DateTime.ToString(\"u\")", () => utc.ToString("u", inv));
F("DateTimeOffset.ToString(\"o\")", () => dto.ToString("o", inv));
F("DateTimeOffset.ToString(\"u\")", () => dto.ToString("u", inv));
F("DateTime(Local).ToString(\"yyyy-MM-ddTHH:mm:ssZ\")  [literal Z, lies]", () => loc.ToString("yyyy-MM-ddTHH:mm:ssZ", inv));
F("DateTime(Unspecified).ToString(\"yyyy-MM-dd'T'HH:mm:ssK\")", () => unsp.ToString("yyyy-MM-dd'T'HH:mm:ssK", inv));
F("DateTimeOffset.ToString(\"yyyy-MM-dd'T'HH:mm:sszzz\")", () => dto.ToString("yyyy-MM-dd'T'HH:mm:sszzz", inv));
F("DateTimeOffset.ToString(\"yyyy-MM-ddTHH:mm:sszzz\") CurrentCulture=th-TH", () => dto.ToString("yyyy-MM-ddTHH:mm:sszzz", new CultureInfo("th-TH")));
F("DateTimeOffset.ToString(\"yyyy-MM-ddTHH:mm:sszzz\") CurrentCulture=ar-SA", () => dto.ToString("yyyy-MM-ddTHH:mm:sszzz", new CultureInfo("ar-SA")));
F("DateTimeOffset.ToString(\"yyyy-MM-ddTHH:mm:sszzz\") CurrentCulture=fi-FI", () => dto.ToString("yyyy-MM-ddTHH:mm:sszzz", new CultureInfo("fi-FI")));
F("DateTimeOffset.ToString(\"o\") CurrentCulture=th-TH", () => dto.ToString("o", new CultureInfo("th-TH")));
F("JsonSerializer.Serialize(DateTime Utc)", () => JsonSerializer.Deserialize<string>(JsonSerializer.Serialize(utc))!);
F("JsonSerializer.Serialize(DateTime Unspecified)", () => JsonSerializer.Deserialize<string>(JsonSerializer.Serialize(unsp))!);
F("JsonSerializer.Serialize(DateTime Local)", () => JsonSerializer.Deserialize<string>(JsonSerializer.Serialize(loc))!);
F("JsonSerializer.Serialize(DateTimeOffset)", () => JsonSerializer.Deserialize<string>(JsonSerializer.Serialize(dto))!);
F("DateTime.ToString() [current culture]", () => utc.ToString());
F("XmlConvert.ToString(DateTimeOffset)", () => XmlConvert.ToString(dto));
return 0;
