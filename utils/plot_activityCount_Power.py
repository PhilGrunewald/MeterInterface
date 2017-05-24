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

Electricity_graph = { 
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
}

Activity_graph = { 
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
    print df
    plt.plot(df.ix['mean'], label = 'Sample Size = ' + str(int(df.ix['count'][0])))
    plt.fill_between(df.ix['25%'].index, df.ix['25%'], df.ix['75%'], alpha = 0.2)
    plt.legend()
    plt.show()



def main():
  """ Description """
  plot(Activity_graph)

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    cursor = connectDB() #this has to be here, outside the functions that reference it
    main()
