#!/usr/bin/env python

import datetime as dt
import MySQLdb.cursors
import numpy as np
import pandas as pd           # to reshape el readings
import matplotlib.pyplot as plt

import db_ini as db     # reads the database and file path information
# override host to local
#db.Host = 'localhost'

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

"Most_intensive_10min": {
    "query": " SELECT a.Watt AS y, a.dt AS x, Meta_idMeta AS label\
                FROM El_hour a\
                INNER JOIN (\
                    SELECT Meta_idMeta AS b_ID, MAX(Watt) AS mWatt\
                    FROM El_hour\
                    WHERE Watt >20\
                    GROUP BY Meta_idMeta\
                    ) b \
                    ON ((Meta_idMeta = b_ID) AND (a.Watt = mWatt)); ",
    "xLabel": "Day",
    "yLabel": "Watt",
    "title" : "Time of hihgest demand hour"
},
"Most_intensive_hour": {
    "query": " SELECT a.Watt AS y, a.dt AS x, Meta_idMeta AS label\
                FROM Electricity_10min a\
                INNER JOIN (\
                    SELECT Meta_idMeta AS b_ID, MAX(Watt) AS mWatt\
                    FROM Electricity_10min\
                    WHERE Watt >20\
                    GROUP BY Meta_idMeta\
                    ) b \
                    ON ((Meta_idMeta = b_ID) AND (a.Watt = mWatt)); ",
    "xLabel": "Day",
    "yLabel": "Watt",
    "title" : "Time of hihgest demand hour"
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

"TUC_Watt": {
    "query": "SELECT tuc AS x,\
                     Watt AS y,\
                     dt AS label\
              FROM hh_el_act_hour {};",
    "xLabel": "TUC",
    "yLabel": "Watt",
    "title" : "..."
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
            x.append(result['x'].time())
        except:
            x.append(int(result['x']))
        y.append(int(result['y']))
        try:
            label.append(int(result['label']))
        except:
            label.append(0)
    return x,y,label

def plotScatter(graphName):
    """ x-y scatter """
    graph = graphs[graphName]
    [x,y,label] = getXY(graph["query"].format(condition))

    # figure
    fig, ax = plt.subplots()
    plt.scatter(x,y,s=200, lw=0, color='g',alpha=0.2)
    plt.xlabel(graph["xLabel"])
    plt.ylabel(graph["yLabel"])

    if isinstance(x[0], dt.time):
        # if x value are time based, make 24 hours with only 3 ticks
        xTickLocations = [dt.time(h,0) for h in range(6,24,6)]
        ax.xaxis.set_ticks(xTickLocations)
        xTickLabels    = ["6am", "noon", "6pm"]
        ax.set_xticklabels(xTickLabels)

    # ax.xaxis.major.locator.set_params(nbins=5)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plt.savefig("../figures/{}.pdf".format(graphName), transparent=True)
    plt.savefig("../figures/{}.png".format(graphName), transparent=True)
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
graphName = graphs.keys()[int(selection)]
plotScatter(graphName)
