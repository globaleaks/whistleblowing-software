import calendar

from datetime import datetime, timedelta


def backup_name(version, id, timestamp):
    backup_date = datetime.fromtimestamp(timestamp).strftime("%Y_%m_%d")
    return "%s_%s_%d_%s.tar.gz" % (backup_date, id, timestamp, version)


def backup_type(date):
    daily = True
    weekly = False
    monthly = False

    last_day_of_month = calendar.monthrange(date.year, date.month)[1]

    if date.weekday() == 6:
        weekly = True

    if date.day == last_day_of_month:
        monthly = True

    return daily, weekly, monthly


def get_records_to_delete(d, w, m, records):
    ret = []

    daily_count = weekly_count = monthly_count = 0

    today = datetime.today()

    for record in records:
        to_delete = True

        if not record.delete:
            b_t = backup_type(record.creation_date)

            date = record.creation_date

            if b_t[2] and monthly_count < m and date > (today - timedelta(days=d + 1) * 30):
                monthly_count += 1
                to_delete = False

            if b_t[1] and weekly_count < w and date > (today - timedelta(days=(w + 1) * 7)):
                weekly_count += 1
                to_delete = False

            if daily_count < d and date > (today - timedelta(days=(d + 1))):
                daily_count += 1
                to_delete = False

        if to_delete:
            ret.append(record)

    return ret
