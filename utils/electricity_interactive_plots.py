#!/usr/bin/env python

import MySQLdb.cursors
import numpy as np #arithmetical operations
import pandas as pd #data analysis
import re #regular expressions - for searching if strings contain numbers etc.
import matplotlib.pyplot as plt #plotting
from pandas import Series, DataFrame #the book suggests this is done explicitly

import db_ini as db     # reads the database and file path information

# override host to local
# db.Host = 'localhost'

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
    "query": "SELECT Count(*) AS y,\
                tuc AS x,\
                Meta_idMeta AS label\
               FROM Activities\
               GROUP BY tuc,Meta_idMeta {};",
    "xLabel": "Activity codes [tuc]",
    "yLabel": "Mentions per person",
    "title" : "Activity frequency"
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


def getMeaningfulHouseholdColumns():
    """ get list of all household characteristics that might be applicable to electricity readings """
    colNames = []
    sqlq = "SELECT col, meaning FROM Meter.Legend \
            WHERE tab = 'Household' and VALUE = 'q' \
            AND col != 'date_choice' AND col != 'page_number' AND col != 'bill_uncertain' AND col != 'appliance_bo' AND meaning != 'Not asked';"
    cursor.execute(sqlq)
    results = cursor.fetchall()
    for result in results:
        #check if column is descriptive; if not, using 'meaning' for meaning
        meaning = result['col']
        if ( bool(re.search(r'\d', result['col']) )): 
            meaning = result['meaning']
        colNames.append( (result['col'], meaning) )
    return colNames



def offer_selection(_description, _list_of_tuples):
    """ 
        Prints entries from list, and an index alongside for selecting. 
        Each element of the list contains two entries. 
        The one without the digits gets printed as being the most descriptive.
    """
    #print preamble
    # print "\n\n", "*","-"*20,"*\n", "{:20}\n".format(_description)
    #go through the list, printing the most informative characteristic
    for characteristic in _list_of_tuples:
        char = characteristic[1]
        #if ( bool(re.search(r'\d', characteristic[0])) ): char = characteristic[1] #if column name is not descriptive (contains a digit), revert to "meaning" from the Legend table
        print "{:5}: {:20}".format(_list_of_tuples.index(characteristic), char)



def DF_getDataMetaIDStats(_graph, _condition):
    query = _graph["query"].format(_condition)
    # ===== Get data =====
    cursor.execute(query)
    results = cursor.fetchall()
    if (len(list(results)) > 0):
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
        d = df_t.describe() #produces a row of stats, but only works column by column (hence the transposition above)
    else:
        d = False
    return d



def plot_electricity_based_on_HH_column(_column_name = 'people', _plot_title = 'People'):
    graph = Electricity_graph
    # graph = Activity_graph
    """Description"""
    #1. get possible values under that column name, sorted in ascending order, with a corresponding meaning
    #!!! Important: some columns, like 'people', will have values that need to be interpreted through the legend table. Therefore we 
    #first try to legend table to see if we can get a range of possible values that column can take
    sqlq = "SELECT value, meaning FROM Meter.Legend WHERE tab = 'Household' and col = '{}' AND value != 'q' AND meaning != 'N/A'".format(_column_name)
    cursor.execute(sqlq)
    results = list(cursor.fetchall())
    #!!! However, for columns like 'pet1' the legend table only specifies the 'q', under the asumption that the values are just numerical (0 for no dogs, 1 for dogs),
    #and do not need to be interpreted. Then we pick up the range of values by querying the actual household table, and assign to them equivalent meanings
    if (len(results) == 0):
        sqlq = "SELECT distinct({}) FROM Meter.Household;".format(_column_name)
        cursor.execute(sqlq)
        results = list(cursor.fetchall())
        out = []
        for i in results:
            value = i[_column_name]
            out.append({'value': value, 'meaning': value})
        results = out
    results = sorted(results, key=lambda k: k['value']) #I DON'T THINK THIS IS WORKING 
    #2. define the mysql condition necessary to retrieve data limited by those values
    sql_proforma_condition = "AND H.{0} = {1}"
    #3. plot results in one figure
    num_results = len(results)
    num_plots = num_results + 1 #to include the overal trend plot
    if (num_plots%2 == 0):
        nrow = num_plots/2
    else:
        nrow = num_plots/2 + 1
    ncol = 2

    same_y_axis = False

    #either
    fig, axs = plt.subplots(nrow, ncol, sharex=True, sharey=same_y_axis, figsize=(8, 6))
    for i, ax in enumerate(fig.axes):
        if (i == 0): #make a general trend plot
            title = 'General Trend'
            d = DF_getDataMetaIDStats(graph, "")
        elif (i < num_plots):
            value = results[i-1]['value']
            title = results[i-1]['meaning']
            sql_condition = sql_proforma_condition.format(_column_name, value)
            print "Getting results with: ", sql_condition
            d = DF_getDataMetaIDStats(graph, sql_condition)
        if (d is not False): #because some results, e.g. averages for 4 night storage heaters, might have no electricity associated with them
            ax.plot(d.ix['mean'], label = 'Sample Size = ' + str(int(d.ix['count'][0])))
            ax.fill_between(d.ix['25%'].index, d.ix['25%'], d.ix['75%'], alpha = 0.2)
            ax.legend()
        ax.xaxis.label.set_visible(False)
        ax.set_title(title)
    if (num_plots % 2 != 0): #if odd number of plots
        print 'here'
        fig.delaxes(axs[(num_plots-1)/2, 1]) #delete the lower right axes
        for l in axs[(num_plots-1)/2 - 1, 1].get_xaxis().get_majorticklabels(): #set x ticks on the axes above
            l.set_visible(True) 
        # for l in axs[(num_plots-1)/2, 1].get_xaxis().get_majorticklabels(): #set x ticks on the axes above
        #     l.set_visible(True) 
    # or
    # plt.figure(figsize=(8, 6))
    # for i in xrange(num_plots):
    #     plt.subplot(nrow, ncol, i+1)
    #     if (i == 0): #make a general trend plotb
    #         title = 'General Trend'
    #         d = DF_getDataMetaIDStats(Electricity_graph, "")
    #     else:
    #         value = results[i-1]['value']
    #         title = results[i-1]['meaning']
    #         sql_condition = sql_proforma_condition.format(value)
    #         d = DF_getDataMetaIDStats(Electricity_graph, sql_condition)
    #     ax = plt.gca()
    #     ax.plot(d.ix['mean'])
    #     ax.fill_between(d.ix['25%'].index, d.ix['25%'], d.ix['75%'], alpha = 0.2)
    #     ax.set_title(title)

    plt.suptitle(_plot_title)
    plt.tight_layout()
    plt.savefig("WasherDryer.pdf", transparent=True)
    plt.show()



def main():
  """
  Description
  """
  characteristics = getMeaningfulHouseholdColumns()
  description_line = "Household characteristics: "
  offer_selection(description_line, characteristics)
  selection = raw_input("Select characteristic: ")
  characteristic = characteristics[int(selection)][0] #will be a column in the Household table, e.g. 'pet1', or 'people'
  description = characteristics[int(selection)][1]
  plot_electricity_based_on_HH_column(characteristic, description)




# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    cursor = connectDB() #this has to be here, outside the functions that reference it
    main()
