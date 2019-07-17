#!/usr/bin/env python
"""
meter_db
--------

NOTE: this is a copy taken from the Analysis repository.
It was moved here to avoid loading external modules in email_confirmation.py, when it runs on the server.
Using sys.path.append does not work with relative paths for cron jobs


A module for interaction with the Meter Database

This module superseeds meter.py and queries.py

For meter.py use meter_tools.py

"""

"""
Content
^^^^^^^

> _DB_connection
Establish connection and cursor

> _Query_functions
Standard methods to retrieve data or execute SQL statements

> _Queries
Wrappers for common and generic SQL queries

> _connectDB
Create connection on import

> _time_budget
"""

import MySQLdb.cursors
from sqlalchemy import create_engine    # fix for pandas sql connections
import pandas as pd
import datetime as dt
from subprocess import call

import interface_ini as db     # reads the database and file path information


""" _DB_connection """


def connectDB():
    """ use db credentials for MySQLdb """
    global dbConnection
    try:
        dbConnection = MySQLdb.connect(
            host=db.Host,
            user=db.User,
            passwd=db.Pass,
            db=db.Name,
            cursorclass=MySQLdb.cursors.DictCursor)
    except:
        db.Host = 'localhost'
        dbConnection = MySQLdb.connect(
            host=db.Host,
            user=db.User,
            passwd=db.Pass,
            db=db.Name,
            cursorclass=MySQLdb.cursors.DictCursor)
    cursor = dbConnection.cursor()
    return cursor


def connectPandasDatabase():
    """ Required connection for data frame operations """
    engine = create_engine("mysql+mysqldb://{}:{}@{}/{}".format(db.User, db.Pass, db.Host, db.Name))
    return engine


"""
_Query_functions
"""


def getHost():
    return db.Host


def getConnection():
    return dbConnection


def getDataframeSQL(sqlq):
    """ takes  query and returns results as a dataframe """
    df = pd.read_sql(sqlq, con=dbConnection)
    return df


def commit():
    global dbConnection
    dbConnection.commit()


def toggleDatabase():
    """ switch between remote and local db """
    global cursor
    if (db.Host == 'localhost'):
        db.Host = '109.74.196.205'
    else:
        db.Host = 'localhost'
    cursor = connectDB()


def backup_database():
    """
    dump sql in local dated file
    """
    dateTimeToday = dt.datetime.now()
    thisDate = dateTimeToday.strftime("%Y_%m_%d")
    call('mysqldump -u ' + db.User + ' -h ' + db.Host + ' -p --databases ' + db.Name +
         ' > ' + './Data/database/' + thisDate + '_' + db.Name + '.sql', shell=True)
    return 'Database backed up as ' + thisDate + '_' + db.Name + '.sql'


def executeSQL(_sqlq):
    """
    For queries that do not return data, such as INSERT
    with safeguard against dropped connections
    Returns: ID of entry
    """
    global cursor
    try:
        cursor.execute(_sqlq)
    except:
        cursor = connectDB()
        cursor.execute(_sqlq)
    return cursor.lastrowid


def getSQL(_sqlq):
    """
    For queries that return data, such as SELECT.
    with safeguard against dropped connections
    If only the first entry is wanted, use::

        g:return column etSQL(query)[0]

    :param str _sqlq: SQL query string
    :return: dict fetchall(): SQL result
    """
    global cursor
    try:
        cursor.execute(_sqlq)
    except:
        cursor = connectDB()
        cursor.execute(_sqlq)
    return cursor.fetchall()

def getTable(table):
    """
    :returns: full table as DataFrame
    """
    sqlq = "SELECT * FROM {}".format(table)
    return getDataframeSQL(sqlq)


def getContact(hhID):
    """
    return contactID for given household
    """
    sqlq = "SELECT Contact_idContact FROM Household WHERE idHousehold = '%s';" % hhID
    if (getSQL(sqlq)):
        result = getSQL(sqlq)[0]
        return "{}".format(result['Contact_idContact'])
    else:
        return '0'


def getNameOfContact(cID):
    """ get Contact name for a given Contact """
    sqlq = """
        SELECT Name,Surname
        FROM Contact
        WHERE idContact = '{}';
        """.format(cID)
    result = getSQL(sqlq)[0]
    return "{} {}".format(result['Name'], result['Surname'])


def getSecurityCode(hhID):
    """ get the security code for this household """
    sqlq = """
        SELECT security_code
        FROM Household
        WHERE idHousehold = '{}';
        """.format(hhID)
    result = getSQL(sqlq)[0]
    return "{}".format(result['security_code'])


def householdExists(hhID):
    """ true if record is found """
    sqlq = "SELECT * FROM Household WHERE idHousehold = %s;" % hhID
    if (getSQL(sqlq)):
        return True
    else:
        return False

def getParticipantCount(householdID):
    """ get number of diaries required """
    sqlq = "SELECT age_group2, age_group3, age_group4, age_group5, age_group6\
            FROM Household \
            WHERE idHousehold = '" + householdID + "';"
    result = getSQL(sqlq)[0]
    return int(result['age_group2']) + int(result['age_group3']) + int(result['age_group4']) + int(result['age_group5']) + int(result['age_group6'])

