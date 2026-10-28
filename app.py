import re
from datetime import datetime, timezone

from pydantic.dataclasses import dataclass
from pyfedappwrap.transformation.base_transformer import BaseTransformerAPP
from pyfedappwrap.transformation.config.transformer_config import BaseTransformerConfig


@dataclass
class TransformerConfig(BaseTransformerConfig):
    pass


FIXED_OUT_FMT = "%Y-%m-%d %H:%M:%S"

# Common explicit patterns we try before falling back to ISO-style parsing
_CANDIDATE_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%d.%m.%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
]

_iso_fraction_rx = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$")
_iso_no_seconds_rx = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?$")


def _parse_unix_timestamp(s: str) -> datetime | None:
    # Accept integer/float seconds or milliseconds
    try:
        s_clean = s.strip()
        if re.fullmatch(r"[+-]?\d{10}", s_clean):  # seconds
            return datetime.fromtimestamp(int(s_clean), tz=timezone.utc)
        if re.fullmatch(r"[+-]?\d{13}", s_clean):  # milliseconds
            return datetime.fromtimestamp(int(s_clean) / 1000.0, tz=timezone.utc)
        # float seconds
        if re.fullmatch(r"[+-]?\d+\.\d+", s_clean):
            return datetime.fromtimestamp(float(s_clean), tz=timezone.utc)
    except (OverflowError, ValueError):
        pass
    return None


def _parse_iso_like(s: str) -> datetime | None:
    # Normalize 'Z' to '+00:00' for fromisoformat, and ensure seconds field exists
    s_norm = s.strip()
    if s_norm.endswith("Z"):
        s_norm = s_norm[:-1] + "+00:00"

    # Add :00 seconds if it's missing in ISO string with only HH:MM
    if _iso_no_seconds_rx.match(s_norm):
        # insert seconds before any timezone suffix
        if '+' in s_norm[16:] or '-' in s_norm[16:]:
            # find last + or - after time part
            idx = max(s_norm.rfind('+'), s_norm.rfind('-'))
            s_norm = s_norm[:16] + ":00" + s_norm[idx:]
        else:
            s_norm = s_norm + ":00"

    # Accept both 'T' and space
    s_norm = s_norm.replace(" ", "T", 1)

    try:
        return datetime.fromisoformat(s_norm)
    except ValueError:
        return None


def _first_match_formats(s: str) -> datetime | None:
    for fmt in _CANDIDATE_INPUT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


class DateTransformer(BaseTransformerAPP[TransformerConfig]):
    def __init__(self):
        super().__init__()

    def transform(self, value: str) -> str:
        """
           Detect the input date/datetime string format and return it as '%Y-%m-%d %H:%M:%S'.

           Rules:
           - Supports many common date/time formats (YYYY-MM-DD, DD.MM.YYYY, slashed variants, with/without time).
           - Supports ISO8601 (with 'T', fractional seconds, 'Z' or ±HH:MM offsets).
           - Supports Unix timestamps (seconds, milliseconds, or float seconds).
           - If the parsed datetime is timezone-aware, it is first converted to UTC, then formatted (no timezone in output).
           - If the parsed datetime is naive (no timezone), it's treated as-is (no implicit timezone shift).
           - If only a date is provided, time defaults to 00:00:00.

           Args:
               value: input string representing a date/datetime.

           Returns:
               str in the fixed format '%Y-%m-%d %H:%M:%S'.

           Raises:
               ValueError if the string cannot be parsed.
           """
        if not isinstance(value, str):
            raise ValueError("Input must be a string.")

        s = value.strip()
        if not s:
            raise ValueError("Empty datetime string.")

        # 1) Try Unix timestamps
        dt = _parse_unix_timestamp(s)
        if dt is not None:
            # dt is aware (UTC)
            return dt.astimezone(timezone.utc).strftime(FIXED_OUT_FMT)

        # 2) Try explicit common formats
        dt = _first_match_formats(s)
        if dt is not None:
            # naive -> leave as-is
            return dt.strftime(FIXED_OUT_FMT)

        # 3) Try ISO-like parsing
        #    (Accept plain 'YYYY-MM-DDTHH:MM[:SS[.fff]][Z|±HH:MM]' or with space)
        if _iso_fraction_rx.match(s) or _iso_no_seconds_rx.match(s) or "T" in s or re.match(
                r"^\d{4}-\d{2}-\d{2}$", s):
            dt = _parse_iso_like(s)
            if dt is not None:
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc)
                return dt.replace(tzinfo=None).strftime(FIXED_OUT_FMT)

        # 4) Last-chance: try a few flexible tweaks (e.g., replace '.' with '-' and retry)
        tweaked = s.replace(".", "-").replace("/", "-")
        if tweaked != s:
            dt = _first_match_formats(tweaked)
            if dt is not None:
                return dt.strftime(FIXED_OUT_FMT)

        raise ValueError(f"Could not parse datetime string: {value}")
