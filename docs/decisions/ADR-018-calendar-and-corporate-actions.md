# ADR-018 — Trading calendar and corporate-action policy

## Context
Indian cash sessions are 09:15–15:30 Asia/Kolkata, with exchange holidays that QUANT LAB does not have a licensed official file for.

## Decision

### Calendar
`WeekdayCalendar` is Mon–Fri 09:15–15:30 IST with provenance `synthetic_weekdays_not_official_nse_holidays`. It **must not** be described as the NSE holiday calendar.

Holidays may be:

1. supplied by a **sourced** file the user ingested, or
2. **derived from observed bar sessions**.

Republic Day (2024-01-26) is a weekday and remains a session on the synthetic calendar until a sourced holiday file says otherwise.

### Corporate actions
Corporate-action rows require `available_time`. If `announcement_time` is unknown, it stays `None` and the event is **unknowable** (`is_knowable_at` is false). Missing CA files yield integrity `NOT_TESTED`, never a silent PASS.

Default return is **price return**. Dividends are not silently embedded. Adjusted prices are an explicit `PriceKind.ADJUSTED_PRICE` series.

## Consequences
- `momentum_N` is N **trading sessions** on the research calendar, not N calendar days.
- Date-only vendor CSVs use `available_time = session close 15:30 IST` and record `availability_convention=session_close` (research-gate WARN). Naive datetimes are rejected.

## References
Prompt 04; `docs/data/CALENDAR.md`; `docs/data/CORPORATE_ACTIONS.md`
