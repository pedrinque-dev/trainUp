from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

TZ = ZoneInfo(settings.TIMEZONE)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def local_date(dt: datetime) -> date:
    return dt.astimezone(TZ).date()


def today_local() -> date:
    return local_date(now_utc())


def local_to_utc(d: date, hour: int = 0, minute: int = 0) -> datetime:
    return datetime.combine(d, time(hour, minute), tzinfo=TZ).astimezone(timezone.utc)


def day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    start = local_to_utc(d)
    return start, local_to_utc(d + timedelta(days=1))


def fmt_local(dt: datetime, pattern: str = "%d/%m %H:%M") -> str:
    return dt.astimezone(TZ).strftime(pattern)