def getHouseholdForMeta(_metaID):
    """ find the one match of HH for this metaID """
    sqlq = "SELECT Household_idHousehold FROM Meta WHERE idMeta = %s;" % _metaID
    if (getSQL(sqlq)):
        result = getSQL(sqlq)[0]
        return ("%s" % result['Household_idHousehold'])
    else:
        return '0'

def getElMetaForHH(idHH):
    """
    :returns: idMeta for the electricity readings of this HH
    """
    sqlq = """
        SELECT idMeta
            FROM Meta
            WHERE Household_idHousehold = {}
            AND DataType = 'E';
        """.format(idHH)
    if (getSQL(sqlq)):
        result = getSQL(sqlq)[0]
        return result['idMeta']
    else:
        # no e readings exist for this HH
        return False

def getHHdtChoice(hhID):
    """ reads a sql date in format "2016-12-31" and returns datetime object """
    sqlq = """
            SELECT date_choice 
            FROM Household 
            WHERE idHousehold = '{}';
            """.format(hhID)
    result = getSQL(sqlq)[0]
    dateStr = ("%s" % result['date_choice'])
    if (dateStr != 'None'):
        f = '%Y-%m-%d'
        return dt.datetime.strptime(dateStr, f)
    else:
        return "None"

def getDateChoice(hhID):
    """ return collection date as a string: "Sun, 31 Dec" """
    this_dt = getHHdtChoice(hhID)
    if (this_dt != 'None'):
        return this_dt.strftime("%a, %-d %b")
    else:
        return "None"

def getStatus(householdID):
    """ get the status for this household """
    sqlq = "SELECT status FROM Household WHERE idHousehold = '%s';" % householdID
    result = getSQL(sqlq)[0]
    return ("%s" % result['status'])

def setStatus(householdID,status):
    """ set the status for this household """
    sqlq = "UPDATE Household SET status = '{}' WHERE idHousehold = '{}';".format(status, householdID)
    executeSQL(sqlq)
    commit()

def getDateTimeFormated(dts):
    """ XXX THIS SHOULD BE in meter_tools only
    DateTimeString as received from database: return 31 Jan 16 """
    # http://strftime.org/
    if (dts != 'None'):
        f = '%Y-%m-%d %H:%M:%S'
        this_dt = dt.datetime.strptime(dts, f)
        return this_dt.strftime("%-d %b %y")
    else:
        return "None"


"""

> _Queries

"""

def getElectricity(idRecording):
    sqlq = """
        SELECT *
        FROM Electricity
        WHERE Meta_idMeta={};
        """.format(idRecording)
    return getDataframeSQL(sqlq)


def getElectricityRecording(time_inc=''):
    """
    Returns set of idMeta values
    """
    sqlq = """
        SELECT DISTINCT(Meta_idMeta)
        FROM Electricity{};
        """.format(time_inc)
    return getDataframeSQL(sqlq)


def getAllGoodElectricityRecording(timescale):
    """
    Returns dataframe with idHH, idMeta, t, and Watt as columns
    """
    sqlq = """
        SELECT M.Household_idHousehold as idHH, M.idMeta as idMeta, dt as t, Watt as Watt
        FROM {} as E
        JOIN Meta as M
        ON E.Meta_idMeta = M.idMeta
        WHERE M.Quality = 1;
        """
    table = 'Electricity_1min'
    if (timescale == 'sec'):
        table = 'Electricity'
    elif (timescale == '10min'):
        table = 'Electricity_10min'
    sqlq = sqlq.format(table)
    return getDataframeSQL(sqlq)


def getHousehold_p2a(average_over_all = False):
    """
        :param average_over_all: if False (default), the normalising
        value is the average ONLY non-peak hours. If True, the normalising
        value is the average over ALL the hours.
        :return dataframe: list of idHousehold and peak2avg values
        :return peak2avg: peak time (5-7pm) Watt values divided by average use for all other hours
    """
    sqlq = """
    SELECT (pWatt / aWatt) AS peak2avg, pWatt AS peakWatt, pHH AS idHousehold
        FROM (
            SELECT AVG(Watt) AS pWatt, Household_idHousehold AS pHH
            FROM hh_el_hour
            WHERE HOUR(dt) BETWEEN 17 AND 19
            GROUP BY Household_idHousehold
        ) AS peakLoad
    JOIN
        (
            SELECT AVG(Watt) AS aWatt, Household_idHousehold AS aHH
            FROM hh_el_hour
            {0}
            GROUP BY Household_idHousehold
        ) AS avgLoad
    ON aHH = pHH
    ORDER BY peak2avg ASC;
    """
    spec = " "
    if not average_over_all:
        spec = " WHERE HOUR(dt) NOT BETWEEN 17 AND 19 "
    sqlq = sqlq.format(spec)
    return getDataframeSQL(sqlq)


