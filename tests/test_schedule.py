from datetime import date

from app.schedule import (
    build_month_schedule_message,
    build_next_status_message,
    build_test_message,
    build_today_status_message,
    build_wear_reminder_message,
    is_wear_day,
    next_wear_date,
    wear_date_for_week,
    wear_dates_for_month,
)


EXPECTED_2026 = {
    1: ["07/01", "16/01", "20/01", "29/01"],
    2: ["02/02", "11/02", "20/02", "24/02"],
    3: ["03/03", "12/03", "16/03", "25/03"],
    4: ["03/04", "07/04", "16/04", "20/04", "29/04"],
    5: ["04/05", "13/05", "22/05", "26/05"],
    6: ["04/06", "08/06", "17/06", "26/06", "30/06"],
    7: ["10/07", "14/07", "23/07", "27/07"],
    8: ["05/08", "14/08", "18/08", "27/08", "31/08"],
    9: ["09/09", "18/09", "22/09"],
    10: ["01/10", "06/10", "15/10", "19/10", "28/10"],
    11: ["06/11", "10/11", "19/11", "23/11"],
    12: ["02/12", "07/12", "16/12", "25/12", "29/12"],
}


def test_generated_2026_schedule_matches_expected_dates():
    actual = {month: [] for month in range(1, 13)}

    for month in range(1, 13):
        for day in range(1, 32):
            try:
                candidate = date(2026, month, day)
            except ValueError:
                continue

            if is_wear_day(candidate):
                actual[month].append(candidate.strftime("%d/%m"))

    assert actual == EXPECTED_2026


def test_prompt_example_week_maps_result_one_to_tuesday():
    monday = date(2025, 7, 28)

    assert (monday.year + monday.month + monday.day) % 5 == 0
    assert wear_date_for_week(monday) == monday


def test_next_wear_date_can_include_today():
    assert next_wear_date(date(2026, 1, 7), include_today=True) == date(2026, 1, 7)


def test_next_wear_date_can_skip_today():
    assert next_wear_date(date(2026, 1, 7), include_today=False) == date(2026, 1, 16)


def test_wear_dates_for_month_matches_january_2026():
    assert [wear_date.strftime("%d/%m") for wear_date in wear_dates_for_month(2026, 1)] == [
        "07/01",
        "16/01",
        "20/01",
        "29/01",
    ]


def test_messages_use_readable_vietnamese_formatting():
    assert (
        build_wear_reminder_message(date(2026, 1, 7))
        == "Nhắc lịch mặc áo\n"
        "Hôm nay 07/01/2026 (thứ 4) là ngày mặc áo theo quy định."
    )
    assert build_today_status_message(date(2026, 1, 7)) == (
        "Hôm nay mặc áo\n"
        "Ngày: 07/01/2026 (thứ 4)"
    )
    assert build_today_status_message(date(2026, 1, 8)) == (
        "Hôm nay không phải ngày mặc áo\n"
        "Ngày: 08/01/2026 (thứ 5)\n"
        "Ngày mặc tiếp theo: 16/01/2026 (thứ 6)"
    )
    assert (
        build_next_status_message(date(2026, 1, 8))
        == "Ngày mặc áo tiếp theo\n"
        "16/01/2026 (thứ 6)"
    )


def test_schedule_and_test_messages_use_readable_vietnamese_formatting():
    assert build_month_schedule_message(date(2026, 1, 8)) == (
        "Lịch mặc áo tháng 01/2026\n"
        "- 07/01 (thứ 4)\n"
        "- 16/01 (thứ 6)\n"
        "- 20/01 (thứ 3)\n"
        "- 29/01 (thứ 5)"
    )
    assert build_test_message() == (
        "Test bot thành công\n"
        "Bot đã gửi được tin nhắn production."
    )
