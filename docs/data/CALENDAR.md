# Trading calendar

See ADR-018.

Default: `WeekdayCalendar` — Monday–Friday, cash session 09:15–15:30 `Asia/Kolkata`.

This is **not** an official NSE holiday calendar. Provenance is `synthetic_weekdays_not_official_nse_holidays`.

To mark holidays:

- ingest a sourced holiday file, or
- call `calendar_from_sessions` on observed bar session dates.

Session dates for bars are computed in IST even when stored timestamps are UTC.
