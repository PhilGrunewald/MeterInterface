#!/usr/bin/env python
import getopt
import sys
import json
import MySQLdb.cursors
import db_ini as db     # reads the database and file path information

# ========= #
#  GLOBALS  #
# ========= #

# override host to local
# db.Host='localhost'

# uncomment to select source file
sourceFile = '../json/LegendHousehold.json'
sourceFile = '../json/LegendIndividual.json'
sourceFile = '../json/activities.json'


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

def insertActivitiesJSON(jsonData):
    """ go two levels deep and insert all"""
    for act in jsonData['activities']:
        if (int(jsonData['activities'][act]['ID']) < 10000):
            col = 'tuc'
        elif (int(jsonData['activities'][act]['ID']) < 20000): 
            col = 'time'
        elif (int(jsonData['activities'][act]['ID']) < 30000): 
            col = 'enjoyment'
        elif (int(jsonData['activities'][act]['ID']) < 40000): 
            col = 'location'
        elif (int(jsonData['activities'][act]['ID']) < 50000): 
            col = 'people'
        elif (int(jsonData['activities'][act]['ID']) < 91000): 
            col = 'survey'
        else:
            col = 'UNDEFINED'
        sqlq =  "INSERT INTO Legend \
                (`table`,`column`,`value`,`meaning`) \
                VALUES ('{}','{}','{}','{}')".format('Activities',col,jsonData['activities'][act]['ID'],jsonData['activities'][act]['title'])
        print sqlq
        cursor.execute(sqlq)
        dbConnection.commit()

def insertJSON(jsonData):
    """ go two levels deep and insert all"""
    for column in jsonData:
        for item in jsonData[column]:
            sqlq =  "INSERT INTO Legend \
                     (`table`,`column`,`value`,`meaning`) \
                     VALUES ('{}','{}','{}','{}')".format("Individual",column,item, jsonData[column][item])
            print sqlq
            cursor.execute(sqlq)
            dbConnection.commit()

# ========= #
#   Main    #
# ========= #

def main():
    """ 
    Populates an sql table `Legend` based on json data 
    Fields are

    - `table` - the name of the sql table for which these values and meanings apply
    - `column` - the column in that table - for activities.json this takes on the definition of the tuc range (see insertActivitiesJSON)
    - `value` - the entry in this column
    - `meaning` - a plain text description of that this value means (e.g. 0:= Female)
    """
    # select source file under Globals 
    with open(sourceFile) as f:    
        jsonData = json.load(f)
    cursor = connectDB()
    if (sourceFile == '../json/activities.json'):
        insertActivitiesJSON(jsonData)
    else:
        insertJSON(jsonData)

# ========= #
#  EXECUTE  #
# ========= #

if __name__ == "__main__":
    main()