def getHousehold_p2a_ppl(average_over_all = False):
    """
        :param average_over_all: if False (default), the normalising
        value is the average ONLY non-peak hours. If True, the normalising
        value is the average over ALL the hours.
        :return dataframe: list of idHousehold and peak2avg values
        :return peak2avg: peak time (5-7pm) Watt values divided by average use for all other hours
    """
    sqlq = """
    SELECT (pWatt / aWatt) AS peak2avg, pWatt AS peakWatt, pHH AS idHousehold,
    age_group1 as young, age_group2 as old,
    (age_group1 + age_group2 + age_group3 + age_group4 + age_group5 + age_group6) as people
        FROM (
            SELECT AVG(Watt) AS pWatt, Household_idHousehold AS pHH
            FROM hh_el_hour
            WHERE HOUR(dt) BETWEEN 17 AND 19
            GROUP BY Household_idHousehold
        ) AS peakLoad
    JOIN
        (
            SELECT AVG(Watt) AS aWatt, Household_idHousehold AS aHH
            FROM hh_el_hour
            {0}
            GROUP BY Household_idHousehold
        ) AS avgLoad
	JOIN Household as H
    ON aHH = pHH
    AND aHH = H.idHousehold
    ORDER BY peak2avg ASC;
    """
    spec = " "
    if not average_over_all:
        spec = " WHERE HOUR(dt) NOT BETWEEN 17 AND 19 "
    sqlq = sqlq.format(spec)
    return getDataframeSQL(sqlq)


def getHousehold_p2a_hh(average_over_all = False):
    """
        Returns a dataframe with ALL household info from the household table,
        and the peakWatt and peak2avg. Used for analysis of which household
        characteristics matter for peak2avg.
        :param average_over_all: if False (default), the normalising
        value is the average ONLY non-peak hours. If True, the normalising
        value is the average over ALL the hours.
    """
    sqlq = """
    SELECT (pWatt / aWatt) AS peak2avg, pWatt AS peakWatt, H.*
        FROM (
            SELECT AVG(Watt) AS pWatt, Household_idHousehold AS pHH
            FROM hh_el_hour
            WHERE HOUR(dt) BETWEEN 17 AND 19
            GROUP BY Household_idHousehold
        ) AS peakLoad
    JOIN
        (
            SELECT AVG(Watt) AS aWatt, Household_idHousehold AS aHH
            FROM hh_el_hour
            {0}
            GROUP BY Household_idHousehold
        ) AS avgLoad
	JOIN Household as H
    ON aHH = pHH
    AND aHH = H.idHousehold
    ORDER BY peak2avg ASC;
    """
    spec = " "
    if not average_over_all:
        spec = " WHERE HOUR(dt) NOT BETWEEN 17 AND 19 "
    sqlq = sqlq.format(spec)
    return getDataframeSQL(sqlq)

def getHouseholdTableEntryLegend(col_entry = 'age_group1'):
    """
    Returns dictionary indexed by household questions (i.e. those columns in the household
    table that have a 'q' entry in the associated legend table). The values are
    dictionaries themselves, with 'question' and 'meaning' as keys. 'question' gives the
    question that is asked of people. 'meaning' is either 'number', or a dictionary
    explicitly saying what the keys (i.e. entries in the household table) are.
    """
    #1. Get household legend info
    household_legend_query = """
    SELECT col, value, meaning FROM Legend WHERE tab = 'Household';
    """
    df = getDataframeSQL(household_legend_query)
    out = {}
    for a, b in df.groupby('col'): #bit of legend corresponding to that column, e.g. 'age_group1'. a is column, b is the corresponding chunk of the dataframe
        q = b['value'] == 'q' #if it's a question asked to the participants
        explanations = q == False
        if (len(b[q])):
            meaning = b[q]['meaning'].values[0] #arghh!!!! Is all this really necessary just to get a value out of a df?
            explanations = dict(zip(b[explanations]['value'], b[explanations]['meaning']))
            if (len(explanations) == 0):
                explanations = 'number'
            out[a] = {'question':meaning, 'legend': explanations}
    return out

def getIndividual_Quality():
    """
        Returns list of idIndividual who's survey has been completed
    """
    sqlq = """
        SELECT idIndividual
        SELECT *
        FROM Individual
        JOIN Meta
            ON idMeta = Meta_idMeta
            WHERE Meta.Quality = 1;
    """
    return getDataframeSQL(sqlq)


def getHouseholdIndividuals():
    """
    Returns list of pairings of
    idIndividual and their idHousehold
    for Individuals who completed their survey
    """
    sqlq = """
        SELECT idIndividual,Household_idHousehold as idHousehold
        FROM Individual
        JOIN Meta
            ON idMeta = Meta_idMeta
            WHERE Meta.Quality = 1;
    """
    return getDataframeSQL(sqlq)


