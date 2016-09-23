#!/usr/bin/python

# imported by interface.py and mailer.py
import os
import csv
import MySQLdb
# import MySQLdb.cursors
import datetime            # needed to read TIME from SQL

from subprocess import call
import subprocess
from sys import stdin
import glob                 # for reading files in directory
from xml.etree import ElementTree as et  # to modify sting xml file for android
import npyscreen as nps

from meter_ini import *     # reads the database and file path information from meter_ini.py

def connectDatabase(_dbHost):
    global dbConnection
    global dbHost
    dbHost = _dbHost
    try:
        dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName, cursorclass = MySQLdb.cursors.DictCursor)
        cursor = dbConnection.cursor()
    except:
        dbHost='localhost'
        dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName, cursorclass = MySQLdb.cursors.DictCursor)
        cursor = dbConnection.cursor()
    return cursor

def getHost():
    return dbHost

def connectDatabaseOLD(_dbHost):
    # remove
    global dbConnection
    global dbHost
    dbHost = _dbHost
    try:
        dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName)
        cursor = dbConnection.cursor()
    except:
        dbHost='localhost'
        dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName)
        cursor = dbConnection.cursor()
    return cursor

def commit():
    global dbConnection
    dbConnection.commit()

def executeSQL(_sqlq):
    # to safeguard against dropped connections
    global cursor
    try:
        cursor.execute(_sqlq)
    except:
        message("Reconnect to datahase")
        cursor = connectDatabase(dbHost)
        cursor.execute(_sqlq)
    return cursor.lastrowid

def getSQL(_sqlq):
    # to safeguard against dropped connections
    global cursor
    try:
        cursor.execute(_sqlq)
    except:
        message("Need to reconnect to datahase")
        cursor = connectDatabase(dbHost)
        cursor.execute(_sqlq)
    return cursor.fetchall()

def toggleDatabase(dbHost):
    global cursor
    if (dbHost == 'localhost'):
        dbHost = '109.74.196.205'
    else:
        dbHost = 'localhost'
    cursor = connectDatabase(dbHost)

def backup_database():
    thisDate = dateTimeToday.strftime("%Y-%m-%d")
    call('mysqldump -u ' + dbUser + ' -h ' + dbHost + ' -p --databases ' + dbName +
         ' > ' + filePath + 'database/' + thisDate + '_' + dbName + '.sql', shell=True)
    message('Database backed up as ' + thisDate + '_' + dbName + '.sql')

def getNameEmail(table,criterium):
    if (table == "Contact"):
        sqlq = "SELECT Contact.idContact,Contact.Name,Contact.email\
                From Contact\
                Join Household\
                ON Household.Contact_idContact = Contact.idContact\
                WHERE %s" % criterium
    else:
        sqlq = "Select *\
                FROM %s\
                WHERE %s" % (table,criterium)
    result = getSQL(sqlq)
    return result

def getRecipientCount(table,criterium):
    return len(getNameEmail(table,criterium))

def getHouseholdCount(condition):
    # count household in database matching the modus criteria
    sqlq = "SELECT count(idHousehold) FROM Household WHERE " + condition +";"
    result = getSQL(sqlq)[0]
    return ("%s" % result['count(idHousehold)'])

def getContact(householdID):
    # return contactID for given household
    sqlq = "SELECT Contact_idContact FROM Household WHERE idHousehold = '%s';" % householdID
    result = getSQL(sqlq)[0]
    return ("%s" % result['Contact_idContact'])

def getNameOfContact(thisContactID):
    # get Contact name for a given Contact
    sqlq ="SELECT Name,Surname\
            FROM Contact \
            WHERE idContact = '%s';" % thisContactID
    result = getSQL(sqlq)[0]
    return str(result['Name']) + ' ' + str(result['Surname'])

def getSecurityCode(householdID):
    # get the security code for this household
    sqlq = "SELECT security_code FROM Household WHERE idHousehold = '%s';" % householdID 
    result = getSQL(sqlq)[0]
    return ("%s" % result['security_code'])

def getHouseholdForMeta(_metaID):
    # count household in database matching the modus criteria
    sqlq = "SELECT Household_idHousehold FROM Meta WHERE idMeta = " + _metaID +";"
    result = getSQL(sqlq)
    return ("%s" % result['Household_idHousehold'])

def getStatus(householdID):
    # get the status for this household
    sqlq = "SELECT status FROM Household WHERE idHousehold = '" + householdID + "'"
    executeSQL(sqlq)
    return ("%s" % (cursor.fetchone()))

def getDateTimeFormated(dts):
    # DateTimeString as received from database: return 31 Jan 16
    # http://strftime.org/
    if (dts != 'None'):
        f = '%Y-%m-%d %H:%M:%S'
        this_dt = datetime.datetime.strptime(dts, f)
        return this_dt.strftime("%-d %b %y")
    else:
        return "None"


def formatBox(col1, col2):
    return "\t\t\t|\t\t" + "{:<22}".format(col1) + "{:<20}".format(col2) + "|"

def formatList(col1, col2):
    return ["\t\t\t" + "{:<25}".format(col1) + "{:<30}".format(col2)]

def message(msgStr):
    # shorthand to display debug information
    nps.notify_confirm(msgStr,editw=1)

