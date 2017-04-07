#!/usr/bin/env python
import MySQLdb.cursors
import numpy as np
import matplotlib.pyplot as plt

import db_ini as db     # reads the database and file path information

# ========= #
#  GLOBALS  #
# ========= #

query  = "SELECT MIN(Watt) AS result \
          FROM Meter.Electricity_10min \
          WHERE Watt > 20 \
          GROUP BY Meta_idMeta;"
bins   = 40

# ========= #
# FUNCTIONS #
# ========= #

def connectDB():
    """ use db credentials for MySQLdb """
    dbConnection = MySQLdb.connect(
        host=db.Host,
        user=db.User,
        passwd=db.Pass,
        db=db.Name,
        cursorclass=MySQLdb.cursors.DictCursor)
    return dbConnection.cursor()

def getResults(_query):
    """ send sql query and return result as list """
    dataList = []
    cursor.execute(_query)
    results = cursor.fetchall()
    for result in results:
        dataList.append(int(result['result']))
    return dataList

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
plotHist(getResults(query))