def getUpcomingHH():
    """
    find HH that selected a date in the next two weeks
    but at least 9 days away (so we have time to send a parcel)
    :returns: dict - list of HHid
    """
    sqlq = """ 
    SELECT idHousehold
    FROM Household
    WHERE status < 4 
    AND date_choice >= CURDATE() + INTERVAL "9" DAY
    AND date_choice < CURDATE() + INTERVAL "14" DAY 
    ORDER BY date_choice ASC
    """
    return getSQL(sqlq)

def getHH_with_no_date():
    """
    find HH that haven't had a date yet
    ignore those contacts who have had a date in the last 90 days (with another HH ID)
    must have signed up at least 10 days ago
    This list will be checked and emailed to on the 15th of every month

    :returns: dict - list of HHid
    """
    sqlq = """ 
        SELECT idHousehold
         FROM Household
        	JOIN Contact 
        	ON Contact_idContact = idContact
         WHERE Household.status = 1
         AND Household.quality > 6
         AND Contact.status <> 'de'
         AND Contact.status <> 'unsubscribed'
         AND Household.timestamp < CURDATE() - INTERVAL "10" DAY
         AND idContact NOT IN (
        	SELECT Contact_idContact 
            FROM Household 
            WHERE Household.status > 3
            AND Household.timestamp > CURDATE() - INTERVAL "90" DAY
         );
    """
    return getSQL(sqlq)

def getHH_to_confirm():
    """
    find HH that selected a date in either 10 days or 8 days
    if they do not act in 2 days they get the second one
    (so we have time to send a parcel)
    :returns: dict - list of HHid
    """
    sqlq = """ 
    SELECT idHousehold
    FROM Household
    WHERE status < 3 
    AND (
        date_choice = CURDATE() + INTERVAL "7" DAY
        OR
        date_choice = CURDATE() + INTERVAL "9" DAY
        ) 
    ORDER BY date_choice ASC
    """
    return getSQL(sqlq)

def getHousehold_eQuality():
    sqlq = """
        SELECT idHousehold
        FROM Household
        JOIN Meta
            ON idHousehold = Household_idHousehold
            WHERE Meta.Quality = 1
            AND   DataType = 'E';
    """
    return getDataframeSQL(sqlq)


def getHH_single():
    """
    :returns: df of idHHs with only one occupant
    """
    sqlq = """
        SELECT idHousehold
        FROM Household
        WHERE `people` = 1
        ;
    """
    return getDataframeSQL(sqlq)

def getHH_notSingle():
    """
    :returns: df of idHHs with only one occupant
    """
    sqlq = """
        SELECT idHousehold
        FROM Household
        WHERE `people` > 1
        ;
    """
    return getDataframeSQL(sqlq)


def getElectricityIDs():
    """
    Returns all IDs with good electricity readings
    """
    sqlq = """
        SELECT idMeta
        FROM Meta
            WHERE DataType = 'E';
    """
    return getDataframeSQL(sqlq)

def getElectricityQuality():
    """
    Returns all IDs with good electricity readings
    """
    sqlq = """
        SELECT idMeta
        FROM Meta
            WHERE Quality = 1
            AND   DataType = 'E';
    """
    return getDataframeSQL(sqlq)

def getHH_aQuality():
    """
    Find all households with at least one good diary
        """
    sqlq = """
        SELECT DISTINCT(idHousehold) AS idHousehold
        FROM Household
        JOIN Meta
            ON idHousehold = Household_idHousehold
            WHERE Meta.Quality = 1
            AND   DataType = 'A'
    ;"""
    return getDataframeSQL(sqlq)


def getHousehold_Quality():
    """
    returns all IDs from Households who completed the diary
    proxy for completion: TimeMobile is no longer the default ('0'), but 1-6
    """
    sqlq = """
        SELECT idHousehold
        FROM Household
        WHERE page_number > 18
    ;"""
    return getDataframeSQL(sqlq)


def getHH_participation_rates():
    """
    Returns dataframe with
    idHousehold
    rate: HH rate of completed diaries
    e.g. HH with 4 over 8 year olds returning 2 diaries has a rate of 0.5
    """
    sqlq = """
        SELECT idHousehold, (participated/eligible) AS rate
        FROM (
            SELECT idHousehold, (age_group2 + age_group3 + age_group4 + age_group5 + age_group6) as eligible, count(idMeta) as participated
            FROM Household
            JOIN Meta
                ON idHousehold = Household_idHousehold
                WHERE DataType = 'A'
                AND Meta.Quality = 1
            GROUP BY idHousehold
        ) AS a
    ;"""
    return getDataframeSQL(sqlq)


