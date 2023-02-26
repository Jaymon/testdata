# -*- coding: utf-8 -*-
import random
import datetime

from ..base import TestData


###############################################################################
# testdata functions
###############################################################################
class DatetimeData(TestData):
    def get_datetime(self, now=None, backward=False, **kwargs):
        """get a datetime

        :param now: datetime|date|int|float|timedelta
            datetime - just returned
            date - returned as a datetime
            int - assumed to be days and will be added/subtracted from utc now
            float - assumed to be seconds and will be added/subtracted from utc now
            timedelta - will be add/subtracted from utc now
        :param backward: if True, then a positive int, float, or timedelta will be
            subtracted from utc now, if False then it will be added
        :param **kwargs: these will be passed to timedelta
        :returns: datetime
        """
        if not now and kwargs:
            now = datetime.timedelta(**kwargs)

        if now:
            if isinstance(now, datetime.datetime):
                pass

            elif isinstance(now, datetime.timedelta):
                seconds = now.total_seconds()
                microseconds = (seconds * 1000000) % 1000000
                if backward and seconds > 0:
                    seconds *= -1.0

                td = datetime.timedelta(seconds=seconds, microseconds=microseconds)
                now = datetime.datetime.utcnow() + td

            elif isinstance(now, datetime.date):
                now = datetime.datetime(now.year, now.month, now.day)

            elif isinstance(now, int):
                if backward and now > 0:
                    now *= -1.0
                now = datetime.datetime.utcnow() + datetime.timedelta(days=now)

            elif isinstance(now, float):
                seconds = int(now)
                microseconds = (now * 1000000) % 1000000
                if backward and seconds > 0:
                    seconds *= -1.0
                td = datetime.timedelta(seconds=now, microseconds=microseconds)
                now = datetime.datetime.utcnow() + td

            else:
                raise ValueError("Unknown value: {}".format(now))

        else:
            now = datetime.datetime.utcnow()

        return now

    def get_birthday(self, as_str=False, start_age=18, stop_age=100):
        """
        return a random YYYY-MM-DD

        :param as_str: boolean, true to return the bday as a YYYY-MM-DD string
        :param start_age: int, minimum age of the birthday date
        :param stop_age: int, maximum age of the birthday date
        :returns: datetime.date|string
        """
        age = random.randint(start_age, stop_age)
        year = (datetime.datetime.utcnow() - datetime.timedelta(weeks=(age * 52))).year
        month = random.randint(1, 12)
        if month == 2:
            day = random.randint(1, 28)
        elif month in [9, 4, 6, 11]:
            day = random.randint(1, 30)
        else:
            day = random.randint(1, 31)

        bday = datetime.date(year, month, day)
        if as_str:
            bday = "{:%Y-%m-%d}".format(bday)

        return bday
    get_bday = get_birthday

    def get_past_datetime(self, now=None):
        """return a datetime guaranteed to be in the past from now"""
        now = self.get_datetime(now, backward=True)
        td = now - datetime.datetime(year=2000, month=1, day=1)
        return now - datetime.timedelta(
            days=random.randint(1, max(td.days, 1)),
            seconds=random.randint(1, max(td.seconds, 1))
        )
    get_past_dt = get_past_datetime
    get_passed_datetime = get_past_datetime
    get_before_datetime = get_past_datetime
    get_past_date_time = get_past_datetime

    def get_past_date(self, now=None):
        dt = self.get_past_datetime(now)
        return datetime.date(dt.year, dt.month, dt.day)
    get_passed_date = get_past_date
    get_before_date = get_past_date

    def get_future_datetime(self, now=None):
        """return a datetime guaranteed to be in the future from now"""
        now = self.get_datetime(now)
        return now + datetime.timedelta(
            weeks=random.randint(1, 52 * 50),
            hours=random.randint(0, 24),
            days=random.randint(0, 365),
            seconds=random.randint(0, 86400)
        )
    get_future_dt = get_future_datetime
    get_after_dt = get_future_datetime
    get_after_date_time = get_future_datetime
    get_future_date_time = get_future_datetime

    def get_future_date(self, now=None):
        dt = self.get_future_datetime(now)
        return datetime.date(dt.year, dt.month, dt.day)

    def get_between_datetime(self, start, stop=None):
        """get a datetime between start and stop

        return a datetime guaranteed to be in the future from start and in the past from stop
        """
        start = self.get_datetime(start)
        stop = self.get_datetime(stop)

        if start >= stop:
            raise ValueError("start datetime >= stop datetime")

        td = stop - start

        kwargs = {}
        if td.days > 0:
            kwargs["days"] = random.randint(0, td.days)

        if td.seconds - 1 > 0:
            kwargs["seconds"] = random.randint(0, td.seconds - 1)

        if td.microseconds - 1 > 0:
            kwargs["microseconds"] = random.randint(0, td.microseconds - 1)

        return start + datetime.timedelta(**kwargs)
    get_between_dt = get_between_datetime
    get_between_date_time = get_between_datetime

    def get_between_date(self, start, stop=None):
        dt = self.get_between_datetime(start, stop)
        return datetime.date(dt.year, dt.month, dt.day)

