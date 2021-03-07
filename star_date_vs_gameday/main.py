# intent is to convert star date to game day integer and back again.
# could be some incorrect answers around start / end of years (week 53 becoming week 1 etc)

import datetime
from dateutil.rrule import *
DAY_ZERO = datetime.date(2001, 12, 24)


def get_star_date_from_game_day(game_day):
    #  take a game day integer, calculate and return the star date
    day_new = rrule(DAILY, byweekday=(MO, TU, WE, TH, FR), dtstart=DAY_ZERO)[game_day]
    sd_year = day_new.year - 1800
    sd_week = day_new.isocalendar()[1]
    sd_day = day_new.isocalendar()[2]
    star_date = '{y}.{w}.{d}'.format(y=sd_year, w=sd_week, d=sd_day)
    return star_date


def get_game_day_from_star_date(sd):
    # take a star_date with format 'year.week.day', calculate and return the game_day integer
    # get the date from star_date, then count how many work days that date after DAY_ZERO
    sd_year = int(sd.split('.')[0]) + 1800
    sd_week = int(sd.split('.')[1])
    sd_day = int(sd.split('.')[2])
    new_date = datetime.date.fromisocalendar(sd_year, sd_week, sd_day)
    game_day = rrule(DAILY, byweekday=(MO, TU, WE, TH, FR), dtstart=DAY_ZERO, until=new_date).count() -1
    return game_day


if __name__ == '__main__':
    test_sd = '221.1.1'
    x = get_game_day_from_star_date(test_sd)
    print(x)

    # test_game_day = 4964
    # x = get_star_date_from_game_day(test_game_day)
    # print(x)