def getPDF(col, tab, condition, name):
    """
    :param str col: column to query
    :param str tab: table to query
    :param str condition: WHERE term in query
    :param str name: label for the return column

    :return: dataframe

    - col: name of the column (col) in a given table (tab)
    - meaning: each value found in this column translated into its meaning as found in the Legend table.
    - `name`: relative share of households to whom this value applies in %. To distinguish this column when executing this query multiple times, the title for the column is specified as `name`, e.g. 'Max' or 'Min' for hh meeting the condition of highest/lowset peak demand, such that they can be merged for comparison

    Households need to meet `condition`
    """

    sqlq = """
    Select col,meaning,{3} FROM
        (SELECT {0} AS thisCol,ROUND
        (
         COUNT(*)/
             (
             SELECT COUNT(*) as count
             FROM {1}
             WHERE {2}
             ) *100 ,1) as {3}
        FROM {1}
        WHERE {2}
        GROUP BY thisCol) as ColPercent
    JOIN Legend
        ON thisCol = Legend.`value`
        WHERE Legend.`col` = '{0}'
        AND Legend.`tab` = '{1}'
        ORDER BY value
    """.format(col, tab, condition, name)
    return getDataframeSQL(sqlq)


def getPDF_noLegend(col, tab, condition, name):
    """
    Used when the meaning of values is not found in Legend (often because they are couning values like 'how many of X do you have' or free text)

    Returns the

    - col: plain english name for the column (col) based on the Legend table
    - meaning: distinct occurances of values encountered in colum (col) in table (tab)
    - `name`: relative share of households to whom this value applies in %. To distinguish this column when executing this query multiple times, the title for the column is specified as `name`, e.g. 'Max' or 'Min' for hh meeting the condition of highest/lowset peak demand, such that they can be merged for comparison

    Households need to meet `condition`
    """

    sqlq = """
    Select meaning AS col, val AS meaning, {3}
        FROM (SELECT {0} AS val,ROUND
        (
        COUNT(*)/
            (SELECT COUNT(*) as count
            FROM {1}
            WHERE {2}
            ) *100,1) as {3}
        FROM {1}
        WHERE {2}
        GROUP BY val) as ColPercent
    JOIN Legend
        ON Legend.`col` = '{0}'
        AND Legend.`tab` = '{1}'
        ORDER BY value;
    """.format(col, tab, condition, name)
    return getDataframeSQL(sqlq)


def getQuestion(col, tab):
    """
    Returns the question asked of a participant for col {0} in table {1}
    """
    sqlq = """
    SELECT meaning AS q
    FROM Legend
    WHERE `value` = 'q'
    AND `col` = '{0}'
    AND `tab` = '{1}'
    ;
    """.format(col, tab)
    results = getSQL(sqlq)
    return results[0]['result']


def getCount(table, condition=True):
    """ number of rows in a `table` matching the `condition` """
    sqlq = """
        SELECT Count(*) as result
        FROM {0}
        WHERE {1};
    """.format(table, condition)
    results = getSQL(sqlq)
    return results[0]['result']


# ----------------------------------------------
#
#                   _energy
#
# ----------------------------------------------

def getAvgPowerForHH(idHH):
    """
    :param ind idHH: id for this HH
    :returns: float of average power for this HH
    """
    sqlq = "SELECT AVG(Watt) AS result FROM hh_el_hour WHERE Household_idHousehold = {};".format(idHH)
    results = getSQL(sqlq)
    return results[0]['result']

def getp2aForHH(idHH):
    """
    :param ind idHH: id for this HH
    :param average_over_all: if False (default), the normalising
        value is the average ONLY non-peak hours. If True, the normalising
        value is the average over ALL the hours.
    :returns: float of peak2avg power for this HH
    """
    sqlq = """
    SELECT (pWatt / aWatt) AS peak2avg
        FROM (
            SELECT AVG(Watt) AS pWatt, Household_idHousehold AS pHH
            FROM hh_el_hour
            WHERE HOUR(dt) BETWEEN 17 AND 19
            AND Household_idHousehold = {}
        ) AS peakLoad
    JOIN
        (
            SELECT AVG(Watt) AS aWatt, Household_idHousehold AS aHH
            FROM hh_el_hour
            WHERE Household_idHousehold = {}
        ) AS avgLoad
    ON aHH = pHH;
    """
    sqlq = sqlq.format(idHH, idHH)
    return getDataframeSQL(sqlq)


def getAvgPowerByHH():
    """
    :returns: dataframe with average power used by each household
    :columns: power, idHousehold
    """
    sqlq = """
        SELECT
            AVG(Watt) AS power,
            Household_idHousehold AS idHousehold
        FROM hh_el_hour
        GROUP BY Household_idHousehold;
        """
    return getDataframeSQL(sqlq)

def getPowerPeriods(idMeta, dt, n=6, asc=True):
    """
    get average power over n 10 min periods following dt
    :param int n: number of 10 min periods to consider
    :returns: float average power over the next n periods
        """
    if asc:
        # readings at and after dt
        MoreOrLess = '>'
        order = 'ASC'
    else:
        # readings leading up to dt
        MoreOrLess = '<'
        order = 'DESC'

    sqlq = """
        SELECT AVG(Watt) AS Watt FROM
            (
            SELECT Watt
            FROM Electricity_10min
            WHERE Meta_idMeta = {}
            AND dt {}= '{}'
            ORDER BY dt {}
            LIMIT {}
            ) as WattReadings
        ;
        """.format(idMeta,MoreOrLess,dt,order,n)
    result = getSQL(sqlq)[0]
    if result['Watt']:
        return result['Watt']
    else:
        return 0

