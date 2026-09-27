// Offline build-diff fixture for ServiceNow SDK 4.x (see ../../README.md).
// Each record/script isolates one finding from references/servicenow.md §3.
import { Table, Record, StringColumn, DateTimeColumn, TimeColumn, ScheduledScript } from '@servicenow/sdk/core'

export const x_rfct_dt_sample = Table({
  name: 'x_rfct_dt_sample',
  label: 'Sample',
  schema: {
    label: StringColumn({ label: 'Label' }),
    dt: DateTimeColumn({ label: 'dt' }),
    tm: TimeColumn({ label: 'tm' }),
  },
})

// F2: Time() with no zone uses the BUILD HOST zone -> XML differs per TZ.
Record({ $id: Now.ID['time_nozone'], table: 'x_rfct_dt_sample', data: { label: 'time_nozone', tm: Time({ hours: 12 }) } })
// F1: zone east of UTC, local time before the offset -> 60 min early (expect 19:30, SDK 4.13.0 gives 18:30).
Record({ $id: Now.ID['time_kolkata'], table: 'x_rfct_dt_sample', data: { label: 'time_kolkata', tm: Time({ hours: 1 }, 'Asia/Kolkata') } })
// Control: explicit UTC is host-independent and correct.
Record({ $id: Now.ID['time_utc'], table: 'x_rfct_dt_sample', data: { label: 'time_utc', tm: Time({ hours: 12 }, 'UTC') } })
// F9: the only gate is the TS type; a cast ships an RFC 3339 string verbatim into glide_date_time XML.
Record({ $id: Now.ID['dt_cast'], table: 'x_rfct_dt_sample', data: { label: 'dt_cast', dt: '2024-01-01T12:00:00Z' as any } })

// Control: no timeZone / 'floating' is mapped to UTC by the plugin (scheduled-script-plugin.js:427), so this is host-independent.
ScheduledScript({ $id: Now.ID['sched_floating'], name: 'sched_floating', frequency: 'once', executionStart: '2026-06-01 12:00:00', script: "gs.info('x')" })
// F4: wall time in the US DST gap; offset computed from host-local Dates -> differs on New_York hosts.
ScheduledScript({ $id: Now.ID['sched_gap'], name: 'sched_gap', frequency: 'once', executionStart: '2026-03-08 02:30:00', timeZone: 'Asia/Kolkata', script: "gs.info('x')" })
// F12: month 13 passes the shape regex, then the converter throws; the record is DROPPED and the build exits 0.
ScheduledScript({ $id: Now.ID['sched_bad'], name: 'sched_bad', frequency: 'once', executionStart: '2024-13-01 00:00:00', timeZone: 'Europe/Paris', script: "gs.info('x')" })
