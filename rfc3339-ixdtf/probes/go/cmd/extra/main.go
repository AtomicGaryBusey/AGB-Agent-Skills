package main

import (
	"fmt"
	"time"
)

func show(label string, t time.Time, err error) {
	if err != nil {
		fmt.Printf("%-60s ERR %v\n", label, err)
		return
	}
	fmt.Printf("%-60s OK utc=%s loc=%q\n", label, t.UTC().Format(time.RFC3339Nano), t.Location().String())
}

func main() {
	t, err := time.Parse("2006-01-02T15:04:05", "2026-09-24T12:00:00")
	show(`Parse("2006-01-02T15:04:05", "...T12:00:00")`, t, err)
	t, err = time.ParseInLocation("2006-01-02T15:04:05", "2026-09-24T12:00:00", time.Local)
	show(`ParseInLocation(no-zone layout, ..., Local)`, t, err)
	t, err = time.Parse("2006-01-02T15:04:05Z", "2026-09-24T12:00:00Z")
	show(`Parse(literal-Z layout, "...Z")`, t, err)
	t, err = time.Parse("2006-01-02T15:04:05Z", "2026-09-24T12:00:00+02:00")
	show(`Parse(literal-Z layout, "...+02:00")`, t, err)
	t, err = time.Parse(time.DateTime, "2026-09-24 12:00:00")
	show(`Parse(time.DateTime, "2026-09-24 12:00:00")`, t, err)
	t, err = time.Parse("2006-01-02T15:04:05Z07:00", "2026-09-24T12:00:00.123456789Z")
	show(`Parse(RFC3339 copy literal, fraction)`, t, err)
	t, err = time.Parse("2006-01-02T15:04:05.000Z07:00", "2026-09-24T12:00:00.123456789Z")
	show(`Parse(".000Z07:00", 9 digits)`, t, err)
	t, err = time.Parse("2006-01-02T15:04:05.000Z07:00", "2026-09-24T12:00:00Z")
	show(`Parse(".000Z07:00", no fraction)`, t, err)
	t, err = time.Parse(time.RFC3339, "2026-09-24T12:00:00.999999999999Z")
	show(`Parse(RFC3339, .999999999999 12 digits)`, t, err)
	t, err = time.Parse(time.RFC3339, "2026-12-31T23:59:59.9999999999Z")
	show(`Parse(RFC3339, 23:59:59.9999999999 rounding?)`, t, err)
	a := time.Date(2026, 9, 24, 12, 0, 0, 0, time.UTC)
	b := a.AddDate(8000, 0, 0)
	fmt.Println("AddDate(8000) Format:", b.Format(time.RFC3339))
	// Local host in UTC offset 0 (Europe/London winter)
	lon, _ := time.LoadLocation("Europe/London")
	w := time.Date(2026, 1, 15, 12, 0, 0, 0, lon)
	fmt.Println("Europe/London winter Format RFC3339:", w.Format(time.RFC3339))
	x, _ := time.Parse(time.RFC3339, "2026-09-24T12:00:00+23:60")
	_, e := x.MarshalJSON()
	fmt.Println("Parse(+23:60) -> Format:", x.Format(time.RFC3339), " MarshalJSON err:", e)
}