# ----------------------------------------------
#
#                   _activities
#
#   imported from Marina my_meter
#
# ----------------------------------------------

def getActTimeForHH(idHH,categorise=False):
    """
    :param ind idHH: id for this HH
    :param boolean categorise: default use activities, if True return Categories instead
    :returns: dataframe with act and times (act are tuc, or categories if True)
    """
    sqlq = """SELECT dt_activity,tuc AS act
            FROM hh_act
            WHERE Household_idHousehold = {};""".format(idHH)
    if categorise:
        sqlq = """SELECT dt_activity,category AS act
            FROM Meter.hh_act
            JOIN Categories
            ON Categories.tuc=hh_act.tuc
            WHERE Household_idHousehold = {};""".format(idHH)
    return getDataframeSQL(sqlq)


def getCatTimeForHH(idHH, category='category'):
    """
    SUPERSEEDED by getActCat
    :param ind idHH: id for this HH
    :returns: dataframe with Category and dt_activity
    """
    sqlq = """SELECT Household_idHousehold AS idHousehold, dt_activity, {}, location
            FROM Meter.hh_act
            JOIN Categories
            ON Categories.tuc=hh_act.tuc
            WHERE Household_idHousehold = {};
            """.format(category,idHH)
    return getDataframeSQL(sqlq)


def getActCat():
    """
    :returns: all activity, Meta and Category columns
        idMeta can be used to link electricity readings
    """
    sqlq = """
            SELECT *
            FROM Meter.hh_act
            JOIN Categories
            ON Categories.tuc=hh_act.tuc
            JOIN Meta
            ON Meta.Household_idHousehold = hh_act.Household_idHousehold
            WHERE DataType = 'E'
            ;"""
    return getDataframeSQL(sqlq)


def getWattCatForHH(idHH, condition="", category = "category"):
    """
    :param str idHH: id for this HH
    :param str condition: "home" restricts location to '1: home' and '6: garden'
    :param str category: options 'category', 'subcategory' or 'e_cat'
    :returns: dataframe with Category and Watt and dt
    """

    if (condition == "home"):
        condition = "AND (location = 1 OR location =6)"
    sqlq = """SELECT {},
                     Watt,
                     dt
              FROM hh_el_act_hour
              JOIN Categories
              ON Categories.tuc = hh_el_act_hour.tuc
              WHERE idHousehold = {}
              {}
              ;""".format(category,idHH,condition)
    return getDataframeSQL(sqlq)


def getActIDs(condition = ""):
    # Returns activity IDs that have been used by participants
    sqlq = "SELECT DISTINCT idActivities FROM Activities {0};".format(condition)
    # return getDataframeSQL(sqlq)
    return getSQL(sqlq)

def getTUCsAndCategories():
    """ Returns a dataframe of TUCs as keys and Categories as values """
    sqlq = "SELECT tuc, category FROM Categories WHERE category is not NULL;"
    return getDataframeSQL(sqlq)

def getDbEntryForActivityID(actID):
    sqlq = "SELECT * FROM Activities WHERE idActivities = '%s';" %actID
    if (getSQL(sqlq)):
        result = getSQL(sqlq)[0]
        out = {}
        string_variables = ['enjoyment', 'people', 'location', 'Meta_idMeta', 'tuc', 'idActivities']
        for key in result:
            value = result[key]
            if (key == 'path'):
                if (value != None):
                    value = value.split(",")
            if (key in string_variables):
                out[key] = "%s" %value
            else:
                out[key] = value
        return out
    else:
        if (cursor.rowcount == 0):
            print "Your result set is empty."
            return 0
        print "Error in 'getPathForActivityID': while executing mySQL query."
        return False

# ----------------------------------------------
#
#                   _time_budget
#
#   imported from Marina my_meter_sql_statements
#
# ----------------------------------------------



def getCategoryCount_byHour(dataType = 'meter'):
    """ Frequency of Category reported per hour
    :param str dataType:

    options:

    - meter (default): number of times that category was reported in that hour
    - TUS_starttime:  number of times that category was reported as having started in that hour
    - TUS: number of 10 minute chunks people spent on that category, hour by hour

    :returns: A pivot table object with

    - index:   category
    - columns: h (for hour)
    - values:  c (for the count of the number of instances of that category in that hour)
    """
    sqlq = {
        'meter': """
            SELECT COUNT(Categories.category) as c, Categories.category as category,
            Hour(dt_activity) as h
            FROM Activities
            JOIN Categories
            JOIN Meta
            ON Categories.tuc = Activities.tuc
            AND Meta.idMeta = Activities.Meta_idMeta
            WHERE Quality = 1
            GROUP BY h, Categories.category;
        """,
        'TUS': """
            SELECT COUNT(category) as c, category, Hour(dt_activity) as h
            FROM TUS2015 as mytable
            JOIN Categories
            ON Categories.tuc = mytable.tuc
            GROUP BY h, category;
        """,
        'TUS_starttime': """
            SELECT COUNT(category) as c, category, Hour(dt_activity) as h
            FROM TUS2015_Meterlike as mytable
            JOIN Categories
            ON Categories.tuc = mytable.tuc
            WHERE
            !(Hour(dt_activity) = 4 AND Minute(dt_activity) = 0)
            GROUP BY h, category;
        """
        }
    df =  getDataframeSQL(sqlq[dataType])
    pt = pd.pivot_table(df, index = 'category', columns = 'h', values = 'c')
    return pt


