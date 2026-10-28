# transformer-date

Normalizes date strings and Unix timestamps to a consistent YYYY-MM-DD HH:MM:SS format.

DateTransformer is a data transformation tool that parses heterogeneous date/datetime strings and returns a normalized timestamp string in the fixed format:
- Output format: "%Y-%m-%d %H:%M:%S" (e.g., 2026-03-03 14:05:00)

It is intended for cleaning and harmonizing date columns coming from mixed sources (UCI datasets, clinical exports, logs, manually entered CSVs, etc.).

## What this tool does
- Accepts an input value as a string and converts it into a standardized datetime string.
- Supports multiple input styles, including:
- Common explicit formats (examples):
- YYYY-MM-DD / YYYY-MM-DD HH:MM / YYYY-MM-DD HH:MM:SS
- YYYY/MM/DD variants
- DD.MM.YYYY variants
- DD/MM/YYYY variants
- ISO-8601-like formats:
- YYYY-MM-DDTHH:MM:SS
- fractional seconds: YYYY-MM-DDTHH:MM:SS.sss
- timezone suffixes: Z or ±HH:MM
- also accepts a single space instead of T
- Unix timestamps:
- seconds (10 digits), e.g. 1700000000
- milliseconds (13 digits), e.g. 1700000000000
- float seconds, e.g. 1700000000.123

## Parsing rules
- Unix timestamps are interpreted as UTC.
- Timezone-aware datetimes (e.g., ISO strings with Z / +02:00) are:
	1.	converted to UTC, then
	2.	formatted without timezone information.
- Naive datetimes (no timezone information) are treated as-is (no implicit timezone shift).
- If the input contains only a date (no time), the time defaults to 00:00:00.
- If the string cannot be parsed, the transformer raises a ValueError.

## Configuration

This transformer currently has no hyperparameters (TransformerConfig is empty).

## Output
- Returns a string in the format: YYYY-MM-DD HH:MM:SS

Example outputs:
- 2026-03-03 00:00:00
- 2026-03-03 14:05:23

# Notes / assumptions
- Empty strings are rejected (ValueError).
- The transformer is strict about numeric conversion for Unix timestamps (only the supported digit-length patterns / float pattern are accepted).
- When outputting timezone-aware inputs, timezone is normalized to UTC and then removed from the final formatted string.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Set APP_ID and platform URLs in .env before connecting.
python main.py
```

Build the container with `docker build -t tool-transformer-date .`.
