import random
import datetime
from datatypes import Datetime

from ..base import TestData


type Now = datetime.datetime|datetime.date|int|float|datetime.timedelta|None


###############################################################################
# testdata functions
###############################################################################
class DatetimeData(TestData):
    def get_timestamp(
        self,
        now: Now = None,
        as_int: bool = False,
        ndigits: int = 6,
        **kwargs,
    ) -> int|float:
        """Get a unix epoch timestamp for `now`

        :param as_int: if True then return the timestamp with `ndigits` of
            magnitude in int form
        :param ndigits: how many subseconds wanted
            0 - none
            3 - millisecond precision
            6 - microsecond precision
            9 - nanosecond precision
        """
        now = self.get_datetime(now)
        return now.as_integer(ndigits) if as_int else now.timestamp()

    def get_datetime(
        self,
        now:Now = None,
        *args,
        **kwargs,
    ) -> Datetime:
        """Return a `datetime` instance

        see `datatypes.datetime.Datetime` since this is basically just a
        passthrough to that
        """
        return Datetime(now, *args, **kwargs)

    def get_birthday(
        self,
        as_str: bool = False,
        start_age: bool = 18,
        stop_age: bool = 100,
    ) -> datetime.date|str:
        """Return a random YYYY-MM-DD

        :param as_str: boolean, true to return the bday as a YYYY-MM-DD string
        :param start_age: int, minimum age of the birthday date
        :param stop_age: int, maximum age of the birthday date
        :returns: datetime.date|string
        """
        age = random.randint(start_age, stop_age)
        year = (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(weeks=(age * 52))
        ).year
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

    def get_past_datetime(
        self,
        now: Now = None,
    ) -> Datetime:
        """return a datetime guaranteed to be in the past from now"""
        now = self.get_datetime(now)
        td = now - datetime.datetime(
            year=1970,
            month=1,
            day=1,
            tzinfo=now.tzinfo,
        )
        return now - datetime.timedelta(
            days=random.randint(1, max(td.days, 1)),
            seconds=random.randint(1, max(td.seconds, 1))
        )
    get_past_dt = get_past_datetime
    get_passed_datetime = get_past_datetime
    get_before_datetime = get_past_datetime
    get_past_date_time = get_past_datetime

    def get_past_date(self, now: Now = None) -> datetime.date:
        """return a date guaranteed to be in the past from now"""
        return self.get_past_datetime(now).date()
    get_passed_date = get_past_date
    get_before_date = get_past_date

    def get_future_datetime(self, now: Now = None) -> Datetime:
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
        """Get a date guarranteed to be in the future from `now`"""
        return self.get_future_datetime(now).date()

    def get_between_datetime(self, start: Now, stop: Now = None) -> Datetime:
        """get a datetime between start and stop

        return a datetime guaranteed to be in the future from start and in the
        past from stop

        :param start: the datetime in the past
        :param stop: the future datetime, defaults to now
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

    def get_between_date(self, start: Now, stop: Now = None) -> datetime.date:
        return self.get_between_datetime(start, stop).date()

