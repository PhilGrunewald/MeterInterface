#!/usr/bin/env python

import MySQLdb.cursors
import numpy as np #arithmetical operations
import pandas as pd #data analysis
import re #regular expressions - for searching if strings contain numbers etc.
import matplotlib.pyplot as plt #plotting
from pandas import Series, DataFrame #the book suggests this is done explicitly

import db_ini as db     # reads the database and file path information

# override host to local
db.Host = 'localhost'

# ========= #
#  GLOBALS  #
# ========= #

graphs = { 
"day_Watt": { 
    "query": "SELECT Watt AS y,\
               dt   AS x,\
               Meta_idMeta AS label\
            FROM Electricity_10min\
            JOIN Meta as M on Meta_idMeta = M.idMeta \
            JOIN Household as H on H.idHousehold = M.Household_idHousehold \
            WHERE M.Quality = 1 \
            {};",
    "xLabel": "Day",
    "yLabel": "Watt",
    "title" : "Participant load"
},

"Activity_graph": { 
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
    "xLabel": "Number of household activities preported per hour",
    "yLabel": "Electricity use [Watt]",
    "title" : "Activity and Power per HH 30 min period"
},

"TUC_Watt": {
    "query": "SELECT category AS x,\
                     Watt AS y,\
                     dt AS label\
              FROM hh_el_act_hour \
              JOIN Categories \
              ON Categories.tuc = hh_el_act_hour.tuc;\
              {};",
    "xLabel": "TUC",
    "yLabel": "Watt",
    "title" : "..."
    },

"Location_Watt" : {
    "query": "SELECT meaning AS x,\
                     Watt AS y,\
                     dt AS label\
              FROM hh_el_act_hour \
              JOIN Legend \
              ON Legend.value = hh_el_act_hour.location\
              WHERE Legend.col = 'location5'\
              {};",
    "xLabel": "Location",
    "yLabel": "Watt",
    "title" : "..."
    },

"Enjoy_Watt": {
    "query": "SELECT enjoyment AS x,\
                     Watt AS y,\
                     dt AS label\
              FROM hh_el_act_hour \
              {};",
    "xLabel": "Location",
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



def getDataFrame(_graph, _condition):
    query = _graph["query"].format(_condition)
    cursor.execute(query)
    results = cursor.fetchall()
    df = DataFrame(list(results)) #a DataFrame object with columns 'x', 'y', and 'label'

    # ===== Rename columns =====
    xL = _graph['xLabel']
    yL = _graph['yLabel']
    df.rename(columns = {'x':xL, 'y':yL}, inplace = True)

    # ===== Disretise time =====
    if (df[xL].dtype == 'datetime64[ns]'): df[xL] = [r.time() for r in df[xL]] #since then what we want is to discretise by time
    #df[xL] = [r.hour*60 + r.minute for r in df['x']]


    # ===== Get stats =====
    df_t = df.pivot_table(yL, ['label'], xL)
    df = df_t.describe() #produces a row of stats, but only works column by column (hence the transposition above)
    return df



def plot(graph):
    # graph = Electricity_graph
    df = getDataFrame(graph, "")
    # max_activity_count = 8
    # df = df[[i for i in xrange(max_activity_count + 1) if i > 0]] #columns with labels from 1 to max_activity_count
    print df
    ind = np.arange(8)  # the x locations for the groups
    width = 0.35       # the width of the bars
    plt.bar(ind + width, df.ix['mean'], width, color = 'green', label = 'Mean')
    #plt.bar(ind + width, df.ix['mean'], width, color = 'green', label = 'Mean')
    # plt.plot([525]*2, color = 'green')
    # plt.fill_between(df.ix['25%'].index, df.ix['25%'], df.ix['75%'], alpha = 0.2, label = '$\pm$ quartile', color = 'green')
    plt.legend(loc='upper left', frameon=False)
    plt.xlabel(graph["xLabel"])
    plt.ylabel(graph["yLabel"])
    # get rid of the frame
    for spine in plt.gca().spines.values():
        spine.set_visible(False)   
    plt.tick_params(top='off', bottom='off', left='on', right='off', labelleft='on', labelbottom='on')
    plt.savefig('activityCount_Power.png')
    plt.show()

def boxplot(graphName):
    graph = graphs[graphName]
    df = getDataFrame(graph, "")
    fig, ax = plt.subplots()
    bp = df.boxplot(ax=ax, notch=True, patch_artist=True)
    print df
    props = dict(boxes="Green", whiskers="White", medians="White", caps="Gray")
    df.plot.box(color=props, patch_artist=True)
    # ax.set_xticks(range(1,9))
    for spine in plt.gca().spines.values():
        spine.set_visible(False)   
    plt.tick_params(top='off', bottom='off', left='on', right='off', labelleft='on', labelbottom='on')
    plt.ylim([0,1200])
    plt.xlabel(graph["xLabel"])
    plt.ylabel(graph["yLabel"])
    plt.savefig("{}.pdf".format(graphName), transparent=True)
    plt.show()

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    cursor = connectDB()
    i = 0
    for graphType in graphs.keys():
        print "{}: {}".format(i, graphType)
        i += 1
    selection = raw_input("Graph type: ")
    graphName = graphs.keys()[int(selection)]
    boxplot(graphName)