def getPeopleCount_byHour(dataType = 'meter'):
    """
    Count of unique users reporting a specific category in each hour of the day
    Input: 'dataType': meter (default) or TUS

    Returns:
        A dataframe object with the following columns:
            - h (for hour)
            - category
            - c (count of unique reporters of this category)
    """
    sqlq = {
        'meter': """
            SELECT COUNT(category) as c, category, h
            FROM (
                SELECT DISTINCT Activities.Meta_idMeta, Hour(dt_activity) as h, Categories.category as category
                FROM Activities
                JOIN Categories
                ON Categories.tuc = Activities.tuc
             ) as alice
            GROUP BY h, category;
        """,
        'TUS': """
            SELECT COUNT(category) as c, category, h
            FROM (
                SELECT DISTINCT hh, pnum, Hour(dt_activity) as h, category
                FROM TUS2015
                JOIN Categories
                ON Categories.tuc = TUS2015.tuc
             ) as alice
            GROUP BY h, category;
        """
        }
    return getDataframeSQL(sqlq[dataType])


def getTUS_listOfTucs_byHour():
    sqlq = """
            SELECT tuc, Hour(dt_activity) as h FROM TUS2015;
    """
    return getDataframeSQL(sqlq)











#set of mysql statements SPECIFICALLY for insertions (i.e. incomplete).
#includes 'household_spec', specifying households generally, and 
#'household_conds', where you can specify the particulars that a household has or doesn't have.
#conditions limit the set of households specified in the spec (or any other set)
household_specifications_with_conditions = { 
    "household_spec"       :   {
        "households_with_at_least_1_participant"   : 
            """
                SELECT DISTINCT Meta.Household_idHousehold as idHH
                FROM Meta
                JOIN Household as H on Meta.Household_idHousehold = H.idHousehold
                WHERE Meta.DataType = 'A' AND Meta.Quality = 1
                {0}
            """,
        "households_with_good_el"   : 
            """
                SELECT DISTINCT Meta.Household_idHousehold as idHH
                FROM Meta
                JOIN Household as H on Meta.Household_idHousehold = H.idHousehold
                WHERE DataType = 'E' AND Quality = 1
                {0}
            """,
        "households_where_participants_are_at_least_half_the_number_of_adults"  :
            """
                SELECT household as idHH 
                FROM( 
                    SELECT  H.idHousehold as household, 
                    (H.age_group2 + H.age_group3 + H.age_group4 + H.age_group5 + H.age_group6) as num_adults, 
                    count(M_P.idMeta) as participants 
                    FROM Household as H 
                    JOIN Meta as M_P on H.idHousehold = M_P.Household_idHousehold 
                    WHERE H.people = (age_group1 + age_group2 + age_group3 + age_group4 + age_group5 + age_group6) 
                    AND M_P.DataType = 'A' AND M_P.Quality = 1 
                    AND H.page_number >= 16
                    {0}
                    GROUP BY household 
                ) as alice 
                WHERE participants >= num_adults/2
            """,
        "households_where_participants_are_equal_to_the_number_of_adults"  :
            """
                SELECT household as idHH 
                FROM( 
                    SELECT  H.idHousehold as household, 
                    (H.age_group2 + H.age_group3 + H.age_group4 + H.age_group5 + H.age_group6) as num_adults, 
                    count(M_P.idMeta) as participants 
                    FROM Household as H 
                    JOIN Meta as M_P on H.idHousehold = M_P.Household_idHousehold 
                    WHERE H.people = (age_group1 + age_group2 + age_group3 + age_group4 + age_group5 + age_group6) 
                    AND M_P.DataType = 'A' AND M_P.Quality = 1 
                    AND H.page_number >= 16
                    {0}
                    GROUP BY household 
                ) as alice 
                WHERE participants == num_adults 
            """,
        "sample_households"  :   
            """
                SELECT idHousehold as idHH 
                FROM Household as H
                WHERE idHousehold = '5210' or idHousehold = '8062'
                {0}
            """
        },
    "household_conds"      : {
        "children"  :   {
            'only young'        :   "AND H.age_group1 > 0",
            'no young'          :   "AND H.age_group1 = 0",
            'only old'          :   "AND H.age_group2 > 0",
            'no old'            :   "AND H.age_group2 = 0",
            'either'            :   "AND H.age_group1 > 0 OR H.age_group2 > 0",
            'both'              :   "AND H.age_group1 > 0 AND H.age_group2 > 0", 
            'none'              :   "AND H.age_group1 = 0 AND H.age_group2 = 0"  
        },
        "day_of_week"   :   {
            'weekday'   : 
            """
                AND H.idHousehold NOT IN 
                (
                    SELECT Distinct  H.idHousehold
                    FROM Household as H
                    JOIN Meta as M on M.Household_idHousehold = H.idHousehold
                    JOIN Activities as A on A.Meta_idMeta = M.idMeta
                    WHERE DAYOFWEEK(A.dt_activity) = 1
                    OR DAYOFWEEK(A.dt_activity) = 7
                )
            """,
            'weekend'   : 
            """
                AND H.idHousehold NOT IN 
                (
                    SELECT Distinct  H.idHousehold
                    FROM Household as H
                    JOIN Meta as M on M.Household_idHousehold = H.idHousehold
                    JOIN Activities as A on A.Meta_idMeta = M.idMeta
                    WHERE DAYOFWEEK(A.dt_activity) = 1
                    OR DAYOFWEEK(A.dt_activity) = 7
                )
            """
        },
        "PV"    :   {'yes': 'AND H.appliance_b9 > 0', 'no': 'AND H.appliance_b9 = 0'},
        "NSH"    :   {'yes': 'AND H.appliance4 > 0', 'no': 'AND H.appliance4 = 0'},
        "EV"    :   {'yes': 'AND H.appliance_b11 > 0', 'no': 'AND H.appliance_b11 = 0'}
    }
}

