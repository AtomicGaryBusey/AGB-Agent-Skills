#### go — `time.Parse(time.RFC3339)`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t12:00:0 | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as "Z | **TOO STRICT** |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | **TOO LENIENT** |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as  | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot parse " | conforming |

#### go — `time.Parse(time.RFC3339Nano)`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05.999999999Z07:00": cannot parse | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05.999999999Z07:00": cannot parse | **TOO STRICT** |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | **TOO LENIENT** |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05.999999999Z07:00": cannot par | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05.999999999Z07:00": cann | conforming |

#### go — `time.ParseInLocation(time.RFC3339, s, time.Local)`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t12:00:0 | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as "Z | **TOO STRICT** |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | **TOO LENIENT** |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as  | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot parse " | conforming |

#### go — `(*time.Time).UnmarshalJSON`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t12:00:0 | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as "Z | **TOO STRICT** |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | **TOO LENIENT** |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as  | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot parse " | conforming |

#### go — `(*time.Time).UnmarshalText`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t12:00:0 | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as "Z | **TOO STRICT** |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | **TOO LENIENT** |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as  | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot parse " | conforming |

#### go — `json.Unmarshal into struct{T time.Time}`

51 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t12:00:0 | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as "Z | **TOO STRICT** |
| `2026-09-24T12:00:00+24:00` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+23:60` | accepted → UTC 2026-09-23T12:00:00.000000000 (offset +24:00) | **TOO LENIENT** |
| `2016-12-31T23:59:60Z` | rejected: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |
| `2026-09-24T12:00:00,5Z` | accepted → UTC 2026-09-24T12:00:00.500000000 (offset +00:00) | **TOO LENIENT** |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | accepted → UTC 2026-09-24T01:00:00.000000000 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:59` | accepted → UTC 2026-09-23T11:01:00.000000000 (offset +24:59) | **TOO LENIENT** |
| `2026-09-24T12:00:00+24:60` | accepted → UTC 2026-09-23T11:00:00.000000000 (offset +25:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00+25:00` | rejected: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | accepted → UTC 2026-09-23T12:00:00.500000000 (offset +24:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00,123456789123Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | **TOO LENIENT** |
| `2026-09-24T12:00:00.5z` | rejected: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" as  | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot parse " | conforming |

#### go — `encoding/json/v2 Unmarshal into struct{T time.Time}`

54 of 59 probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24t12:00:00Z` | rejected: json: parsing time "2026-09-24t12:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "t1 | **TOO STRICT** |
| `2026-09-24T12:00:00z` | rejected: json: parsing time "2026-09-24T12:00:00z" as "2006-01-02T15:04:05Z07:00": cannot parse "z" | **TOO STRICT** |
| `2016-12-31T23:59:60Z` | rejected: json: parsing time "2016-12-31T23:59:60Z": second out of range | too strict (no leap second) |
| `2016-12-31T18:59:60-05:00` | rejected: json: parsing time "2016-12-31T18:59:60-05:00": second out of range | too strict (no leap second) |
| `2026-09-24T12:00:00.123456789012Z` | accepted → UTC 2026-09-24T12:00:00.123456789 (offset +00:00) | conforming (lossy: fraction truncated to 9 digits) |

Extra inputs (not in `inputs.json`):

| Input | Result | RFC verdict |
|---|---|---|
| `2026-09-24T1:00:00Z` | rejected: json: parsing time "2026-09-24T1:00:00Z" as "2006-01-02T15:04:05Z07:00": cannot parse "1"  | conforming |
| `2026-09-24T12:00:00+24:59` | rejected: json: parsing time "2026-09-24T12:00:00+24:59": timezone hour out of range | conforming |
| `2026-09-24T12:00:00+24:60` | rejected: json: parsing time "2026-09-24T12:00:00+24:60": timezone hour out of range | conforming |
| `2026-09-24T12:00:00+25:00` | rejected: json: parsing time "2026-09-24T12:00:00+25:00": time zone offset hour out of range | conforming |
| `2026-09-24T12:00:00.5+23:60` | rejected: json: parsing time "2026-09-24T12:00:00.5+23:60": timezone minute out of range | conforming |
| `2026-09-24T12:00:00,123456789123Z` | rejected: json: parsing time "2026-09-24T12:00:00,123456789123Z" as "2006-01-02T15:04:05Z07:00": can | conforming |
| `2026-09-24T12:00:00.5z` | rejected: json: parsing time "2026-09-24T12:00:00.5z" as "2006-01-02T15:04:05Z07:00": cannot parse " | **TOO STRICT** |
| `2026-09-24T12:00:00+00:44:30` | rejected: json: parsing time "2026-09-24T12:00:00+00:44:30": extra text: ":30" | conforming |
| `0099-01-01T00:00:00Z` | accepted → UTC 0099-01-01T00:00:00.000000000 (offset +00:00) | conforming |
| `2026-09-24T12:00:00\u00a0Z` | rejected: json: parsing time "2026-09-24T12:00:00\xc2\xa0Z" as "2006-01-02T15:04:05Z07:00": cannot p | conforming |

