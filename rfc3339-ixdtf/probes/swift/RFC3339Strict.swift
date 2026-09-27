// Strict RFC 3339 date-time parse/format for Swift, independent of Foundation's calendars.
//
// Why not a Foundation formatter: every Foundation parser probed (ISO8601DateFormatter,
// Date.ISO8601FormatStyle / JSONDecoder .iso8601, DateFormatter) uses a Gregorian calendar with the
// 1582 Julian cutover, so "0001-01-01T00:00:00Z" becomes 0000-12-30 proleptic (2 days early),
// and all of them accept inputs outside the grammar (see SWIFT.md).
//
// Policy (same as probes/go/strict.go and rfcdt's default "iers-months"):
//   * exactly the RFC 3339 §5.6 date-time grammar, ASCII digits, T/t, Z/z, whole string;
//   * §5.7 day-of-month check; year 0000-9999 (proleptic Gregorian);
//   * second 60 only at 23:59:60 UTC on the last day of Mar/Jun/Sep/Dec from 1972 on. Date cannot
//     hold a leap second, so it is returned as :59 plus the fraction, with leap = true;
//   * the fraction is kept to 9 digits (Date is a Double: about 0.1 us near 2026).
import Foundation

enum RFC3339Error: Error { case grammar(String), range(String) }

private func daysFromCivil(_ y0: Int, _ m: Int, _ d: Int) -> Int {
    let y = m <= 2 ? y0 - 1 : y0
    let era = (y >= 0 ? y : y - 399) / 400
    let yoe = y - era * 400
    let doy = (153 * (m > 2 ? m - 3 : m + 9) + 2) / 5 + d - 1
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy
    return era * 146097 + doe - 719468
}

private func isLeapYear(_ y: Int) -> Bool { (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 }

func parseRFC3339Strict(_ s: String) throws -> (date: Date, leap: Bool) {
    let b = Array(s.utf8)
    func digits(_ i: Int, _ n: Int) throws -> Int {
        guard i + n <= b.count else { throw RFC3339Error.grammar("short") }
        var v = 0
        for k in i..<(i + n) {
            guard b[k] >= 0x30 && b[k] <= 0x39 else { throw RFC3339Error.grammar("digit expected at \(k)") }
            v = v * 10 + Int(b[k] - 0x30)
        }
        return v
    }
    func lit(_ i: Int, _ c: UInt8...) throws {
        guard i < b.count, c.contains(b[i]) else { throw RFC3339Error.grammar("expected \(c) at \(i)") }
    }
    let y = try digits(0, 4); try lit(4, 0x2D)
    let mo = try digits(5, 2); try lit(7, 0x2D)
    let d = try digits(8, 2); try lit(10, 0x54, 0x74)  // T t
    let h = try digits(11, 2); try lit(13, 0x3A)
    let mi = try digits(14, 2); try lit(16, 0x3A)
    let sec = try digits(17, 2)
    var i = 19
    var nanos = 0
    if i < b.count && b[i] == 0x2E {  // "."
        i += 1
        let start = i
        while i < b.count && b[i] >= 0x30 && b[i] <= 0x39 {
            if i - start < 9 { nanos = nanos * 10 + Int(b[i] - 0x30) }
            i += 1
        }
        guard i > start else { throw RFC3339Error.grammar("empty fraction") }
        for _ in 0..<max(0, 9 - (i - start)) { nanos *= 10 }
    }
    var offMin = 0
    guard i < b.count else { throw RFC3339Error.grammar("missing offset") }
    if b[i] == 0x5A || b[i] == 0x7A {  // Z z
        i += 1
    } else {
        try lit(i, 0x2B, 0x2D)
        let sign = b[i] == 0x2B ? 1 : -1
        let oh = try digits(i + 1, 2); try lit(i + 3, 0x3A)
        let om = try digits(i + 4, 2)
        guard oh <= 23, om <= 59 else { throw RFC3339Error.grammar("offset out of range") }
        offMin = sign * (oh * 60 + om)
        i += 6
    }
    guard i == b.count else { throw RFC3339Error.grammar("trailing characters") }
    let dim = [31, isLeapYear(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    guard (1...12).contains(mo), d >= 1, d <= dim[mo - 1], h <= 23, mi <= 59, sec <= 60 else {
        throw RFC3339Error.grammar("field out of range")
    }
    let secs = (daysFromCivil(y, mo, d) * 86400) + h * 3600 + mi * 60 + min(sec, 59) - offMin * 60
    let leap = sec == 60
    if leap {  // UTC must be 23:59:59 on the last day of Mar/Jun/Sep/Dec, 1972 or later
        let u = secs
        let tod = ((u % 86400) + 86400) % 86400
        let day = (u - tod) / 86400
        // civil date of `day`
        let z = day + 719468
        let era = (z >= 0 ? z : z - 146096) / 146097
        let doe = z - era * 146097
        let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365
        let doy = doe - (365 * yoe + yoe / 4 - yoe / 100)
        let mp = (5 * doy + 2) / 153
        let dd = doy - (153 * mp + 2) / 5 + 1
        let mm = mp < 10 ? mp + 3 : mp - 9
        let yy = yoe + era * 400 + (mm <= 2 ? 1 : 0)
        let last = [31, isLeapYear(yy) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mm - 1]
        guard tod == 86399, dd == last, [3, 6, 9, 12].contains(mm), yy >= 1972 else {
            throw RFC3339Error.range("second 60 is not at a leap-second position")
        }
    }
    return (Date(timeIntervalSince1970: TimeInterval(secs) + TimeInterval(nanos) / 1e9), leap)
}

/// "YYYY-MM-DDTHH:MM:SS[.fff…]Z" in UTC, proleptic Gregorian, fixed `fractionDigits` (0...9).
/// Throws for years outside 0000-9999 instead of printing an invalid or wrong string.
func formatRFC3339UTC(_ date: Date, fractionDigits: Int = 3) throws -> String {
    let t = date.timeIntervalSince1970
    var whole = t.rounded(.down)
    let frac = t - whole
    let scale = pow(10.0, Double(fractionDigits))
    var f = Int((frac * scale).rounded(.down))  // truncate: never print a later instant
    if f >= Int(scale) { f = 0; whole += 1 }
    var secs = Int(whole)
    let tod = ((secs % 86400) + 86400) % 86400
    secs -= tod
    let z = secs / 86400 + 719468
    let era = (z >= 0 ? z : z - 146096) / 146097
    let doe = z - era * 146097
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100)
    let mp = (5 * doy + 2) / 153
    let d = doy - (153 * mp + 2) / 5 + 1
    let m = mp < 10 ? mp + 3 : mp - 9
    let y = yoe + era * 400 + (m <= 2 ? 1 : 0)
    guard (0...9999).contains(y) else { throw RFC3339Error.range("year \(y) outside 0000-9999") }
    var out = String(format: "%04d-%02d-%02dT%02d:%02d:%02d", y, m, d, tod / 3600, (tod / 60) % 60, tod % 60)
    if fractionDigits > 0 { out += "." + String(format: "%0\(fractionDigits)d", f) }
    return out + "Z"
}
