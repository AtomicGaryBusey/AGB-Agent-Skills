// JsonSchema.Net probe for JSON Schema `format` (date-time, date, time).
//   dotnet build -c Release;  dotnet bin/Release/net10.0/JsProbe.dll [adapter] <variant>
// run_vectors.py adapter: stdin = one string, stdout = {"ok":…}; RFCDT_BATCH=1: JSON lines in, one
// result line per input.  `JsProbe.dll list` prints the date-time variants (<key>\t<target-kind>).
// variants: assert (2020-12, RequireFormatValidation = true), default (2020-12, no options),
//           draft7 (draft-07, no options), date / time (2020-12, format date / time, RequireFormatValidation),
//           pattern (assert + the strict RFC 3339 "pattern" from ecosystem.md),
//           pattern-nl (pattern + "not": {"pattern": "\n"}; .NET Regex `$` also matches before a final newline).
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;

string[] listed = ["assert", "default", "draft7", "pattern", "pattern-nl"];
if (args.Length > 0 && args[0] == "list") { foreach (var k in listed) Console.WriteLine(k + "\trfc3339"); return; }
var rest = args.Length > 0 && args[0] == "adapter" ? args[1..] : args;
var variant = rest.Length > 0 ? rest[0] : "assert";
if (variant is not ("assert" or "default" or "draft7" or "pattern" or "pattern-nl" or "date" or "time"))
{ Console.Error.WriteLine($"unknown variant {variant} (see: list)"); Environment.Exit(2); }
var fmt = variant is "date" or "time" ? variant : "date-time";
var dialect = variant == "draft7" ? "http://json-schema.org/draft-07/schema#" : "https://json-schema.org/draft/2020-12/schema";
const string Pat = "^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)([.][0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$";
var pat = variant is "pattern" or "pattern-nl" ? $",\"pattern\":\"{Pat}\"" : "";
if (variant == "pattern-nl") pat += ",\"not\":{\"pattern\":\"\\n\"}";
var schemaText = $"{{\"$schema\":\"{dialect}\",\"type\":\"string\",\"format\":\"{fmt}\"{pat}}}";
var schema = JsonSchema.FromText(schemaText);
var opts = new EvaluationOptions { OutputFormat = OutputFormat.List };
if (variant is not ("default" or "draft7")) opts.RequireFormatValidation = true;

JsonObject Check(string s)
{
    var result = new JsonObject();
    try
    {
        var inst = JsonSerializer.SerializeToElement(s);
        var r = schema.Evaluate(inst, opts);
        result["ok"] = r.IsValid;
        if (!r.IsValid)
        {
            var errs = (r.Details ?? []).Where(d => d.Errors != null).SelectMany(d => d.Errors!.Values).ToList();
            if (r.Errors != null) errs.AddRange(r.Errors.Values);
            result["error"] = string.Join("; ", errs);
        }
    }
    catch (Exception e) { result["ok"] = false; result["error"] = e.GetType().Name + ": " + e.Message; }
    return result;
}

var utf8 = new UTF8Encoding(false);
if (Environment.GetEnvironmentVariable("RFCDT_BATCH") == "1")
{
    // JSON lines in (ASCII), one result line per request, same order, echoing "id".
    using var reader = new StreamReader(Console.OpenStandardInput(), utf8);
    string? line;
    while ((line = reader.ReadLine()) != null)
    {
        if (string.IsNullOrWhiteSpace(line)) continue;
        var req = JsonNode.Parse(line)!;
        var res = Check((string)req["input"]!);
        res["id"] = (string?)req["id"];
        Console.WriteLine(res.ToJsonString());
    }
    return;
}
string one;
using (var stdin = Console.OpenStandardInput())
using (var ms = new MemoryStream()) { stdin.CopyTo(ms); one = utf8.GetString(ms.ToArray()); }
Console.WriteLine(Check(one).ToJsonString());
