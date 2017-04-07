#!/usr/bin/env python
import getopt
import sys
import json
import MySQLdb.cursors
import db_ini as db     # reads the database and file path information
# override host to local
# db.Host='localhost'

# ========= #
#  GLOBALS  #
# ========= #

# with open('Definitions.json') as f:    
with open('../activities.json') as f:    
    jsonData = json.load(f)

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
        print  "INSERT INTO Legend (`table`,`column`,`value`,`meaning`) VALUES ('{}','{}','{}','{}')".format('Activities',col,jsonData['activities'][act]['ID'],jsonData['activities'][act]['title'])
        sqlq =  "INSERT INTO Legend (`table`,`column`,`value`,`meaning`) VALUES ('{}','{}','{}','{}')".format('Activities',col,jsonData['activities'][act]['ID'],jsonData['activities'][act]['title'])
        cursor.execute(sqlq)
        dbConnection.commit()

def insertJSON(jsonData):
    """ go two levels deep and insert all"""
    for column in jsonData:
        for item in jsonData[column]:
            print  "INSERT INTO Legend (`table`,`column`,`value`,`meaning`) VALUES ('{}','{}','{}','{}')".format("Individual",column,item, jsonData[column][item])
            sqlq =  "INSERT INTO Legend (`table`,`column`,`value`,`meaning`) VALUES ('{}','{}','{}','{}')".format("Individual",column,item, jsonData[column][item])
            cursor.execute(sqlq)
            dbConnection.commit()

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    cursor = connectDB()
    insertActivitiesJSON(jsonData)
    # insertJSON(jsonData)

