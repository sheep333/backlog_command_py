from datetime import datetime, timedelta


def datetimefilter(value, fmt="%Y-%m-%d %H:%M:%S"):
    if not value:
        return ""
    dt = datetime.fromisoformat(value[:-1])
    local_dt = dt + timedelta(hours=9)
    return datetime.strftime(local_dt, fmt)


def datefilter(value, fmt="%Y-%m-%d"):
    if not value:
        return ""

    dt = datetime.fromisoformat(value[:-1])
    return dt.strftime(fmt)
