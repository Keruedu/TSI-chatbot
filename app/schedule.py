import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


VN_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
WEEKDAY_NAMES = {
    0: "thứ 2",
    1: "thứ 3",
    2: "thứ 4",
    3: "thứ 5",
    4: "thứ 6",
    5: "thứ 7",
    6: "chủ nhật",
}


def today_vietnam() -> date:
    return datetime.now(VN_TIMEZONE).date()


def parse_iso_date(raw_date: str) -> date:
    return date.fromisoformat(raw_date)


def monday_of_week(target_date: date) -> date:
    return target_date - timedelta(days=target_date.weekday())


def wear_date_for_week(target_date: date) -> date:
    monday = monday_of_week(target_date)
    offset = (monday.year + monday.month + monday.day) % 5
    return monday + timedelta(days=offset)


def is_wear_day(target_date: date) -> bool:
    return wear_date_for_week(target_date) == target_date


def next_wear_date(from_date: date, include_today: bool = True) -> date:
    cursor = from_date if include_today else from_date + timedelta(days=1)
    for day_offset in range(14):
        candidate = cursor + timedelta(days=day_offset)
        if is_wear_day(candidate):
            return candidate

    raise RuntimeError("Could not find the next wear date within two weeks.")


def format_date(target_date: date) -> str:
    return target_date.strftime("%d/%m/%Y")


def format_weekday(target_date: date) -> str:
    return WEEKDAY_NAMES[target_date.weekday()]


def format_short_date(target_date: date) -> str:
    return target_date.strftime("%d/%m")


def wear_dates_for_month(year: int, month: int) -> list[date]:
    _, days_in_month = calendar.monthrange(year, month)
    wear_dates: list[date] = []

    for day in range(1, days_in_month + 1):
        candidate = date(year, month, day)
        if is_wear_day(candidate):
            wear_dates.append(candidate)

    return wear_dates


def build_wear_reminder_message(target_date: date) -> str:
    return "\n".join(
        [
            "Nhắc lịch mặc áo",
            (
                f"Hôm nay {format_date(target_date)} ({format_weekday(target_date)}) "
                "là ngày mặc áo theo quy định."
            ),
        ]
    )


def build_today_status_message(target_date: date) -> str:
    if is_wear_day(target_date):
        return "\n".join(
            [
                "Hôm nay mặc áo",
                f"Ngày: {format_date(target_date)} ({format_weekday(target_date)})",
            ]
        )

    next_date = next_wear_date(target_date, include_today=False)
    return "\n".join(
        [
            "Hôm nay không phải ngày mặc áo",
            f"Ngày: {format_date(target_date)} ({format_weekday(target_date)})",
            f"Ngày mặc tiếp theo: {format_date(next_date)} ({format_weekday(next_date)})",
        ]
    )


def build_next_status_message(target_date: date) -> str:
    next_date = next_wear_date(target_date, include_today=True)
    return "\n".join(
        [
            "Ngày mặc áo tiếp theo",
            f"{format_date(next_date)} ({format_weekday(next_date)})",
        ]
    )


def build_month_schedule_message(target_date: date) -> str:
    wear_dates = wear_dates_for_month(target_date.year, target_date.month)
    lines = [f"Lịch mặc áo tháng {target_date:%m/%Y}"]

    if not wear_dates:
        lines.append("- Không có ngày mặc áo trong tháng này.")
    else:
        lines.extend(
            f"- {format_short_date(wear_date)} ({format_weekday(wear_date)})"
            for wear_date in wear_dates
        )

    return "\n".join(lines)


def build_test_message() -> str:
    return "\n".join(
        [
            "Test bot thành công",
            "Bot đã gửi được tin nhắn production.",
        ]
    )
