// RFC 3339 / RFC 9557 probe for Apple Foundation (Swift).
//
//   swiftc -O -o "$BUILD/swiftrfc" probes/swift/main.swift probes/swift/RFC3339Strict.swift
//   TZ=America/New_York "$BUILD/swiftrfc" probe probes/inputs.json > results/swift.jsonl
//   TZ=America/New_York "$BUILD/swiftrfc" produce                 >> results/swift.jsonl
//   "$BUILD/swiftrfc" adapter <api-key>     (run_vectors.py adapter; per-process or RFCDT_BATCH=1)
//   "$BUILD/swiftrfc" list                  (adapter keys: <key>\t<target-kind>)
//
// Output rows follow probes/analyze.py: {lang, kind, api, mode, id, input, ok, out, utc, err}.
// "utc" is computed from timeIntervalSince1970 with a proleptic-Gregorian civil-from-days
// routine (NOT with a Foundation formatter, whose Gregorian calendar has a Julian cutover),
// rounded to 1 microsecond: Date is a Double, so digits past ~0.1 us are float noise.
import Foundation

// MARK: - helpers

func civil(_ z0: Int64) -> (Int64, Int, Int) {  // days since 1970-01-01 -> proleptic Gregorian y/m/d
    let z = z0 + 719468
    let era = (z >= 0 ? z : z - 146096) / 146097
    let doe = z - era * 146097
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365
    let y = yoe + era * 400
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100)
    let mp = (5 * doy + 2) / 153
    let d = Int(doy - (153 * mp + 2) / 5 + 1)
    let m = Int(mp < 10 ? mp + 3 : mp - 9)
    return (m <= 2 ? y + 1 : y, m, d)
}

func utcString(_ d: Date) -> String {
    let t = d.timeIntervalSince1970
    var us = Int64((t * 1_000_000).rounded())
    var secs = us >= 0 ? us / 1_000_000 : -((-us + 999_999) / 1_000_000)
    us -= secs * 1_000_000
    var days = secs >= 0 ? secs / 86400 : -((-secs + 86399) / 86400)
    secs -= days * 86400
    if secs >= 86400 { secs -= 86400; days += 1 }
    let (y, m, dd) = civil(days)
    let ys = y < 0 ? String(format: "-%04lld", -y) : String(format: "%04lld", y)
    return ys + String(format: "-%02d-%02dT%02lld:%02lld:%02lld.%06lld", m, dd, secs / 3600, (secs / 60) % 60, secs % 60, us)
}

func emit(_ o: [String: Any?]) {
    var clean: [String: Any] = [:]
    for (k, v) in o { clean[k] = v ?? NSNull() }
    let data = try! JSONSerialization.data(withJSONObject: clean, options: [.sortedKeys, .withoutEscapingSlashes])
    print(String(decoding: data, as: UTF8.self))
}

struct ProbeError: Error, CustomStringConvertible { let description: String }
func must(_ d: Date?, _ why: String = "returned nil") throws -> Date {
    guard let d else { throw ProbeError(description: why) }
    return d
}

let posix = Locale(identifier: "en_US_POSIX")
let utcTZ = TimeZone(identifier: "UTC")!
func dfmt(_ pattern: String, locale: Locale? = posix, tz: TimeZone? = nil, lenient: Bool = false) -> DateFormatter {
    let f = DateFormatter()
    if let locale { f.locale = locale }
    if let tz { f.timeZone = tz }
    f.dateFormat = pattern
    f.isLenient = lenient
    return f
}
func isoFmt(_ opts: ISO8601DateFormatter.Options? = nil, tz: TimeZone? = nil) -> ISO8601DateFormatter {
    let f = ISO8601DateFormatter()
    if let opts { f.formatOptions = opts }
    if let tz { f.timeZone = tz }
    return f
}

// MARK: - consumers

let isoDefault = isoFmt()
let isoFrac = isoFmt([.withInternetDateTime, .withFractionalSeconds])
let decoderISO: JSONDecoder = { let d = JSONDecoder(); d.dateDecodingStrategy = .iso8601; return d }()
let decoderFrac: JSONDecoder = {
    let d = JSONDecoder()
    d.dateDecodingStrategy = .custom { dec in
        let s = try dec.singleValueContainer().decode(String.self)
        if let v = isoFrac.date(from: s) ?? isoDefault.date(from: s) { return v }
        throw DecodingError.dataCorrupted(.init(codingPath: dec.codingPath, debugDescription: "bad date"))
    }
    return d
}()
func jsonDecode(_ s: String, _ dec: JSONDecoder) throws -> Date {
    let lit = try JSONSerialization.data(withJSONObject: [s], options: [])  // ["<s>"] as JSON
    return try dec.decode([Date].self, from: lit)[0]
}

