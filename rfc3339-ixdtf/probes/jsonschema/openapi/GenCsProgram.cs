// Adapter for the C# DateTimeJsonConverter emitted by openapi-generator (probed: openapi-generator-cli 7.25.0).
//   java -jar openapi-generator-cli-7.25.0.jar generate -i spec.yaml -g csharp -o out-csharp
//   dotnet new console -n GenCs; copy out-csharp/src/Org.OpenAPITools/Client/DateTimeJsonConverter.cs next to this file
//   dotnet build -c Release;  dotnet bin/Release/net10.0/GenCs.dll          (run_vectors.py adapter; stdin = one string)
//   dotnet bin/Release/net10.0/GenCs.dll produce                            (writer: Utc / Unspecified / Local DateTime)
using System.Text.Json;
using Org.OpenAPITools.Client;
if (args.Length > 0) { var oo = new JsonSerializerOptions(); oo.Converters.Add(new DateTimeJsonConverter());
 foreach (var d in new[]{ new DateTime(2026,9,24,12,0,0,DateTimeKind.Utc), new DateTime(2026,9,24,12,0,0,DateTimeKind.Unspecified), new DateTime(2026,9,24,8,0,0,DateTimeKind.Local)}) Console.WriteLine(d.Kind + " -> " + JsonSerializer.Serialize(d, oo)); return; }
var s = new StreamReader(Console.OpenStandardInput()).ReadToEnd();
var o = new JsonSerializerOptions(); o.Converters.Add(new DateTimeJsonConverter());
try {
  var d = JsonSerializer.Deserialize<DateTime>(JsonSerializer.Serialize(s), o);
  Console.WriteLine(JsonSerializer.Serialize(new { ok = true, utc = d.ToString("yyyy-MM-ddTHH:mm:ss.fffffff") + (d.Kind == DateTimeKind.Utc ? "Z" : " kind=" + d.Kind), reser = JsonSerializer.Serialize(d, o) }));
} catch (Exception e) { Console.WriteLine(JsonSerializer.Serialize(new { ok = false, error = e.GetType().Name })); }
