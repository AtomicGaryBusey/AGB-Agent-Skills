---
type: regex
flags: "mi"
match: "not_contains"
---
^(?=[^\n]*(?:timeutil\.py[`'\"]?(?:[:#]L?\s?|,?\s+(?:lines?|l\.|L)\s*)(?:47|46|45)(?!\d)|format_instant))(?=[^\n]*(?:millisecond|three|3 (fractional )?digits|fraction|secfrac|precision))(?=[^\n]*(?:\b(?:Nonconformit(?:y|ies)|Deviations?|Advisor(?:y|ies))\b))\|[^\n]*$
