#!/usr/bin/env python
import MySQLdb.cursors
import numpy as np
import matplotlib.pyplot as plt

import db_ini as db     # reads the database and file path information

# ========= #
#  GLOBALS  #
# ========= #

graphs = {
"activityCountByIndividual": {
    "query": "SELECT count(*) as result FROM Meter.Activities WHERE Meta_idMeta > 2696 GROUP BY Meta_idMeta;",
    "bins": 30,
    "xLabel": "Activities reported per person",
    "yLabel": "Probablility",
    "title" : ""
},

"baseload_distribution": {
    "query": "SELECT MIN(Watt) AS result \
          FROM Meter.Electricity_10min \
          WHERE Watt > 10 \
          GROUP BY Meta_idMeta;",
    "bins": 30,
    "xLabel": "Baseload [Watt]",
    "yLabel": "Probablility",
    "title" : ""
},

"Most_intensive_hour": {
    
    "query": "SELECT MAX(Watt) AS y,\
                Hour(dt) AS result\
                FROM Electricity_10min\
                GROUP BY Meta_idMeta;",
    "bins": 24,
    "xLabel": "Day",
    "yLabel": "Watt",
    "title" : "Time of hihgest demand hour"
},

"average_load_distribution": {
    "query": "SELECT AVG(Watt) AS result \
          FROM Meter.El_hour \
          WHERE Watt > 10 \
          GROUP BY Meta_idMeta;",
    "bins": 30,
    "xLabel": "Average load [Watt]",
    "yLabel": "Probablility",
    "title" : ""
},

"peakload_distribution": {
    "query": "SELECT MAX(Watt) AS result \
          FROM Meter.El_hour \
          WHERE Watt > 10 \
          GROUP BY Meta_idMeta;",
    "bins": 30,
    "xLabel": "Baseload [Watt]",
    "yLabel": "Probablility",
    "title" : ""
},

"6pm_load_distribution_10min" : {
    "query": "\
        SELECT Watt AS result \
        FROM Meter.Electricity_10min \
        WHERE \
        Watt > 20 \
        AND \
        dt LIKE \"%18:%\";",
    "bins": 30,
    "xLabel": "10 min load between 6pm and 7pm [Watt]",
    "yLabel": "Probablility",
    "title" : ""
},

"6pm_load_distribution_hour" : {
    "query": "\
        SELECT Watt AS result \
        FROM Meter.El_hour \
        WHERE \
        Watt > 20 \
        AND \
        dt LIKE \"%18:%\";",
    "bins": 30,
    "xLabel": "Load between 6pm and 7pm [Watt]",
    "yLabel": "Probablility",
    "title" : ""
}
}
bins   = 100

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

def plotHist(graphName):
    """ create the figure """
    graph = graphs[graphName]
    data = getResults(graph["query"])
    print "Average"
    mean = np.mean(data)
    print mean

    fig, ax = plt.subplots()
    # plt.hist(plotData, bins, range=(min(plotData), max(plotData)), normed=False, facecolor='green', alpha=0.5)
    plt.hist(data, graph["bins"], range=(min(data), max(data)), normed=True, facecolor='green', alpha=0.5)

    # Annotate the mean value
    plt.plot([mean, mean],ax.get_ylim())
    ax.text(mean, ax.get_ylim()[1], "Mean {:.1f}".format(mean))

    # plt.yticks(np.arange(0, 0.041, 0.01))
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    
    plt.xlabel(graph["xLabel"])
    plt.ylabel(graph["yLabel"])
    plt.savefig("../figures/{}.pdf".format(graphName), transparent=True)
    plt.savefig("../figures/{}.png".format(graphName), transparent=True)
    # plt.show()


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
    plotHist(graphName)
