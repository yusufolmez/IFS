from datetime import date, datetime, timedelta

def calculate_total_working_days(start_date, end_date):

    public_holidays = [
        date(2025,1,1),
        date(2025,3,29),
        date(2025,3,30),
        date(2025,3,31),
        date(2025,4,23),
        date(2025,5,1),
        date(2025,5,19),
        date(2025,6,5),
        date(2025,6,6),
        date(2025,6,7),
        date(2025,6,8),
        date(2025,6,9),
        date(2025,7,15),
        date(2025,8,30),
        date(2025,9,28),
        date(2025,9,29),
        date(2025,12,31),
    ]
    weekdays_count = 0

    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5 and current_date not in public_holidays: 
            weekdays_count += 1
        current_date += timedelta(days=1)

    return weekdays_count