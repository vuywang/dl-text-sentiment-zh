from datetime import datetime


def now_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")