let apis: [(key: String, name: String, fn: (String) throws -> Date)] = [
    ("iso", "ISO8601DateFormatter() [default: .withInternetDateTime]", { try must(isoDefault.date(from: $0)) }),
    ("isofrac", "ISO8601DateFormatter [.withInternetDateTime, .withFractionalSeconds]", { try must(isoFrac.date(from: $0)) }),
    ("isoboth", "ISO8601DateFormatter: try .withFractionalSeconds, then default", {
        try must(isoFrac.date(from: $0) ?? isoDefault.date(from: $0)) }),
    ("isostyle", "Date(s, strategy: .iso8601)", { try Date($0, strategy: .iso8601) }),
    ("isostylefrac", "Date.ISO8601FormatStyle(includingFractionalSeconds: true).parse", {
        try Date.ISO8601FormatStyle(includingFractionalSeconds: true).parse($0) }),
    ("jsoniso", "JSONDecoder .dateDecodingStrategy = .iso8601", { try jsonDecode($0, decoderISO) }),
    ("jsonfrac", "JSONDecoder .custom (ISO8601DateFormatter frac, then default)", { try jsonDecode($0, decoderFrac) }),
    ("dfposix", "DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\")", {
        try must(dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX").date(from: $0)) }),
    ("dfposixfrac", "DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX\")", {
        try must(dfmt("yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX").date(from: $0)) }),
    ("dfposixlenient", "DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", isLenient=true)", {
        try must(dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", lenient: true).date(from: $0)) }),
    ("dfliteralz", "DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ss'Z'\") [default TZ]", {
        try must(dfmt("yyyy-MM-dd'T'HH:mm:ss'Z'").date(from: $0)) }),
    ("dfdefault", "DateFormatter(Locale.current, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\") [no en_US_POSIX]", {
        try must(dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: nil).date(from: $0)) }),
    ("dfth", "DateFormatter(th_TH, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\") [no en_US_POSIX]", {
        try must(dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: Locale(identifier: "th_TH")).date(from: $0)) }),
    ("strict", "parseRFC3339Strict (RFC3339Strict.swift: byte parser + civil arithmetic)", { try parseRFC3339Strict($0).date }),
]

struct ProbeInput: Decodable { let id: String; let s: String }
struct ProbeInputs: Decodable { let inputs: [ProbeInput]; let legacy: [ProbeInput]? }

func probe(_ path: String) {
    // probes/inputs.json schema 2 ({"inputs", "legacy"}: inputs + legacy) or the old list form.
    // JSONDecoder, not JSONSerialization (whose NSString bridge drops a leading U+FEFF).
    let data = FileManager.default.contents(atPath: path)!
    let dec = JSONDecoder()
    let inputs: [ProbeInput]
    if let list = try? dec.decode([ProbeInput].self, from: data) {
        inputs = list
    } else {
        let d = try! dec.decode(ProbeInputs.self, from: data)
        inputs = d.inputs + (d.legacy ?? [])
    }
    for a in apis {
        for rec in inputs {
            let id = rec.id, s = rec.s
            do {
                let d = try a.fn(s)
                emit(["lang": "swift", "kind": "parse", "api": a.name, "mode": "3339", "id": id, "input": s,
                      "ok": true, "out": isoFrac.string(from: d), "utc": utcString(d)])
            } catch {
                emit(["lang": "swift", "kind": "parse", "api": a.name, "mode": "3339", "id": id, "input": s,
                      "ok": false, "err": String(String(describing: error).prefix(160))])
            }
        }
    }
}

struct BatchLine: Decodable { let id: String; let input: String }

func adapterAnswer(_ a: (key: String, name: String, fn: (String) throws -> Date), _ s: String) -> [String: Any?] {
    do {
        let d = try a.fn(s)
        return ["ok": true, "utc": utcString(d)]
    } catch {
        return ["ok": false, "error": String(String(describing: error).prefix(120))]
    }
}

// run_vectors.py adapter: per-process (stdin = one string) or batch (RFCDT_BATCH=1, JSON lines).
// Date keeps no offset, so no "fields" are returned; "utc" feeds instant_check.py.
func adapter(_ key: String) {
    let data = FileHandle.standardInput.readDataToEndOfFile()
    guard let a = apis.first(where: { $0.key == key }) else {
        FileHandle.standardError.write("unknown adapter key \(key); see: swiftrfc list\n".data(using: .utf8)!)
        exit(2)
    }
    if ProcessInfo.processInfo.environment["RFCDT_BATCH"] == "1" {
        for line in String(decoding: data, as: UTF8.self).split(separator: "\n", omittingEmptySubsequences: true) {
            // JSONDecoder, not JSONSerialization: the NSString bridge drops a leading U+FEFF (BOM),
            // which would hide vector 3339-5.6-068 from the target.
            guard let req = try? JSONDecoder().decode(BatchLine.self, from: Data(line.utf8)) else {
                emit(["ok": false, "error": "bad batch line"]); continue
            }
            var o = adapterAnswer(a, req.input)
            o["id"] = req.id
            emit(o)
        }
        return
    }
    emit(adapterAnswer(a, String(decoding: data, as: UTF8.self)))
}

// MARK: - producers

func F(_ api: String, _ f: () throws -> String) {
    do { emit(["lang": "swift", "kind": "format", "api": api, "out": try f()]) }
    catch { emit(["lang": "swift", "kind": "format", "api": api, "out": nil, "err": String(describing: error)]) }
}

func produce() {
    let t = Date(timeIntervalSince1970: 1_790_251_200)  // 2026-09-24T12:00:00Z
    let paris = TimeZone(identifier: "Europe/Paris")!
    let monroviaT = Date(timeIntervalSince1970: 43_200)          // 1970-01-01T12:00:00Z
    let paris1850 = Date(timeIntervalSince1970: -3_786_825_600 - 561)  // 1850-01-01T00:00 LMT (+00:09:21)
    let y1 = Date(timeIntervalSince1970: -62_135_596_800)        // 0001-01-01T00:00:00Z proleptic
    let y0 = Date(timeIntervalSince1970: -62_167_219_200)        // 0000-01-01T00:00:00Z proleptic
    let ym1 = Date(timeIntervalSince1970: -62_198_755_200)       // -0001-01-01T00:00:00Z proleptic
    let y9999 = Date(timeIntervalSince1970: 253_402_300_799)     // 9999-12-31T23:59:59Z
    let y10000 = Date(timeIntervalSince1970: 253_402_300_800)    // 10000-01-01T00:00:00Z
    let dec28 = Date(timeIntervalSince1970: 1_798_459_200)       // 2026-12-28T12:00:00Z (ISO week 2027-W53? week-year 2027)
    let off30 = TimeZone(secondsFromGMT: 30)!
    let offM4430 = TimeZone(secondsFromGMT: -2670)!
    let lon = TimeZone(identifier: "Europe/London")!
    let jan = Date(timeIntervalSince1970: 1_768_478_400)         // 2026-01-15T12:00:00Z

    F("ISO8601DateFormatter().string(from:) [timeZone default GMT]") { isoDefault.string(from: t) }
    F("ISO8601DateFormatter, timeZone = .current (America/New_York)") { isoFmt(tz: .current).string(from: t) }
    F("ISO8601DateFormatter, timeZone = Europe/Paris") { isoFmt(tz: paris).string(from: t) }
    F("ISO8601DateFormatter, timeZone = Europe/London, January (offset 0 but known)") { isoFmt(tz: lon).string(from: jan) }
    F("ISO8601DateFormatter [.withFractionalSeconds], +0.123456789 s") { isoFrac.string(from: t.addingTimeInterval(0.123456789)) }
    F("ISO8601DateFormatter [.withFractionalSeconds], +0 s") { isoFrac.string(from: t) }
    F("ISO8601DateFormatter [.withFractionalSeconds], +0.9996 s") { isoFrac.string(from: t.addingTimeInterval(0.9996)) }
    F("ISO8601DateFormatter [.withFractionalSeconds], -0.0004 s (just before 12:00Z)") { isoFrac.string(from: t.addingTimeInterval(-0.0004)) }
    F("ISO8601DateFormatter, TimeZone(secondsFromGMT: 30) (+00:00:30)") { isoFmt(tz: off30).string(from: t) }
    F("ISO8601DateFormatter, TimeZone(secondsFromGMT: -2670) (-00:44:30)") { isoFmt(tz: offM4430).string(from: t) }
    F("ISO8601DateFormatter, Africa/Monrovia, 1970-01-01T12:00:00Z (MMT -00:44:30)") {
        isoFmt(tz: TimeZone(identifier: "Africa/Monrovia")!).string(from: monroviaT) }
    F("ISO8601DateFormatter, Europe/Paris, 1850-01-01 00:00 LMT (+00:09:21)") { isoFmt(tz: paris).string(from: paris1850) }
    F("ISO8601DateFormatter, 0001-01-01T00:00:00Z (proleptic)") { isoDefault.string(from: y1) }
    F("ISO8601DateFormatter, 0000-01-01T00:00:00Z (proleptic)") { isoDefault.string(from: y0) }
    F("ISO8601DateFormatter, -0001-01-01T00:00:00Z (proleptic)") { isoDefault.string(from: ym1) }
    F("ISO8601DateFormatter, 9999-12-31T23:59:59Z") { isoDefault.string(from: y9999) }
    F("ISO8601DateFormatter, 10000-01-01T00:00:00Z") { isoDefault.string(from: y10000) }
    F("ISO8601DateFormatter [.withInternetDateTime, .withSpaceBetweenDateAndTime]") {
        isoFmt([.withInternetDateTime, .withSpaceBetweenDateAndTime]).string(from: t) }
    F("ISO8601DateFormatter [.withInternetDateTime] minus .withColonSeparatorInTimeZone") {
        isoFmt([.withFullDate, .withFullTime, .withDashSeparatorInDate, .withColonSeparatorInTime], tz: paris).string(from: t) }
    F("ISO8601DateFormatter.string(from:timeZone:formatOptions: [.withInternetDateTime])") {
        ISO8601DateFormatter.string(from: t, timeZone: paris, formatOptions: [.withInternetDateTime]) }

    F("date.formatted(.iso8601)") { t.formatted(.iso8601) }
    F("Date.ISO8601FormatStyle(timeZone: Europe/Paris).format") { Date.ISO8601FormatStyle(timeZone: paris).format(t) }
    F("Date.ISO8601FormatStyle(timeZone: .current).format") { Date.ISO8601FormatStyle(timeZone: .current).format(t) }
    F("Date.ISO8601FormatStyle(includingFractionalSeconds: true), +0.123456789 s") {
        Date.ISO8601FormatStyle(includingFractionalSeconds: true).format(t.addingTimeInterval(0.123456789)) }
    F("Date.ISO8601FormatStyle(includingFractionalSeconds: true), +0.9996 s") {
        Date.ISO8601FormatStyle(includingFractionalSeconds: true).format(t.addingTimeInterval(0.9996)) }
    F("Date.ISO8601FormatStyle(timeZone: secondsFromGMT 30)") { Date.ISO8601FormatStyle(timeZone: off30).format(t) }
    F("Date.ISO8601FormatStyle, Africa/Monrovia 1970") {
        Date.ISO8601FormatStyle(timeZone: TimeZone(identifier: "Africa/Monrovia")!).format(monroviaT) }
    F("Date.ISO8601FormatStyle, Europe/Paris 1850 LMT") { Date.ISO8601FormatStyle(timeZone: paris).format(paris1850) }
    F("date.formatted(.iso8601), 0001-01-01T00:00:00Z") { y1.formatted(.iso8601) }
    F("date.formatted(.iso8601), 0000-01-01T00:00:00Z") { y0.formatted(.iso8601) }
    F("date.formatted(.iso8601), -0001-01-01T00:00:00Z") { ym1.formatted(.iso8601) }
    F("date.formatted(.iso8601), 10000-01-01T00:00:00Z") { y10000.formatted(.iso8601) }
    F("Date.ISO8601FormatStyle(dateTimeSeparator: .space)") { Date.ISO8601FormatStyle(dateTimeSeparator: .space).format(t) }
    F("Date.ISO8601FormatStyle(timeZoneSeparator: .omitted, timeZone: Paris)") {
        Date.ISO8601FormatStyle(timeZoneSeparator: .omitted, timeZone: paris).format(t) }

    let enc: (JSONEncoder.DateEncodingStrategy?) -> JSONEncoder = { s in let e = JSONEncoder(); if let s { e.dateEncodingStrategy = s }; return e }
    F("JSONEncoder .iso8601") { String(decoding: try enc(.iso8601).encode([t.addingTimeInterval(0.5)]), as: UTF8.self) }
    F("JSONEncoder default (.deferredToDate)") { String(decoding: try enc(nil).encode([t]), as: UTF8.self) }
    F("JSONEncoder .iso8601, 10000-01-01T00:00:00Z") { String(decoding: try enc(.iso8601).encode([y10000]), as: UTF8.self) }

    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\") [default TZ New York]") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX").string(from: t) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX", tz: utcTZ).string(from: t) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ss'Z'\") [default TZ!]") { dfmt("yyyy-MM-dd'T'HH:mm:ss'Z'").string(from: t) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssZ\") [New York]") { dfmt("yyyy-MM-dd'T'HH:mm:ssZ").string(from: t) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssZZZZZ\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssZZZZZ", tz: utcTZ).string(from: t) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssxxx\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssxxx", tz: utcTZ).string(from: t) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", secondsFromGMT -2670)") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", tz: offM4430).string(from: t) }
    F("DateFormatter(en_US_POSIX, \"YYYY-MM-dd'T'HH:mm:ssXXXXX\", UTC) 2026-12-28 [week-year]") { dfmt("YYYY-MM-dd'T'HH:mm:ssXXXXX", tz: utcTZ).string(from: dec28) }
    F("DateFormatter(en_US_POSIX, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", UTC) 0001-01-01T00:00:00Z [Julian cutover]") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", tz: utcTZ).string(from: y1) }
    F("DateFormatter(Locale.current=\(Locale.current.identifier), \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: nil, tz: utcTZ).string(from: t) }
    F("DateFormatter(th_TH, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: Locale(identifier: "th_TH"), tz: utcTZ).string(from: t) }
    F("DateFormatter(ar_SA, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: Locale(identifier: "ar_SA"), tz: utcTZ).string(from: t) }
    F("DateFormatter(en-US-u-hc-h12, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: Locale(identifier: "en-US-u-hc-h12"), tz: utcTZ).string(from: t) }
    F("DateFormatter(fi_FI, \"yyyy-MM-dd'T'HH:mm:ssXXXXX\", UTC)") { dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", locale: Locale(identifier: "fi_FI"), tz: utcTZ).string(from: t) }
    F("DateFormatter(en_US_POSIX, calendar=.buddhist explicitly, UTC)") {
        let f = dfmt("yyyy-MM-dd'T'HH:mm:ssXXXXX", tz: utcTZ); f.calendar = Calendar(identifier: .buddhist); return f.string(from: t) }
    F("\"\\(date)\" / date.description") { "\(t)" }
    F("date.ISO8601Format()") { t.ISO8601Format() }
    F("formatRFC3339UTC(date, fractionDigits: 3), +0.9996 s") { try formatRFC3339UTC(t.addingTimeInterval(0.9996)) }
    F("formatRFC3339UTC(date, fractionDigits: 6), 0001-01-01T00:00:00Z") { try formatRFC3339UTC(y1, fractionDigits: 6) }
    F("formatRFC3339UTC(date, fractionDigits: 0), 0000-01-01T00:00:00Z") { try formatRFC3339UTC(y0, fractionDigits: 0) }
    F("formatRFC3339UTC(date), 10000-01-01T00:00:00Z") { try formatRFC3339UTC(y10000) }
}

// MARK: - main

let args = CommandLine.arguments
switch args.count > 1 ? args[1] : "" {
case "probe": probe(args.count > 2 ? args[2] : "inputs.json")
case "produce": produce()
case "adapter": adapter(args.count > 2 ? args[2] : "")
case "list": for a in apis { print("\(a.key)\trfc3339") }  // <key>\t<target-kind>
default:
    FileHandle.standardError.write("usage: swiftrfc probe <inputs.json> | produce | adapter <key> | list\n".data(using: .utf8)!)
    exit(2)
}
