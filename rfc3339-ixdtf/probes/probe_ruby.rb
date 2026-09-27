# RFC 3339 / RFC 9557 conformance probe for Ruby 3.4 stdlib.
# Usage: TZ=America/New_York ruby probe_ruby.rb [probe] > results/ruby.jsonl
#        ruby probe_ruby.rb list            # adapter keys: <key>\t<target-kind>
#        ruby probe_ruby.rb adapter <key>   # scripts/run_vectors.py adapter (per-process + batch)
#   run_vectors.py --target 'ruby probes/probe_ruby.rb adapter time-iso8601' --batch \
#       --target-kind rfc3339 --target-options fixed --target-has-tzdata yes
require "json"
require "time"
require "date"

# probes/inputs.json schema 2 (inputs + legacy) or the old list form.
def load_inputs
  doc = JSON.parse(File.read(File.join(__dir__, "inputs.json")))
  doc.is_a?(Array) ? doc : doc["inputs"] + (doc["legacy"] || [])
end

def utc_of(t)
  t = t.to_time if t.is_a?(DateTime)
  u = t.getutc
  u.strftime("%Y-%m-%dT%H:%M:%S.%15N")
end

def emit(h) = puts(JSON.generate({ lang: "ruby" }.merge(h)))

# Exception text can carry the input's raw bytes (binary encoding): make it valid UTF-8.
def err_text(e, n) = "#{e.class}: #{e.message.dup.force_encoding("UTF-8").scrub("?")}"[0, n]

# key, probe API name, target kind, parser
APIS = [
  ["time-iso8601", "Time.iso8601 / Time.xmlschema", "rfc3339", ->(s) { Time.iso8601(s) }],
  ["datetime-rfc3339", "DateTime.rfc3339", "rfc3339", ->(s) { DateTime.rfc3339(s) }],
  ["datetime-iso8601", "DateTime.iso8601", "rfc3339", ->(s) { DateTime.iso8601(s) }],
  ["time-parse", "Time.parse", "rfc3339", ->(s) { Time.parse(s) }],
  ["time-strptime-z", "Time.strptime('%Y-%m-%dT%H:%M:%S%z')", "rfc3339", ->(s) { Time.strptime(s, "%Y-%m-%dT%H:%M:%S%z") }],
  ["time-new", "Time.new(s) [Ruby 3.2+ string form]", "rfc3339", ->(s) { Time.new(s) }],
].freeze

def parse_probe(api, fn, inputs, mode = "3339")
  inputs.each do |r|
    begin
      v = fn.call(r["s"])
      emit(kind: "parse", api: api, mode: mode, id: r["id"], input: r["s"], ok: true, out: v.inspect, utc: utc_of(v))
    rescue StandardError => e
      emit(kind: "parse", api: api, mode: mode, id: r["id"], input: r["s"], ok: false, err: err_text(e, 160))
    end
  end
end

# Adapter fields: the result's local wall-clock fields and offset (Time/DateTime keep both).
# DateTime counts days on the Julian calendar before 1582-10-15 (Date::ITALY); RFC 3339 dates
# are Gregorian, so its fields are read on the proleptic Gregorian calendar (new_start).
def fields_of(v)
  if v.is_a?(DateTime)
    v = v.new_start(Date::GREGORIAN)
    ns = (v.sec_fraction * 1_000_000_000).to_i
    sec, off = v.sec, (v.offset * 24 * 60).to_i
  else
    ns = v.nsec
    sec, off = v.sec, v.utc_offset.div(60)
  end
  f = { year: v.year, month: v.month, day: v.day, hour: v.hour, minute: v.min, second: sec,
        leap_second: sec == 60, offset_minutes: off }
  f[:secfrac] = format("%09d", ns) if ns.positive?
  f
end

def answer(fn, s)
  v = fn.call(s)
  { ok: true, fields: fields_of(v) }
rescue StandardError => e
  { ok: false, error: err_text(e, 200) }
end

case ARGV[0]
when "list"
  APIS.each { |k, _, kind, _| puts "#{k}\t#{kind}" }
  exit 0
when "adapter"
  api = APIS.find { |a| a[0] == ARGV[1] }
  abort("unknown adapter key #{ARGV[1].inspect}; see: probe_ruby.rb list") unless api
  data = $stdin.binmode.read.force_encoding("UTF-8")
  if ENV["RFCDT_BATCH"] == "1"
    data.split("\n").each do |line|
      next if line.strip.empty?
      req = JSON.parse(line)
      $stdout.puts JSON.generate({ id: req["id"] }.merge(answer(api[3], req["input"])))
    end
  else
    puts JSON.generate(answer(api[3], data))
  end
  exit 0
when nil, "probe"
else
  abort("usage: probe_ruby.rb [probe] | list | adapter <key>")
end

INPUTS = load_inputs
APIS.each { |_, api, _, fn| parse_probe(api, fn, INPUTS) }

def fmt(api)
  emit(kind: "format", api: api, out: yield)
rescue StandardError => e
  emit(kind: "format", api: api, out: nil, err: e.message)
end
t = Time.utc(2026, 9, 24, 12, 0, 0)
fmt("Time#xmlschema / #iso8601 (utc)") { t.xmlschema }
fmt("Time#xmlschema(3)") { Time.utc(2026, 9, 24, 12, 0, 0, 123456.789r).xmlschema(3) }
fmt("Time#xmlschema (local)") { t.getlocal.xmlschema }
fmt("Time#to_s") { t.to_s }
fmt("Time#inspect") { t.inspect }
fmt("DateTime#rfc3339") { DateTime.new(2026, 9, 24, 14, 0, 0, "+02:00").rfc3339 }
fmt("Time#to_json (json gem, no ActiveSupport)") { JSON.parse(JSON.generate([t]))[0] }
fmt("Time#strftime('%Y-%m-%dT%H:%M:%S%z')") { t.getlocal("+02:00").strftime("%Y-%m-%dT%H:%M:%S%z") }
fmt("Time#strftime('%FT%T%:z')") { t.getlocal("+02:00").strftime("%FT%T%:z") }
fmt("Time.utc(10000).xmlschema") { Time.utc(10000, 1, 1).xmlschema }
fmt("Time.utc(-1).xmlschema") { Time.utc(-1, 1, 1).xmlschema }
fmt("Time.utc(12).xmlschema") { Time.utc(12, 1, 1).xmlschema }
fmt("Time#getlocal('+00:00:30').xmlschema") { t.getlocal("+00:00:30").xmlschema }