#the three functions below differ only on the initial query that gets either activity, or electricity, or household
#info
def get_activities_from_specified_households(households = "households_with_at_least_1_participant", hh_conds = False):
    query = """
            SELECT M.Household_idHousehold as idHH, M.idMeta as idMeta, A.dt_activity as t, A.location as loc
            FROM ( {0} ) as alice
            JOIN Meta as M 
            JOIN Activities as A
            WHERE M.Household_idHousehold = alice.idHH
            AND M.DataType = 'A' AND M.Quality = 1 
            AND A.Meta_idMeta = M.idMeta;
            """
    hh = household_specifications_with_conditions["household_spec"][households]
    #combine conditions into one string (since conditions start with 'AND..' in mysql)
    hh_conditions = " "
    if (hh_conds):
        for key, value in hh_conds.iteritems():
            if (key == 'custom'):
                cond = value
            else:
                cond = household_specifications_with_conditions["household_conds"][key][value] #get the mysql statement for that condition
            hh_conditions += cond + " "
    spec = hh.format(hh_conditions)
    query = query.format(spec)
    return getDataframeSQL(query)

def get_electricity_from_specified_households(households = "households_with_at_least_1_participant", hh_conds = False):
    query = """
            SELECT M.Household_idHousehold as idHH, E.dt as t, E.Watt as Watt
            FROM ( {0} ) as alice
            JOIN Meta as M 
            JOIN Electricity_10min as E
            WHERE M.Household_idHousehold = alice.idHH
            AND M.DataType = 'E' AND M.Quality = 1 
            AND E.Meta_idMeta = M.idMeta;
            """
    hh = household_specifications_with_conditions["household_spec"][households]
    #combine conditions into one string (since conditions start with 'AND..' in mysql)
    hh_conditions = " "
    if (hh_conds):
        for key, value in hh_conds.iteritems():
            if (key == 'custom'):
                cond = value
            else:
                cond = household_specifications_with_conditions["household_conds"][key][value] #get the mysql statement for that condition
            hh_conditions += cond + " "
    spec = hh.format(hh_conditions)
    query = query.format(spec)
    return getDataframeSQL(query)

def get_household_info_from_specified_households(households = "households_with_at_least_1_participant", hh_conds = False):
    query = """
            SELECT H.idHousehold as idHH, 
            count(M_P.idMeta) as participants,
            (H.age_group2 + H.age_group3 + H.age_group4 + H.age_group5 + H.age_group6) as num_adults,
            (H.age_group1 + H.age_group2 + H.age_group3 + H.age_group4 + H.age_group5 + H.age_group6) as num_people
            FROM ( {0} ) as alice
            JOIN Household as H 
            JOIN Meta as M_P on H.idHousehold = M_P.Household_idHousehold 
            WHERE M_P.DataType = 'A' AND M_P.Quality = 1 
            AND H.idHousehold = alice.idHH
            GROUP BY alice.idHH;
            """
    hh = household_specifications_with_conditions["household_spec"][households]
    #combine conditions into one string (since conditions start with 'AND..' in mysql)
    hh_conditions = " "
    if (hh_conds):
        for key, value in hh_conds.iteritems():
            if (key == 'custom'):
                cond = value
            else:
                cond = household_specifications_with_conditions["household_conds"][key][value] #get the mysql statement for that condition
            hh_conditions += cond + " "
    spec = hh.format(hh_conditions)
    query = query.format(spec)
    return getDataframeSQL(query)










"""
_connectDB
connect to db on importing this module
"""

cursor = connectDB()
