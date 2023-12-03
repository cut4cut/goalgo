from datetime import date, datetime, timedelta

MOS_TZ = timedelta(hours=3)


def nowday_mostz() -> date:
    # Moscow TZ for any local time
    dt = datetime.utcnow() + MOS_TZ
    return date(dt.year, dt.month, dt.day)


def now_dt_mostz() -> datetime:
    # Moscow TZ for any local time
    return datetime.utcnow() + MOS_TZ
