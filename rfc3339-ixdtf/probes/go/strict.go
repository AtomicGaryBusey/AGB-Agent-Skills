package main

import (
	"errors"
	"regexp"
	"time"
)

// rfc3339Re is RFC 3339 §5.6 date-time (ASCII digits only, T/t, Z/z, whole string).
// RE2 has no lookbehind and "$" only matches at end of text without the (?m) flag.
var rfc3339Re = regexp.MustCompile(`^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$`)

// ParseRFC3339Strict is the safe replacement used in GO.md §3.
// It accepts exactly the RFC 3339 date-time grammar (incl. lower-case t/z),
// relies on time.Parse for the §5.7 day-of-month check, and accepts second 60
// only at 23:59:60 UTC on the last day of Mar/Jun/Sep/Dec from 1972 on
// (rfcdt's default "iers-months" policy). time.Time cannot hold second 60,
// so a leap second is returned as :59 (fraction kept) with leap=true.
func ParseRFC3339Strict(s string) (t time.Time, leap bool, err error) {
	if !rfc3339Re.MatchString(s) {
		return time.Time{}, false, errors.New("not an RFC 3339 date-time")
	}
	b := []byte(s)
	b[10] = 'T'
	if b[len(b)-1] == 'z' {
		b[len(b)-1] = 'Z'
	}
	norm := string(b)
	if norm[17:19] == "60" {
		leap = true
		norm = norm[:17] + "59" + norm[19:]
	}
	t, err = time.Parse(time.RFC3339Nano, norm)
	if err != nil {
		return time.Time{}, false, err
	}
	if leap {
		u := t.UTC()
		last := u.AddDate(0, 0, 1).Day() == 1
		m := u.Month()
		if !(u.Hour() == 23 && u.Minute() == 59 && u.Second() == 59 && last &&
			(m == 3 || m == 6 || m == 9 || m == 12) && u.Year() >= 1972) {
			return time.Time{}, false, errors.New("second 60 is not at a leap-second position")
		}
	}
	return t, leap, nil
}
