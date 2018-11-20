#!/usr/bin/python
import MySQLdb
import interface_ini as db     # reads the database and file path information from meter_ini.py

try:
    dbConnection = MySQLdb.connect(host="energy-use.org", user=db.User, passwd= db.Pass, db=db.Name)
    cursor = dbConnection.cursor()
    print "success"
except:
    print "fail"
