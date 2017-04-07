#!/usr/bin/env python
import MySQLdb.cursors
import numpy as np
import pandas as pd           # to reshape el readings
import matplotlib.pyplot as plt

import db_ini as db     # reads the database and file path information
# override host to local
# db.Host = 'localhost'

# ========= #
#  GLOBALS  #
# ========= #

BaseloadPerHH  = "SELECT MIN(Watt) AS result \
          FROM Meter.Electricity_10min \
          WHERE Watt > 20 \
          GROUP BY Meta_idMeta;"
bins   = 40

ActivityCount_by_WattHour = "\
    SELECT COUNT(ActivityHH.Household_idHousehold) AS x, Watt AS y\
     FROM (\
     SELECT * \
    	FROM Meta\
        JOIN Activities\
        ON Meta_idMeta = idMeta\
     ) ActivityHH\
     JOIN (\
     SELECT * \
    	FROM Meta\
        JOIN El_hour\
        ON Meta_idMeta = idMeta\
     ) ElectricityHH\
     ON ActivityHH.Household_idHousehold = ElectricityHH.Household_idHousehold\
     AND dt BETWEEN dt_activity - INTERVAL 30 MINUTE AND dt_activity + INTERVAL 30 MINUTE\
    GROUP BY dt,Watt,ElectricityHH.Household_idHousehold;"

# ========= #
# FUNCTIONS #
# ========= #

def connectDB():
    """ use db credentials for MySQLdb """
    global dbConnection
    dbConnection = MySQLdb.connect(
        host=db.Host,
        user=db.User,
        passwd=db.Pass,
        db=db.Name,
        cursorclass=MySQLdb.cursors.DictCursor)
    return dbConnection.cursor()

def create_e1hour():
    """ take 1 min readings and produce table with 1 hour mean values """
    sqlq = "SELECT idMeta AS result FROM Meta WHERE DataType = 'E' AND Quality = '1'";
    metaIDs = getResults(sqlq)
    for metaID in metaIDs:
        sqlq = "SELECT * FROM Meter.Electricity WHERE Meta_idMeta=%s" % metaID
        df_elec = pd.read_sql(sqlq, con=dbConnection)
        df_elec.index = pd.to_datetime(df_elec.dt)        # index by time
        # downsample, label left such that time refers to the next minute
        df_elec_resampled = df_elec.resample('60min', label='left').mean()
        # remove index, so that a new one is auto-incremented
        del df_elec_resampled['idElectricity']
        # pandas is brutal, if not append it rewrites the table!!
        df_elec_resampled.to_sql(con=dbConnection, name='El_hour', if_exists='append', flavor='mysql')

def getXY(_query):
    """ send sql query and return result as list """
    x = []
    y = []
    h = {}
    cursor.execute(_query)
    results = cursor.fetchall()
    for result in results:
        actCount = int(result['x'])
        power    = int(result['y'])
        x.append(actCount)
        y.append(power)
        try:
            h[actCount].append(power)
        except KeyError:
            h[actCount] = [power]
    return x,y,h

def getResults(_query):
    """ send sql query and return result as list """
    dataList = []
    cursor.execute(_query)
    results = cursor.fetchall()
    for result in results:
        dataList.append(int(result['result']))
    return dataList

def plotScatter(d):
    """ x-y scatter """
    print d[2]
    data = d[2]
    x_ = []
    y_ = []
    for dkey in data:
        x_.append(dkey)
        y_.append(np.mean(data[dkey]))
    plt.scatter(d[0],d[1],alpha=0.1)
    plt.scatter(x_,y_,c='red')
    plt.xlabel('Activities reported per hour')
    plt.ylabel('Baseload [Watt]')
    plt.show()


def plotHist(plotData):
    """ create the figure """
    fig, ax = plt.subplots()
    plt.hist(plotData, bins, range=(min(plotData), max(plotData)), normed=True, facecolor='gray', alpha=0.5)
    # plt.yticks(np.arange(0, 0.041, 0.01))
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    
    plt.xlabel('Baseload [Watt]')
    plt.ylabel('Probability')
    plt.show()

# ========= #
#  EXECUTE  #
# ========= #

cursor = connectDB()
query = ActivityCount_by_WattHour
# plotHist(getResults(query))
plotScatter(getXY(query))
# create_e1hour()
