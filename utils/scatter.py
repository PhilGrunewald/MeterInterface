#!/usr/bin/env python

import MySQLdb.cursors
import numpy as np
import pandas as pd           # to reshape el readings
import matplotlib.pyplot as plt

import db_ini as db     # reads the database and file path information
# override host to local
db.Host = 'localhost'

# ========= #
#  GLOBALS  #
# ========= #

graphs = { 
"Load": { 
    "query": "SELECT Watt AS y,\
               dt   AS x,\
               Meta_idMeta AS label\
            FROM Electricity_10min\
            {};",
    "xLabel": "Day",
    "yLabel": "Watt",
    "title" : "Participant load"
},

"TUC_Count": {
    "query": "SELECT Count(*) AS y,\
                tuc AS x,\
                Meta_idMeta AS label\
               FROM Activities\
               GROUP BY tuc,Meta_idMeta {};",
    "xLabel": "Activity codes [tuc]",
    "yLabel": "Mentions per person",
    "title" : "Activity frequency"
},

"ActivityCount_by_WattHour": {
    "query": "SELECT COUNT(ActivityHH.Household_idHousehold) AS x,\
                     Watt AS y,\
                     dt AS label\
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
              GROUP BY dt,Watt,ElectricityHH.Household_idHousehold {};",
    "xLabel": "Activity count",
    "yLabel": "Watt",
    "title" : "Activity and Power per HH 30 min period"
    }
}
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

def getXY(_query):
    """ send sql query and return result as list """
    x = []
    y = []
    label = []
    cursor.execute(_query)
    results = cursor.fetchall()
    for result in results:
        try:
            x.append(int(result['x']))
        except:
            # handle datetime values
            xVal = "{}".format(result['x']).split(' ')[1]
            x.append("{}".format(xVal).split(':')[0])
        y.append(int(result['y']))
        try:
            label.append(int(result['label']))
        except:
            label.append(0)
    return x,y,label

def plotScatter(d):
    """ x-y scatter """
    plt.scatter(d[0],d[1],color='g',alpha=0.1)
    plt.xlabel(graph["xLabel"])
    plt.ylabel(graph["yLabel"])
    plt.show()

# ========= #
#  EXECUTE  #
# ========= #

cursor = connectDB()
i = 0
for graphType in graphs.keys():
    print "{}: {}".format(i, graphType)
    i += 1
condition = ""
selection = raw_input("Graph type: ")
graph = graphs[graphs.keys()[int(selection)]]
plotScatter(getXY(graph["query"].format(condition)))
