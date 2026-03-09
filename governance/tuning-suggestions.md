# Tuning Suggestions

## excessive-login-failures
- suggestion: increase threshold from 10 -> 15
- reason: 620 alerts / 30d, FP rate 48%

## impossible-travel
- suggestion: review rule logic
- reason: 0 alerts in 30d

## suspicious-powershell
- suggestion: optimize query
- reason: average query latency 2450 ms
