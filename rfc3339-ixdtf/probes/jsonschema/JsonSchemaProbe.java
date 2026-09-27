// networknt json-schema-validator probe for JSON Schema `format` (date-time, date, time).
//
// Classpath: json-schema-validator 3.0.7 + itu 1.14.0 + jackson-core/databind/dataformat-yaml 3.2.1
// + jackson-annotations 2.22 + snakeyaml-engine 3.0.1 + slf4j-api 2.0.17 (all from Maven Central).
// Leave itu off the classpath to probe the java.time OffsetDateTime.parse fallback.
//
//   javac -cp 'lib/*' -d out JsonSchemaProbe.java
//   java -cp 'out:lib/*' JsonSchemaProbe [adapter] <variant>   (run_vectors.py adapter; stdin = one string;
//                                                              RFCDT_BATCH=1: JSON lines, one result per line)
//   java -cp 'out:lib/*' JsonSchemaProbe list                  (date-time variants: <key>\t<target-kind>)
//
// variants: assert        2020-12, format "date-time", formatAssertionsEnabled(true)
//           default       2020-12, format "date-time", no configuration
//           date | time   2020-12, format "date" / "time", assertions enabled
//           draft7        draft-07 dialect, format "date-time", no configuration
//           pattern       as assert, plus the strict RFC 3339 "pattern" from ecosystem.md
import com.networknt.schema.*;
import tools.jackson.databind.node.StringNode;
import java.nio.charset.StandardCharsets;
import java.util.List;

public class JsonSchemaProbe {
    static final String[] LISTED = {"assert", "default", "draft7", "pattern"};

    public static void main(String[] a) throws Exception {
        if (a.length > 0 && a[0].equals("list")) {
            for (String k : LISTED) System.out.println(k + "\trfc3339");
            return;
        }
        if (a.length > 0 && a[0].equals("adapter")) a = java.util.Arrays.copyOfRange(a, 1, a.length);
        String variant = a.length > 0 ? a[0] : "assert";
        String fmt = switch (variant) { case "date" -> "date"; case "time" -> "time"; default -> "date-time"; };
        boolean draft7 = variant.equals("draft7");
        String pat = variant.equals("pattern") ? ",\"pattern\":\"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)([.][0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$\"" : "";
        String schemaText = draft7
            ? "{\"$schema\":\"http://json-schema.org/draft-07/schema#\",\"type\":\"string\",\"format\":\"" + fmt + "\"}"
            : "{\"$schema\":\"https://json-schema.org/draft/2020-12/schema\",\"type\":\"string\",\"format\":\"" + fmt + "\"" + pat + "}";
        boolean enable = !(variant.equals("default") || draft7);
        SchemaRegistry reg = enable
            ? SchemaRegistry.withDefaultDialect(SpecificationVersion.DRAFT_2020_12,
                b -> b.schemaRegistryConfig(SchemaRegistryConfig.builder().formatAssertionsEnabled(true).build()))
            : SchemaRegistry.withDefaultDialect(draft7 ? SpecificationVersion.DRAFT_7 : SpecificationVersion.DRAFT_2020_12);
        Schema schema = reg.getSchema(schemaText);
        if ("1".equals(System.getenv("RFCDT_BATCH"))) {
            // JSON lines in; the runner escapes everything to ASCII, so a small reader suffices.
            tools.jackson.databind.ObjectMapper m = new tools.jackson.databind.ObjectMapper();
            java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(System.in, StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (String line; (line = r.readLine()) != null; ) {
                if (line.isBlank()) continue;
                tools.jackson.databind.JsonNode req = m.readTree(line);
                String res = check(schema, req.get("input").asString());
                out.append("{\"id\": ").append(q(req.get("id").asString())).append(", ").append(res.substring(1)).append('\n');
            }
            System.out.print(out);
            System.out.flush();
            return;
        }
        String s = new String(System.in.readAllBytes(), StandardCharsets.UTF_8);
        System.out.println(check(schema, s));
    }

    static String check(Schema schema, String s) {
        try {
            List<com.networknt.schema.Error> errs = schema.validate(StringNode.valueOf(s));
            if (errs.isEmpty()) return "{\"ok\": true}";
            return "{\"ok\": false, \"error\": " + q(errs.get(0).getMessage()) + "}";
        } catch (Exception e) {
            return "{\"ok\": false, \"error\": " + q(e.toString()) + "}";
        }
    }

    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 0x20 || c > 0x7e) b.append(String.format("\\u%04x", (int) c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
}
