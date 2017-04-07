#!/usr/bin/python

import sys
import getopt
import json
import MySQLdb.cursors
import db_ini as db      # database credentials

opt_hits = False

def _getJSON(filePath):
    """ returns json from file """
    datafile = open(filePath, 'r')
    return json.loads(datafile.read().decode("utf-8"))


def _connectDatabase(_dbHost):
    """ try to connect to server - else to local database """
    global dbHost
    global dbConnection
    dbHost = _dbHost
    try:
        dbConnection = MySQLdb.connect(host=db.Host, user=db.User, passwd= db.Pass, db=db.Name, cursorclass = MySQLdb.cursors.DictCursor)
        cursor = dbConnection.cursor()
    except:
        dbHost='localhost'
        dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName, cursorclass = MySQLdb.cursors.DictCursor)
        cursor = dbConnection.cursor()
    return cursor

def pathAll():
    """ call getPath for all activity id's"""
    sqlq = "SELECT idActivities FROM Activities"
    cursor.execute(sqlq)
    results = cursor.fetchall()
    print sqlq
    for result in results:
        idAct = result['idActivities']
        path  = getPath(idAct)
        if path:
            unpackPath(idAct,path)

def pathThis(idMeta):
    """ call getPath for all activity for a given idMeta """
    sqlq = "SELECT idActivities FROM Activities WHERE Meta_idMeta = '{}';".format(idMeta)
    cursor.execute(sqlq)
    results = cursor.fetchall()
    print sqlq
    for result in results:
        idAct = result['idActivities']
        path  = getPath(idAct)
        if path:
            unpackPath(idAct,path)

def getPath(idAct):
    """ return path as ?list? """
    sqlq = "SELECT Path FROM Activities WHERE idActivities = '{}';".format(idAct)
    print sqlq
    cursor.execute(sqlq)
    result = cursor.fetchall()
    path = result[0]['Path']
    if path:
        return path.split(",") 
    else:
        return False

def unpackPath(idAct, activities):
    for act in activities:
        try:
            sqlq = "INSERT INTO Path \
            (`Activities_idActivities`, `idButton`) \
            VALUES \
            ({}, {})".format(idAct,act)
            print sqlq
            cursor.execute(sqlq)
            dbConnection.commit()
        except:
            print "XXX DUD!!! XXX"
    

def main(argv):
    """ Check for arguments """
    helpStr =  'app_tree.py [ch] \n options \n [-h,--help]\t\tthis help \n [-c,--hitcount]\tshow usage of buttons'
    try:
       opts, args = getopt.getopt(argv,"a:m:ch",["hitcount","help"])
    except getopt.GetoptError:
       print helpStr
       sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
          print helpStr
          sys.exit()
        elif opt in ("-m", "--activity"):
          pathThis(arg)
        elif opt in ("-a", "--activity"):
          pathThis(arg)
        elif opt in ("-c", "--hitcount"):
          opt_hits = True
    if len(sys.argv) == 1:
        pathAll()
    print "Entry complete\n\n"


if __name__ == "__main__":
    cursor      = _connectDatabase(db.Host)
    main(sys.argv[1:])
