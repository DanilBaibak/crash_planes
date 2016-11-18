#! /usr/bin/env python

"""
Initial code for working with data from PlaneCrashInfo.com.

More to come...
"""

import re

import numpy as np
import pandas as pd


# database cleaning

US_STATES = [
    ('AL', 'Alabama'),
    ('AK', 'Alaska'),
    ('AZ', 'Arizona'),
    ('AR', 'Arkansas'),
    ('CA', 'California'),
    ('CO', 'Colorado'),
    ('CT', 'Connecticut'),
    ('DE', 'Delaware'),
    ('DC', 'District Of Columbia'),
    ('FL', 'Florida'),
    ('GA', 'Georgia'),
    ('HI', 'Hawaii'),
    ('ID', 'Idaho'),
    ('IL', 'Illinois'),
    ('IN', 'Indiana'),
    ('IA', 'Iowa'),
    ('KS', 'Kansas'),
    ('KY', 'Kentucky'),
    ('LA', 'Louisiana'),
    ('ME', 'Maine'),
    ('MD', 'Maryland'),
    ('MA', 'Massachusetts'),
    ('MI', 'Michigan'),
    ('MN', 'Minnesota'),
    ('MS', 'Mississippi'),
    ('MO', 'Missouri'),
    ('MT', 'Montana'),
    ('NE', 'Nebraska'),
    ('NV', 'Nevada'),
    ('NH', 'New Hampshire'),
    ('NJ', 'New Jersey'),
    ('NM', 'New Mexico'),
    ('NY', 'New York'),
    ('NC', 'North Carolina'),
    ('ND', 'North Dakota'),
    ('OH', 'Ohio'),
    ('OK', 'Oklahoma'),
    ('OR', 'Oregon'),
    ('PA', 'Pennsylvania'),
    ('RI', 'Rhode Island'),
    ('SC', 'South Carolina'),
    ('SD', 'South Dakota'),
    ('TN', 'Tennessee'),
    ('TX', 'Texas'),
    ('UT', 'Utah'),
    ('VT', 'Vermont'),
    ('VA', 'Virginia'),
    ('WA', 'Washington'),
    ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'),
    ('WY', 'Wyoming')
]

US_STATES_FLAT = [entry[0] for entry in US_STATES] + [entry[1] for entry in US_STATES]


def clean_location(location):
    """
    Clean locations

    :param location:
    :return:
    """

    if type(location) != str:
        return np.nan

    # clean outliers
    outliers = ['Over', 'Over', 'Near', 'Off', 'off', 'Territory of', 'South of', 'the', 'coast']
    for outlier in outliers:
        location = location.replace(outlier, '').strip()

    # clean typos
    typos = [
        ('United States', 'USA'), ('Unied Kingdom', 'United Kingdom'), ('UK', 'United Kingdom'),
        ('United States', 'USA'), ('Russian', 'Russia'), ('Irkutsk Russia', 'Russia'),
        ('Washington DC', 'Washington'), ('Washington D.C.', 'Washington'), ('Washingon', 'Washington'),
        ('Minnisota', 'Minnesota'),
    ]
    for search, replace in typos:
        location = location.replace(search, replace)

    return location


def country_of_loc(location):
    """
    Get country of given location.

    E.g. 'St. Moritz, Switzerland' -> 'Switzerland' or
    'Jackson, Mississippi' -> 'USA'
    """
    if type(location) != str:
        return '?'

    country = location.split(',')[-1].strip()
    if country in US_STATES_FLAT:
        country = 'USA'

    return country


def int_or_nan(x):
    try:
        x = int(x)
    except ValueError:
        x = np.nan
    return x


def split_fatalities(entry):
    """
    Split 'Fatalities' entry into dictionary.

    '?' are converted to np.nan. Counts should be ints, not floats...

    E.g. '15 (passengers:13 crew:2)' 
      -> {'total':15, 'passengers':13, 'crew':2}.
    """
    names = 'total passengers crew'.split()
    counts = re.findall('(\?|\d+)', entry)
    counts = [int_or_nan(c) for c in counts]
    return dict(list(zip(names, counts)))


def get_accident_type(df):
    """
    Try to recognize type of the accident
    :param df:
    :return:
    """
    accident_type = ''
    accidents_type = []

    # unfortunately data is quite dirty
    for (location, origin, destination) in df[['Location', 'Origin', 'Destination']].values:
        if location is np.NaN or origin is np.NaN or destination is np.NaN:
            # unknown
            accident_type = 0
        elif location == origin or location in origin or origin in location:
            # take-off
            accident_type = 1
        elif location == destination or location in destination or destination in location:
            # landing
            accident_type = 2
        else:
            # others
            accident_type = 3

        accidents_type.append(accident_type)

    return accidents_type


def clean_database(df):
    """Return copy of database after cleaning."""

    dfc = df.copy()

    # drop useless columns
    dfc = dfc.drop(['Unnamed: 0', 'Unnamed: 0.1', 'Registration:', 'Flight #:', 'cn / ln:'], axis=1)

    # remove trailing ':' in index/column names
    dfc = dfc.rename(columns={cn: cn[:-1] for cn in list(dfc.columns)})

    # replace all '?' values with NaN
    dfc.replace(to_replace='?', value=np.nan, inplace=True)

    # make datetimeindex from date/time fields
    dfc = dfc.set_index(pd.DatetimeIndex(dfc['Date']))
    dfc.sort_index(inplace=True)
    dfc = dfc.drop(['Date'], axis=1)

    # split route field into origin/destination
    values = dfc.Route.values
    dfc['Origin'] = [v.split(' - ')[0] if type(v) != float else np.nan for v in values]
    dfc['Destination'] = [v.split(' - ')[-1] if type(v) != float else np.nan for v in values]

    # split fatalities field
    dfc['Fatalities_total'] = dfc['Fatalities'].apply(lambda x: split_fatalities(x)['total'])

    # make Ground field numeric (or nan)
    dfc['Ground'] = dfc['Ground'].apply(pd.to_numeric)

    # cleaning
    dfc['Location'] = dfc['Location'].apply(lambda x: clean_location(x))

    # add country field extracted from accident location
    dfc['Location_Country'] = dfc['Location'].apply(lambda x: country_of_loc(x))

    dfc.rename(columns={'AC  Type': 'AC_Type'}, inplace=True)

    # add type of the accident
    dfc['Accident_type'] = get_accident_type(dfc)

    return dfc
