#!/usr/bin/env python

# 22 May 2017 - PG unfinished!!

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

graphs = { 
"Load": { 
    "query": "SELECT dt, \
              Watt AS x, \
              category AS y \
              FROM Meter.hh_act_el \
              Join Categories \
              ON hh_act_el.tuc = Categories.tuc;",
    "xLabel": "Watt",
    "yLabel": "Activity categories",
    "title" : "High power and low power activities"
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

def getStack(_query):
    """ create stacked bars """
    data = {}
    cursor.execute(_query)
    results = cursor.fetchall()
    for result in results:
        try:
            data[result['y']].append(result['x'])
        except:
            data[result['y']] = [result['x']]
    print data
    return data


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
# plotScatter(getXY(graph["query"].format(condition)))

getStack(graph["query"])

