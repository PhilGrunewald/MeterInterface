#!/usr/bin/python

## UPDATE Meta SET Household_idHousehold = (Household_idHousehold - 97000) WHERE Household_idHousehold >99000 AND idMeta >1000;
## UPDATE Household SET idHousehold = (idHousehold - 97000) WHERE idHousehold >99000;

## 
# ADD -- SELECT individual
# show Upcoming deployments
# upload_10min_readings is not called - use Numpi smoothing for 10 min readings
# individual = MeterApp._Forms['SelectionForm'].SelectionOptions.value

# Shortcuts:
#-----------
#action_keys        single key commands
#menu_text          main screen text
#menu_bar           the pop up menu
#display_data       display data depending on displayModus
#action_highlighted action based on line selected (enter) depending on displayModus
#statusUpdate       list of and setting of household status


import os
import csv
import MySQLdb
import datetime            # needed to read TIME from SQL

from subprocess import call
import subprocess
from sys import stdin
import glob                 # for reading files in directory
from xml.etree import ElementTree as et  # to modify sting xml file for android
import npyscreen

# For plotting
import flask                  # serve python
import json                   # used for reading activities.json
import urllib                 # to read json from github
import numpy as np            # used for mean
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

from bokeh.plotting import figure, curdoc, vplot, show
from bokeh.plotting import figure, show, output_file
from bokeh.models import Range1d, Circle

from meter_ini import *     # reads the database and file path information from meter_ini.py

app = flask.Flask(__name__)
app.config['DEBUG'] = True


modi = [ 'Processed', 'Issued', 'Upcoming', 'Future' , 'No date yet']

Criteria = {
        'Processed':    'status > 5 ORDER BY date_choice DESC',
        'Issued':       'status = 5',
        'Upcoming':     'date_choice > CURDATE() AND date_choice < CURDATE() + INTERVAL "28" DAY ORDER BY date_choice ASC',
        'Future':       'date_choice > CURDATE()',
        'No date yet':  'date_choice < "2010-01-01"',
        'no reading':   'Watt < 10',
        'high reading': 'Watt > 500'
        }

operationModus = modi[0]
timePeriod = datetime.datetime(1,1,1,4,0,0) # 4am start
contactID = '0'
metaID = '0'
individual = '0'
householdID = '0'
HouseholdIDs = [ 0,0,0,0,0 ]                            # used to store last visited HH for each modus
dataType = 'E'
participantCount = '0'
aMeterCount = '0'
eMeterCount = '0'

dateTimeToday = datetime.datetime.now()
str_date = dateTimeToday.strftime("%Y-%m-%d")
SerialNumbers   = []

def xxxUpdateStatus(void):
    # a one-off function used to get the status of legacy entries right
    sqlq="SELECT Household_idHousehold FROM Meta WHERE DataType = 'E' AND CollectionDate is not null;"
    cursor.execute(sqlq)
    result = cursor.fetchall()
    for ID in result:
        strID = ("%s" % ID)
        sqlq = "UPDATE Household SET status = 6 WHERE idHousehold = " + strID + ";"
        cursor.execute(sqlq)
    dbConnection.commit()

def connectDatabase(_dbHost):
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

def toggleDatabase(void):
    global cursor
    global dbHost
    if (dbHost == 'localhost'):
        dbHost = '109.74.196.205'
    else:
        dbHost = 'localhost'
    cursor = connectDatabase(dbHost)
    MeterApp._Forms['MAIN'].setMainMenu()

def toggleOperationModus(void):
    global operationModus
    global modi
    global householdID
    global HouseholdIDs

    modusNumber = modi.index(operationModus)
    HouseholdIDs[modusNumber] = householdID
    modusNumber = (modusNumber+1) % len(modi)
    operationModus = modi[modusNumber]
    householdID = str(HouseholdIDs[modusNumber])

    MeterApp._Forms['MAIN'].setMainMenu()
    # getHousehold()

def getDateOfFirstEntry(thisFile,col):
    # Find the date string in a data file
    # expected format: ...,2016-02-22T17:00:00.000Z,...
    # in the second column
    with open(thisFile, 'r') as f:
            firstLine = f.readline()
    dateTime = firstLine.split(',')[col]
    thisDate = dateTime[0:10]
    return thisDate

def getMetaData(MetaFile, ItemName):
    # extract content from meta file (or any other file)
    content = ""
    for line in open(MetaFile):
        if ItemName in line:
            content = line.split(ItemName + ": ", 1)[1]
    return content.strip()

def backup_database():
    thisDate = dateTimeToday.strftime("%Y-%m-%d")
    call('mysqldump -u ' + dbUser + ' -h ' + dbHost + ' -p --databases ' + dbName +
         ' > ' + filePath + 'database/' + thisDate + '_' + dbName + '.sql', shell=True)
    npyscreen.notify_confirm('Database backed up as ' + thisDate + '_' + dbName + '.sql')

def plot_data(_householdID):
    # get readings for a given metaID
    # XXX this fetches only one - could be more than one...
    metaID = getMetaID(_householdID)

    # READ ACTIVITIES.JSON
    ## THis worked fine for a while and suddenly I got "Error 503 backend read error" from github
    activity_file = urllib.urlopen('https://raw.githubusercontent.com/PhilGrunewald/MeterApp/master/www/js/activities.json').read()
    activities = json.loads(activity_file)
    # activity_file = "/Users/phil/Sites/MeterApp/www/js/activities.json"
    #with open(activity_file, "r") as f:
    #       activities = json.loads(f.read())

    # GET ELECTRICTY READINGS
    sqlq = "SELECT dt,watt FROM Electricity WHERE Meta_idMeta = "+ metaID +" AND idElectricity % 60 =0 AND watt > 20;"

    cursor.execute(sqlq)
    result = list(cursor.fetchall())
    watt=[]
    date_time=[]
    for item in result:
        date_time.append(item[0])
        watt.append(item[1])

    # get min and max values
    minWatt = min(watt) 
    maxWatt = max(watt)
    peakDateTime = date_time[[t for t,y in enumerate(watt) if y == maxWatt][0]]
    minDateTime = date_time[[t for t,y in enumerate(watt) if y == minWatt][0]]
    meanWatt = np.mean(watt)
    minTime = date_time[1]
    maxTime = date_time[-1]
    # string versions

    str_minWatt  = "{:,.0f}".format(minWatt) + " Watt"
    str_maxWatt  = "{:,.0f}".format(maxWatt) + " Watt"
    str_peakTime = str(peakDateTime.hour) + ":" +str(peakDateTime.minute) 
    str_minTime  = str(minDateTime.hour) + ":" +str(minDateTime.minute) 
    str_meanWatt = "{:,.0f}".format(meanWatt)
    str_costDay  = "{:,.0f}".format(meanWatt*24/1000*0.14)
    str_costYear = "{:,.0f}".format(meanWatt*24/1000*0.14*365)
    #p.y_range = Range1d(17, 22)

    ## TIME USE DATA
    tuc_colours = {
            'care_self':        '#66c2a5', 
            'care_other':       '#8da0cb', 
            'care_house':       '#e5c494', 
            'recreation':       '#e78ac3', 
            'travel':           '#ffd92f',
            'food':             '#a6d854',
            'work':             '#fc8d62',
            'other_category':   '#ededed'
            }
    tuc_colours_dim = {
            'care_self':        '#66c2a533', 
            'care_other':       '#8da0cb33', 
            'care_house':       '#e5c49433', 
            'recreation':       '#e78ac333', 
            'travel':           '#ffd92f33',
            'food':             '#a6d85433',
            'work':             '#fc8d6233',
            'other_category':   '#ededed33'
            }

    tuc_key     =[]
    tuc_category=[]
    tuc_ID      =[]
    tuc_location=[]
    tuc_time    =[]
    tuc_colour  =[]
    tuc_size    =[]

    sqlq = "SELECT dt_activity,activity,location FROM Activities WHERE Meta_idMeta = "+str(2301)+";"
    cursor.execute(sqlq)
    result = list(cursor.fetchall())

    for item in result:
        tuc_time.append(item[0])
        tuc_key.append(item[1])
        tuc_location.append(item[2])
        thisCat = activities['activities'][item[1]]['category']
        tuc_category.append(thisCat)
        if (str(item[2]) == "1"):
            tuc_colour.append(tuc_colours[thisCat])
            tuc_size.append(4000)
        else:
            tuc_colour.append(tuc_colours_dim[thisCat])
            tuc_size.append(6000)

    p = figure(width=800, height=350,  x_axis_type="datetime")
    #p = figure(width=800, height=350, tools="tap", x_axis_type="datetime")
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Electricity use [Watt]'

    ## Style (removal)
    ##--------------------  
    p.outline_line_width = 0
    p.outline_line_color = "white"
    #
    #p.ygrid.band_fill_alpha = 0.3
    #p.ygrid.band_fill_color = "red"
    #p.grid.bounds = (0, minWatt)
    #
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.yaxis.minor_tick_line_color = None
    #
    p.line(date_time, watt, color="green")

    time_bar = p.square(x=tuc_time, 
                        y=tuc_size, 
                        size = 5, 
                        color= tuc_colour,
                        nonselection_color="purple"
                        )

    # bands
    p.quad(top=[minWatt, meanWatt], bottom=[0, minWatt], left=[minTime, minTime],
                   right=[maxTime, maxTime], color=["blue", "gray"], fill_alpha=0.2, line_color=None)

    # p.line([minTime, maxTime], [minWatt, minWatt], color="blue")
    # p.line([minTime, maxTime], [meanWatt, meanWatt], color="gray")
    p.text([minDateTime, peakDateTime], [0, maxWatt*0.9], 
            text_color = ["blue", "red"],
            angle      = [0, 0],
            text=["Baseload: " + str_minWatt, "Peak: " + str_maxWatt])
    renderer = p.circle([minDateTime, peakDateTime], [minWatt, maxWatt], size=10, 
            fill_color=["blue","red"],
            fill_alpha=0.2,
            # set visual properties for selected glyphs
            selection_color="firebrick",
            # set visual properties for non-selected glyphs
            nonselection_fill_alpha=0.2,
            nonselection_fill_color="green",
            nonselection_line_color="firebrick",
            nonselection_line_alpha=1.0) 
    # selected_circle      = Circle(fill_alpha=0.2, fill_color="firebrick", line_color=None)
    # nonselected_circle   = Circle(fill_alpha=0.2, fill_color="red", line_color="firebrick")
    # renderer.selection_glyph = selected_circle
    # renderer.nonselection_glyph = nonselected_circle

    #p.line(date_time, setPoint, color="navy")
    plotFilePath = plotPath + str(householdID) + '.html'

    output_file(plotFilePath, title= str(householdID) + ' electricity use')
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    
    script, div = components(p, INLINE)
    show(p)
    # npyscreen.notify_confirm("pre app")
    # app.run()
    # npyscreen.notify_confirm("app started")
    # html = flask.render_template('meter_graph.html',
    #     plot_script=script,
    #     plot_div=div,
    #     js_resources=js_resources,
    #     css_resources=css_resources,
    #     _from = date_time[-1],
    #     minWatt  = str_minWatt,
    #     minTime  = str_minTime,
    #     maxWatt  = str_maxWatt,
    #     peakTime = str_peakTime,
    #     meanWatt = str_meanWatt,
    #     costDay  = str_costDay,
    #     costYear = str_costYear,
    #     name     = 'bob',
    #     metaID   = metaID
    #     )
    # # return encode_utf8(html)
    # npyscreen.notify_confirm("Graph generated: " + plotFilePath)
    # plotFile = open(plotFilePath, "w+")
    # plotFile.write(encode_utf8(html))
    # plotFile.close()
    os.system("scp " + plotFilePath + " phil@109.74.196.205:/var/www/energy-use.org/public_html/data/")


def data_download():
    # pull files from phone
    call('adb pull /sdcard/METER/ ' + filePath, shell=True)
    cmd = 'adb shell ls /sdcard/Meter/'
    s = subprocess.check_output(cmd.split())
    call('adb shell rm -rf /sdcard/Meter/*.csv', shell=True)
    call('adb shell rm -rf /sdcard/Meter/*.meta', shell=True)
    updateIDfile('0')                                           # set to 0 to avoid confusion if phone comes on again
    MeterApp.switchForm('MetaForm')


def data_review():
    MeterApp.switchForm('MetaForm')

def data_upload():
    # set up file names
    global filePath

    allMetafiles = filePath + '*.meta'
    fileList = glob.glob(allMetafiles)
    # XXX do as list iteration...
    MetaFile = fileList[0]
    fileName, void = MetaFile.split('.meta')
    uploadFile(fileName)


def add_time_use_to_file(idIndividual, idTimeUseCode, TimePeriod, timeUseActivity):
# def add_time_use(idIndividual, idTimeUseCode, TimePeriod):
    # idMeta may need to be invented - if new entry
    # Time in 1-144 for 10 minute interval

    # write to a buffer file first
    tuc_file = open(tucFilePath, "a")
    tuc_file.write(idTimeUseCode + ', ' + TimePeriod[0:5] +', ' + timeUseActivity + '\n')
    # for row in data:
    #     data_file.write("%s,%s\n" % (row[0], row[1]))
    tuc_file.close()

def identifyIndividual():
    # 1) get Household ID from Contact ID (assume 1:1 relationship)
    # 2) get all Meta IDs for Time use diaries for this household (these should have been created when sending out the diaries
    # 3) if more than one individual in household, show individuals for selection
    # return to ActionControllerData where the selection form is called
    # the calls upload_time_use_data

    sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" +\
        contactID + "'"
    cursor.execute(sqlq)
    # householdID = str(cursor.fetchone())
    householdID = ("%s" % cursor.fetchone())
   
    sqlq = "SELECT SerialNumber FROM Meta where Household_idHousehold ='" + str(householdID) + "' and DataType = 'T'"
    # sqlq = "SELECT SerialNumber FROM Meta where Household_idHousehold ='75' and DataType = 'T'"
    cursor.execute(sqlq)
    global SerialNumbers
    SerialNumbers = list(cursor.fetchall())

def upload_time_use_file():
    #### SUPERSEEDED by uploadActivityFile()


    
    # what came before:
    # MetaID for these entries has been identified
    # now the text file is read into the data base
    tuc_file = open(tucFilePath, "r")
    period = 1
    for row in tuc_file:
         col = row.split(',')
         sqlq = "INSERT INTO TimeUse(TimePeriod, TimeUseCode_idTimeUseCode,Meta_idMeta,Dishwasher)\
                 VALUES ('" + col[1] + "', '" + col[0] + "', '" + MetaID + "', '" + str(Dishwasher[period]) + "');"
         cursor.execute(sqlq)
         period += 1

    dbConnection.commit()
    tuc_file.close()



def get_time_period(timestr):
    # convert into one of 144 10minute periods of the day
    factors = [6, 0.1, 0.00167]
    return sum([a*b for a, b in zip(factors, map(int, timestr.split(':')))])

def period_hhmm(intPeriod):
    dateTimeValue = datetime.datetime(1,1,1,4,0,0) + datetime.timedelta(minutes = (intPeriod-1) * 10)
    return str(dateTimeValue.time())[0:5]

def next_period(thisTime):
    # advances datetime object by 10 minutes, e.g. '04:50:00' -> '05:00:00'
    return thisTime + datetime.timedelta(minutes = 10)
    
def time_in_seconds(timestr): # not used - just kept for reference...
    # '00:01:01' -> 61
    factors = [3600, 60, 1]
    return sum([a*b for a, b in zip(factors, map(int, timestr.split(':')))])

def getReadingPeriods(_householdID,_condition,_duration):
    # returns start and end of consequitive records matching the condition
    # used to identify how long 'no readings' were taken, or 'high readings'
    metaID = getMetaID(_householdID)        # only fetches the first (should only be one...)
    if (metaID != 'None'):
        sqlq = "SELECT idElectricity FROM Electricity WHERE " + _condition +\
            " AND Meta_idMeta = " + metaID + " ORDER BY dt"
        cursor.execute(sqlq)
        eIDs = cursor.fetchall()
        if eIDs:
            prevID   =  int("%s" % eIDs[0])
            startIDs = [prevID]
            endIDs   = []
            durations= []
        
            for eID in eIDs:
                eID = int("%s" % eID)
                if (eID != (prevID+1)):
                    endIDs.append(prevID)
                    startIDs.append(eID)
                prevID = eID
            endIDs.append(prevID)

            for i in range(len(endIDs)):
                duration = endIDs[i]-startIDs[i]
                if (duration > _duration):
                    durations.append(duration/60)
            if (len(durations) > 5):
                return len(durations)
            else:
                return durations   
        else:
            return "none"
    else:
        return "no meta entry"


def upload_10min_readings(idMeta=20):
    # calc the average for each 10 min period and write to database
    sqlq = "SELECT Time,Watt FROM Electricity WHERE Meta_idMeta = '" +\
        str(idMeta) + "' ORDER BY Time"
    cursor.execute(sqlq)
    eReadings = cursor.fetchall()

    period = 1
    thisPeriodSum = 0
    thisPeriodCounter = 1

    for thisLine in eReadings:
        if get_time_period("%s" % (thisLine[0])) < period:
            thisPeriodSum = thisPeriodSum + float(thisLine[1])
            thisPeriodCounter += 1
        else:  # entered next period -> write average of last period and reset
            if (thisPeriodCounter == 1):
                        # if no readings, set value to -1 as error flag
                thisPeriodSum = -1
            sqlq = "INSERT INTO Electricity_periods(Period,Watt,Meta_idMeta)\
                VALUES ('" + str(period) + "', '" +\
                str(thisPeriodSum/thisPeriodCounter) + "', '" + \
                str(idMeta) + "')"
            cursor.execute(sqlq)
            period += 1
            thisPeriodSum = float(thisLine[1])
            thisPeriodCounter = 1
    # one more time at the end to make sure we get the last period as well
    if (thisPeriodCounter == 1):  # if no readings set value to -1 as error flag
        thisPeriodSum = -1
    sqlq = "INSERT INTO Electricity_periods(Period,Watt,Meta_idMeta) \
        VALUES ('" + str(period) + "', '" +\
        str(thisPeriodSum/thisPeriodCounter) + "', '" + str(idMeta) + "')"
    cursor.execute(sqlq)

def uploadDataFile(fileName,dataType,_metaID,collectionDate):  
    global metaID
    global householdID
    metaID = _metaID
    householdID = getHouseholdForMeta(metaID)

    # put file content into database
    dataFile = fileName + '.csv'
    dataFileName = os.path.basename(dataFile)


    if (dataType == 'E'):
        os.system("scp " + dataFile + " phil@109.74.196.205:/home/phil/meter")
        sqlq = "LOAD DATA INFILE '/home/phil/meter/" + dataFileName + "' INTO TABLE Electricity FIELDS TERMINATED BY ',' (dt,Watt) SET Meta_idMeta = " + str(metaID) + ";"
        cursor.execute(sqlq)
        updateHouseholdStatus(householdID,6)
    else:
        csv_data = csv.reader(file(dataFile))
        if (dataType == 'I'):
            sqlq = "INSERT INTO Individual(Meta_idMeta) VALUES('"+str(metaID)+"')"
            cursor.execute(sqlq)                             # create an entry
            dbConnection.commit()
            individualID = cursor.lastrowid                  # get the id of the entry just made
            for row in csv_data:                             # populate columns
                sqlq = "UPDATE Individual SET " + row[1] + " = '" + row[2] + "'\
                        WHERE idIndividual = '"+str(individualID)+"';"
                cursor.execute(sqlq)
        if (dataType == 'A'):
            for row in csv_data:                                                       # insert each line into Activities
                sqlq = "INSERT INTO Activities(Meta_idMeta,dt_activity,dt_recorded,tuc,category,activity,location,people,enjoyment) \
                        VALUES('"+row[0]+"', '"+row[1]+"', '"+row[2]+"', '"+row[3]+"', '"+row[4]+"', '"+row[5]+"', '"+row[6]+"', '"+row[7]+"', '"+row[8]+"')"
                cursor.execute(sqlq)
    # update meta entry - this MUST already exist!
    # we don't want 'I' in the Meta table - only E or A
    if (dataType == 'I'):
        dataType = 'A'
    sqlq = "UPDATE Meta SET \
            `DataType`='"+ dataType +"', \
            `CollectionDate`='"+ collectionDate +"'\
            WHERE `idMeta`='" +metaID+"';"
    cursor.execute(sqlq)
    dbConnection.commit()
    # npyscreen.notify_confirm(dataType + " data for HH " +householdID+ " now in database")

def data_download_upload(self):
    # call upload and download
    data_download()
    data_upload()

def diary_setup():
    # 2 Nov 15 - create a meta file entry and generate ID
    global MetaID
    # 1) get household ID (assuming a 1:1 relationship!)
    sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '"\
        + contactID + "'"
    cursor.execute(sqlq)
    householdID = ("%s" % cursor.fetchone())

    sqlq = "INSERT INTO Meta(DataType, Household_idHousehold) \
           VALUES ('T', '" + householdID + "')"
    cursor.execute(sqlq)
    dbConnection.commit()
    MetaID = cursor.lastrowid
    npyscreen.notify_confirm('Diary ID' + str(MetaID) + 'has been created')

def getMetaIDs(householdID, deviceType):
    # check if eMeter has been configured
    sqlq = "SELECT idMeta FROM Meta WHERE DataType = '"+deviceType+"' AND Household_idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    return cursor.fetchall()
    

def getDeviceMetaIDs(householdID, deviceType):
    # check if eMeter has been configured
    sqlq = "SELECT idMeta FROM Meta WHERE DataType = '"+deviceType+"' AND Household_idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    results = cursor.fetchall()
    metaIDs = ''
    for result in results:
        metaIDs = metaIDs + ("{:<6}".format("%s" % result))
    return metaIDs

def getParticipantCounters(householdID):
    counters = getParticipantCount(householdID)
    clist = ''
    for counter in range(counters):
        clist = clist + ("{:<6}".format("%s" % (counter + 1)))
    return clist


def getHouseholdForMeta(_metaID):
    # count household in database matching the modus criteria
    sqlq = "SELECT Household_idHousehold FROM Meta WHERE idMeta = " + _metaID +";"
    cursor.execute(sqlq)
    return ("%s" % cursor.fetchone())

def getHouseholdCount():
    # count household in database matching the modus criteria
    sqlq = "SELECT count(idHousehold) FROM Household WHERE " + Criteria[operationModus] +";"
    cursor.execute(sqlq)
    return ("%s" % cursor.fetchone())

def getDeviceCount(householdID, deviceType):
    # check if eMeter has been configured
    sqlq = "SELECT count(idMeta) FROM Meta WHERE DataType = '"+deviceType+"' AND Household_idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    # Count = ("%s" % cursor.fetchone())
    return cursor.fetchone()
    
    # check if aMeter has been configured
    sqlq = "SELECT count(idMeta) FROM Meta WHERE DataType = 'A' AND Household_idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    aMeterCount = ("%s" % cursor.fetchone())

def getNameOfContact(thisContactID):
    # get Contact name for a given Contact
    sqlq ="SELECT Name,Surname\
            FROM Contact \
            WHERE idContact = '" + thisContactID + "';"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    return str(result[0]) + ' ' + str(result[1])

def getContactName(householdID):
    # disused
    # XXX always returned "Phil Grunewald" - presumably picking contact = 0 ??!
    # get Contact name for a given household
    sqlq ="SELECT Contact_idContact\
            FROM Household \
            WHERE idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    thisContact = str(cursor.fetchone())
    return getNameOfContact(thisContact)

def getSecurityCode(householdID):
    # get the security code for this household
    sqlq = "SELECT security_code FROM Household WHERE idHousehold = '" + householdID + "'"
    cursor.execute(sqlq)
    return ("%s" % (cursor.fetchone()))

def getStatus(householdID):
    # get the status for this household
    sqlq = "SELECT status FROM Household WHERE idHousehold = '" + householdID + "'"
    cursor.execute(sqlq)
    return ("%s" % (cursor.fetchone()))

def getParticipantCount(householdID):
    # get number of diaries required
    sqlq ="SELECT age_group2, age_group3, age_group4, age_group5, age_group6\
            FROM Household \
            WHERE idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    return int(result[0]) + int(result[1]) + int(result[2]) + int(result[3]) + int(result[4])

def getHousehold():
    ## DISUSED
    # get the next hh matching the modus criteria
    global householdID
    global contactID
    sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE " + Criteria[operationModus] +";"
    cursor.execute(sqlq)
    result =  cursor.fetchone()
    if (result):
        householdID =  ("%s" % result[0])
        contactID   =  ("%s" % result[1])

def getPreviousHousehold(void):
    # get the next hh matching the modus criteria
    global householdID
    global contactID
    sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE idHousehold < " + householdID + " AND " + Criteria[operationModus] +";"
    # sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE " + Criteria[operationModus] +" AND idHousehold < " + householdID +" ORDER BY idHousehold DESC;"
    cursor.execute(sqlq)
    result =  cursor.fetchone()
    if (result):
        householdID =  ("%s" % result[0])
        contactID   =  ("%s" % result[1])
    MeterApp._Forms['MAIN'].setMainMenu()

def getNextHousehold(void):
    # get the next hh matching the modus criteria
    global householdID
    global contactID
    sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE idHousehold > " + householdID + " AND " + Criteria[operationModus] +";"
    cursor.execute(sqlq)
    result =  cursor.fetchone()
    if (result):
        householdID =  ("%s" % result[0])
        contactID   =  ("%s" % result[1])
    MeterApp._Forms['MAIN'].setMainMenu()


def getNextHouseholdForParcel(void):
    global householdID
    global contactID
    global str_date
    # get the household that has the nearest chosen date
    sqlq ="SELECT idHousehold, Contact_idContact, date_choice \
            FROM Household \
            WHERE date_choice > CURDATE() AND status = 0 ORDER BY date_choice ASC LIMIT 1;"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    householdID = ("%s" % result[0])
    contactID   = ("%s" % result[1])
    str_date    = ("%s" % result[2])
    MeterApp._Forms['MAIN'].setMainMenu()


def updateHouseholdStatus(householdID, status):
    # update status of household                            #statusUpdate
    # only case 3,5,6 and 7 dealt with here. others from php forms.
    # 0 : hhq incomplete                hhq.php
    # 1 : hhq complete but no date      hhq.php
    # 2 : date selected                 hhq.php 
    # 3 : 2 week warning sent           compose_email('confirm')
    # 4 : date confirmed                confirm.php
    # 5 : kit sent                      phone_id_setup()
    # 6 : data uploaded                 uploadDataFile()
    # 7 : data emailed to participant   compose_email('graph')
    # 8 : participant made annotations
    sqlq = "UPDATE Household \
            SET `status`="+ str(status) +"\
            WHERE `idHousehold` ='" + str(householdID) + "';"
    cursor.execute(sqlq)
    dbConnection.commit()


def phone_id_setup(meterType):
    # 2 Nov 15 - assumes that the apps are already installed
    global metaID
    global householdID
    # 1) get household ID (assuming a 1:1 relationship!)
    # sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '"\
    #     + str(contactID) + "'"
    # cursor.execute(sqlq)
    # householdID = ("%s" % cursor.fetchone())

    # 2) create a meta id entry for an 'eMeter'
    sqlq = "INSERT INTO Meta(DataType, Household_idHousehold) \
           VALUES ('"+ meterType +"', '" + householdID + "')"
    cursor.execute(sqlq)
    dbConnection.commit()
    metaID = str(cursor.lastrowid)
    updateIDfile(metaID)

    if (meterType == 'E'):
        # only need this once per household
        print_letter()
        updateHouseholdStatus(householdID,5)

    MeterApp._Forms['MAIN'].wStatus2.value =\
        "Phone was assigned ID " + metaID
    MeterApp._Forms['MAIN'].wStatus2.display()
    MeterApp._Forms['MAIN'].setMainMenu()

def updateIDfile(_id):
    idFile = open(idFilePath, 'w+')
    idFile.write(str(_id))
    idFile.close()
    # XXX only needs doing once, but flashing doesn't seem to create this folder
    call('adb shell mkdir /sdcard/METER', shell=True)
    call('adb push ' + idFilePath + ' /sdcard/METER/', shell=True)
    call('adb shell date -s `date "+%Y%m%d.%H%M%S"`',  shell=True)
    # shut down phone (unless id is 0, i.e. the phone still needs setting up)
    if (_id):
        call('adb shell reboot -p',  shell=True)


def aMeter_setup():
    # compile and upload the cordova activity app
    call('/Users/phil/Sites/MeterApp/platforms/android/cordova/run', shell=True)
    # install AutoStart app
    call('adb install ~/Software/Android/AutoStart_2.1.apk',
         shell=True)
    # configure phone for recording
    phone_id_setup('A')

def root_phone():
    call('adb install -r ./apk/root.apk',  shell=True)
    call('adb install -r ./apk/Insecure.apk',  shell=True)
    call('adb install -r ./apk/Flashify.apk',  shell=True)
    call('adb push ./apk/recovery.img /sdcard/',  shell=True)
    npyscreen.notify_confirm("Complete process\n1) connect to WiFi\n2) run KingoRoot\n3) in Insecure check adbd at boot\n4) Flashify > Recovery image > choose a file \"/sdcard/recovery.img\" >yup (2min)\n5) Press <Home> Flash e/aMeter (this Menu)")

def flash_phone(meterType):
    call('adb install -r ./apk/root.apk',  shell=True)
    call('adb install -r ./apk/Insecure.apk',  shell=True)
    call('adb install -r ./apk/Flashify.apk',  shell=True)
    call('adb push ./apk/recovery.img /sdcard/',  shell=True)
    npyscreen.notify_confirm("Complete process\n1) connect to WiFi\n2) run KingoRoot\n3) in Insecure check adbd at boot\n4) Flashify > Recovery image > choose a file \"/sdcard/recovery.img\" >yup (2min)\n5) Press <Home> Flash e/aMeter (this Menu)")
    # restore phone from Mater copy
    if (meterType == 'E'):
        call('adb push ./flash_eMeter/ /sdcard/',  shell=True)
    elif (meterType == 'A'):
        call('adb push ./flash_aMeter/ /sdcard/',  shell=True)
    call('adb reboot recovery',  shell=True)
    npyscreen.notify_confirm("Phone restarting\n1) Restore \n2) Select \"... KitKat\" \n3) swipe (2min) \n4) Reboot System\n5) assign a/eMeter ID (this Menu)")

def eMeter_setup():
    # superseeded by flash_phone()
    # Compile and run phone_id_setup(E)
    # XXX call('ant debug -f ~/Software/Android/DMon/build.xml', shell=True)
    # remove old copy
    # XXX call('adb uninstall com.Phil.DEMon', shell=True)
    # install new
    # call('adb install -r \
    #     ~/Software/Android/DMon/bin/MainActivity-debug.apk',
    #      shell=True)
    # install AutoStart app
    call('adb install -r ./apk/AppHider.apk',  shell=True)
    call('adb install -r ./apk/AutoStart.apk',  shell=True)
    call('adb install -r ./apk/eMeter.apk',  shell=True)

    # create the METER folder
    call('adb shell mkdir /sdcard/METER', shell=True)
    # configure phone for recording
    phone_id_setup('E')

def getMetaID(_householdID):
    # should be superseeded by getMetaIDs()
    # return contactID for given household
    sqlq = "SELECT idMeta FROM Meta WHERE DataType = 'E' AND Household_idHousehold = '" + _householdID + "' ORDER BY idMeta DESC LIMIT 1"
    cursor.execute(sqlq)
    return ("%s" % cursor.fetchone())

def getContact(householdID):
    # return contactID for given household
    sqlq = "SELECT contact_idContact FROM Household WHERE idHousehold = '" + householdID + "'"
    cursor.execute(sqlq)
    return ("%s" % cursor.fetchone())

def getDateChoice(householdID):
    # return collection data as a string: Sun, 31 Dec
    sqlq = "SELECT date_choice FROM Household WHERE idHousehold = '" + householdID + "'"
    cursor.execute(sqlq)
    dateStr = ("%s" % cursor.fetchone())
    if (dateStr != 'None'):
        f = '%Y-%m-%d'
        this_dt = datetime.datetime.strptime(dateStr, f)
        return this_dt.strftime("%a, %-d %b")
    else:
        return "None"

def getDateTimeFormated(dts):
    # DateTimeString as received from database: return 31 Jan 16
    # http://strftime.org/
    if (dts != 'None'):
        f = '%Y-%m-%d %H:%M:%S'
        this_dt = datetime.datetime.strptime(dts, f)
        return this_dt.strftime("%-d %b %y")
    else:
        return "None"

def XXXgetCollectionDate(householdID):
    # superseeded by getDateChoice
    # return collection data as a string: Sunday, 31 December
    sqlq = "SELECT date_choice FROM Household WHERE idHousehold = '" + householdID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    strCollectionDate = ("%s" % (result[0]))
    dateArray = strCollectionDate.split('-')
    CollectionDate = datetime.date(int(dateArray[0]), int(dateArray[1]), int(dateArray[2]))
    return CollectionDate.strftime("%A, %e %B")



def compose_email(type,edit=True):
    # Contact participant with editabel email
    # edit = False -> send immediately
    global householdID

    # get contact details
    contactID = getContact(householdID)
    metaID    = getMetaID(householdID)

    sqlq = "SELECT Name, Surname, Address1,Address2,Town,Postcode,email \
            FROM Contact \
            WHERE idContact = '"\
        + contactID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    thisName    = ("%s %s" % (result[0:2]))
    thisAddress = ("%s</br>%s</br>%s %s" % (result[2:6]))
    thisAddress = thisAddress.replace("None </br>", "")
    thisDate    = getDateChoice(householdID)
    thisEmail   = ("%s" % (result[6]))
    CcEmail     = 'philipp.grunewald@ouce.ox.ac.uk'

    thisAddress = thisAddress.replace("None</br>", "")

    participantCount = ("%s" % getParticipantCount(str(householdID)))

    # prepare the custom email
    # templateFile = open(emailPath + "email_compose_" + type + ".md", "r")
    templateFile = open(emailPath + "email_" + type + ".html", "r")
    templateText = templateFile.read()
    templateFile.close()

    templateText = templateText.replace("[householdID]", householdID)
    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[address]", thisAddress)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[metaID]", metaID)
    templateText = templateText.replace("[securityCode]", getSecurityCode(householdID))
    templateText = templateText.replace("[participantCount]", participantCount)

    if (participantCount != "1"):
        templateText = templateText.replace("[s]", "s")
        templateText = templateText.replace("[people]", "people")
        templateText = templateText.replace("{multiple booklets}", ". Each of you is encouraged to take part (so long as they are eight or older). I hope you will be able to persuade them to join you")
    else:
        templateText = templateText.replace("[s]", "")
        templateText = templateText.replace("[people]", "person")
        templateText = templateText.replace("{multiple booklets}", "") 

    if (edit):
        # needs email in line 1, Cc in line 2 and Subject in line 3
        # template has subject as line one -> insert emails
        templateText = thisEmail + '\n' + CcEmail + '\n' + templateText
    else:
        # only keep the body of the text -> remove line 1 (Subject)
        subjectLine = templateText.splitlines()[0]
        templateText = templateText[templateText.find('\n')+1:]     # find line break and return all from there - i.e. remove first line

    emailFilePath = emailPath + "tempEmail.htmail"
    emailFile = open(emailFilePath, "w+")
    emailFile.write(templateText)
    emailFile.close()

    if (type == 'confirm'):
        updateHouseholdStatus(householdID, 3)
    elif (type == 'graph'):
        # households that had been 'processed' and now 'processed and contacted'
        updateHouseholdStatus(householdID, 7)
    
    if (edit):
        call('vim ' + emailFilePath, shell=True)
    else:
        call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + thisEmail + ' -b philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath, shell=True)

def email_many():
    # compose message
    emailFilePath = emailPath + "email_many.html"
    # give oportunity to edit the template
    call('vim ' + emailFilePath, shell=True)

    templateFile = open(emailFilePath, "r")
    templateText = templateFile.read()
    templateFile.close()

    subjectLine = templateText.splitlines()[0]
    templateText = templateText[templateText.find('\n')+1:]     # find line break and return all from there - i.e. remove first line

    # personalise
    emailPathPersonal = emailPath + "email_personal.html"
    sqlq="SELECT Name,email FROM Mailinglist WHERE scope = 'test'"
    cursor.execute(sqlq)
    results = list(cursor.fetchall())
    for result in results:
        # npyscreen.notify_confirm(str(result))
        emailText = templateText.replace("[name]", result[0])
        emailAddress = result[1]
        emailFile = open(emailPathPersonal, "w+")
        emailFile.write(emailText)
        emailFile.close()
        call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + ' < ' + emailPathPersonal, shell=True)



def pre_parcel_email(householdID):
    # send an email to check contact details are right
    contactID = getContact(householdID)

    # get contact details
    sqlq = "SELECT Name, Surname, Address1,Address2,Town,Postcode,email FROM Contact WHERE idContact = '"\
        + contactID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    thisName    = ("%s %s" % (result[0:2]))
    thisAddress = ("%s</br>%s</br>%s %s" % (result[2:6]))
    thisAddress = thisAddress.replace("None </br>", "")
    thisDate    = getDateChoice(householdID)
    thisEmail   = ("%s" % (result[6]))
    thisEmail = "mail@philippshome.de"

    # prepare the custom email
    templateFile = open(emailPath + "pre_parcel_email.html", "r")
    templateText = templateFile.read()
    templateFile.close()

    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[address]", thisAddress)
    templateText = templateText.replace("[householdID]", householdID)
    templateText = templateText.replace("[securityCode]", getSecurityCode(householdID))

    participantCount = ("%s" % getParticipantCount(str(householdID)))
    templateText = templateText.replace("[participantCount]", participantCount)

    if (participantCount != "1"):
        templateText = templateText.replace("[s]", "s")
        templateText = templateText.replace("{multiple booklets}", ". Each of you is encouraged to take part (so long as they are eight or older). I hope you will be able to persuade them to join you")
    else:
        templateText = templateText.replace("[s]", "")
        templateText = templateText.replace("{multiple booklets}", "") 

    emailFilePath = emailPath + "tempEmail.mail"
    emailFile = open(emailFilePath, "w+")
    emailFile.write(templateText)
    emailFile.close()
    call('mutt -e "set content_type=text/html" -s "[Meter] Ready for your Meter day on ' +thisDate+ '?" ' + thisEmail + ' -b philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath, shell=True)
    updateHouseholdStatus(householdID,3)
    # email contains link to take status to 4: confirmed        

def print_letter():
    # personal letter as pdf
    global householdID
    contactID = getContact(householdID)
    participantCount = ("%s" % getParticipantCount(str(householdID)))

    # The letter
    dateToday = datetime.datetime.now()
    todayDate = dateToday.strftime("%e %B %Y")

    sqlq = "SELECT Name, Surname, Address1,Address2,Town,Postcode FROM Contact WHERE idContact = '"\
        + contactID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    thisName    = ("%s %s" % (result[0:2]))
    thisAddress = ("%s\n\n %s \n\n%s %s" % (result[2:6]))
    thisAddress = thisAddress.replace("None ", "")
    thisDate = getDateChoice(householdID)

    letterFile = letterPath + contactID + "_letter"
    letterTemplate = letterPath + "letter.md"
    templateFile = open(letterTemplate, "r")
    templateText = templateFile.read()
    templateFile.close()

    templateText = templateText.replace("[address]", thisAddress)
    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[today]", todayDate)
    templateText = templateText.replace("[participantCount]", participantCount)
    if (participantCount != "1"):
        templateText = templateText.replace("[s]", "s")
        templateText = templateText.replace("{multiple booklets}", " -- one for each household member above the age of eight. Do encourage the others to join you. The more people fill in their booklet, the better our understanding of electricity use becomes")
    else:
        templateText = templateText.replace("[s]", "")
        templateText = templateText.replace("{multiple booklets}", "") 

    myFile = open(filePath + "temp_letter.md", "w+")
    myFile.write(templateText)
    myFile.close()

    call('pandoc -V geometry:margin=1.3in -V fontsize=11pt ' + filePath + "temp_letter.md -o" + letterFile + ".pdf", shell=True)
    # call('pandoc -V fontsize=11pt ' + filePath + "temp_letter.md -o" + letterFile + ".pdf", shell=True)

    # ADDRESS LABEL
    # produces postage label and personal letter
    toAddress = thisName + "\n\n" + thisAddress

    myFile = open(letterPath + "address.md", "a")
    myFile.write(toAddress)
    myFile.write("\\vspace{10 mm}\n\n")
    myFile.close()
    call('pandoc -V geometry:margin=0.8in ' + letterPath + "address.md -o" +
         letterPath + "address.pdf ", shell=True)
    call('lp -d Xerox_Phaser_3250 ' + letterFile + '.pdf', shell=True)

def formatBox(col1, col2):
    return "\t\t\t|\t\t" + "{:<12}".format(col1) + "{:<30}".format(col2) + "|"


# ------------------------------------------------------------------------------
# --------------------------FORMS-----------------------------------------------
# ------------------------------------------------------------------------------

class ActionControllerData(npyscreen.MultiLineAction):
    # action key shortcuts                                      #action_keys
    def __init__(self, *args, **keywords):
        super(ActionControllerData, self).__init__(*args, **keywords)
        global MenuActionKeys
        MenuActionKeys = {
            # '1': self.eMeter_setup,
            #   'p': self.eMeter_setup,
            # 'A': print_letter,
            'A': self.btnA,
            ## 'A': self_pre_post_email,
            'D': self.aMeter_id_setup,
            'E': self.btnE,
            # 'E': self.eMeter_id_setup,
            '>': getNextHousehold,
            '<': getPreviousHousehold,
            # 'N': getNextHouseholdForParcel,

            'P': self.btnP,
            # 'P': self.data_download,
            'S': self.showHouseholds,
            "M": toggleOperationModus,
            "H": self.show_MainMenu,
            "X": self.parent.exit_application,
            # "u": self.data_upload,
            # "D": data_download_upload,
            # "C": self.show_TimeUse,
            # "t": self.show_DataTypes,
            # "c": self.show_Contact,
            # "a": self.show_NewContact,
            # "i": self.show_NewIndividual,
            # "I": self.show_Individual,
            # "m": self.show_MetaForm,
            # "s": self.show_MainMenu,
            # '5': self.add_nTimeUse ,
        }
        self.add_handlers(MenuActionKeys)


    def actionHighlighted(self, selectedLine, keypress):
        # choose action based on the display status and selected line           #action_highlighted
        global householdID 
        global contactID
        global str_date 
        global metaID
        global individual 
        global paticipantCount
        global eMeterCount
        global aMeterCount
        global dataType

        if (self.parent.myStatus == 'Main'):
            self.parent.wMain.values = ['Selection: ', selectedLine,
                                        '\tM\t\t to return to the main menu']
            self.parent.wMain.display()
            global MenuActionKeys
            MenuActionKeys[selectedLine[1]]()

        elif (self.parent.myStatus == 'Contact'):
            dataArray = selectedLine.split(',')
            contactID = str(dataArray[0])
            self.parent.wStatus2.value =\
                "Contact changed to " + str(dataArray[1])
            self.parent.identifyHousehold()
            # self.parent.wStatus2.display()
            # self.parent.setMainMenu()

        elif (self.parent.myStatus == 'Diaries'):
            dataArray = selectedLine.split('\t')
            metaID = str(dataArray[0])
            self.parent.wStatus2.value =\
                "Diary ID " + metaID + " ready for entry"
            self.parent.wStatus2.display()
            # self.parent.setMainMenu()
            self.parent.show_TimeUseEntryScreen()

        elif (self.parent.myStatus == 'XXXDiaries'):
            dataArray = selectedLine.split('\t')
            metaID    = str(dataArray[0])
            self.parent.wStatus2.value =\
                "Diary ID " + str(dataArray[0]) + " for Household " + str(dataArray[2]) + " selected"
            self.parent.wStatus2.display()
            # self.parent.setMainMenu()
            self.parent.show_TimeUseEntryScreen()

        elif (self.parent.myStatus == 'Households'):
            # items are padded out with spaces to produce neat columns. These are removed with .strip()
            dataArray   = selectedLine.split('\t')
            householdID = str(dataArray[0]).strip()
            contactID   = str(dataArray[1]).strip()
            str_date    = str(dataArray[2]).strip()
            self.parent.wStatus2.value =\
                "Household changed to " + householdID +\
                " for Contact " + contactID +\
                " on " + str_date
            self.parent.wStatus2.display()
            self.parent.setMainMenu()


        elif (self.parent.myStatus == 'Meta'):
            dataArray = selectedLine.split('\t\t')
            metaID  = str(dataArray[0])
            dataType = str(dataArray[3])
            self.parent.wStatus2.value =\
                "Meta " + metaID + ", type " + dataType
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

        elif (self.parent.myStatus == 'Household'):
            dataArray = selectedLine.split('\t')
            householdID  = str(dataArray[0])
            self.parent.wStatus2.value =\
                "Household changed to " + str(dataArray[0])
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

        elif (self.parent.myStatus == 'Individual'):
            dataArray = selectedLine.split('\t')
            individual  = str(dataArray[0])
            self.parent.wStatus2.value =\
                "Individual changed to " + str(dataArray[2]) + " from household " + str(dataArray[0])
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

        elif (self.parent.myStatus == 'Tables'):
            self.parent.wStatus2.values = ['Table ', selectedLine, 'was selected!']
            self.parent.wStatus2.display()
            self.parent.display_selected_data(selectedLine)

        elif (self.parent.myStatus == 'TimeUseCode'):
            timeUseArray = selectedLine.split('\t')         # the time use code is left of the two tabs and acts as ID
            global idTimeUseCode
            idTimeUseCode = str(timeUseArray[0])
            global timeUseActivity
            timeUseActivity = str(timeUseArray[2])
            self.add_TimeUse()
            self.parent.display_selected_data('TimeUseCode')

        elif (self.parent.myStatus == 'DataTypes'):
            dataTypeArray = selectedLine.split('\t')
            dataType = str(dataTypeArray[0])
            self.parent.wStatus2.value =\
                "Data type changed to " + str(dataTypeArray[2])
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

    def btnA(self, *args, **keywords):
        print_letter()
        if (operationModus == 'X'):
            pre_parcel_email(householdID)
        elif (operationModus == 'Upcoming'):
            pre_parcel_email(householdID)

    def btnE(self, *args, **keywords):
        if (operationModus == 'Processed'):
            compose_email('graph')
        if (operationModus == 'Issued'):
            compose_email('request_return')
        elif (operationModus == 'Upcoming'):
            phone_id_setup('E')

    def btnP(self, *args, **keywords):
        if (operationModus == 'Processed'):
            plot_data(householdID)
        elif (operationModus == 'Issued'):
            data_download()

    def show_MainMenu(self, *args, **keywords):
        self.parent.setMainMenu()

    def aMeter_id_setup(self, *args, **keywords):
        phone_id_setup('A')
        
    def showHouseholds(self, *args, **keywords):
        self.parent.display_selected_data('Households')

    def data_download(self, *args, **keywords):
        data_download()

    def data_upload(self, *args, **keywords):
        data_upload()

    def edit_TimeUse(self, *args, **keywords):
        subprocess.call(['vim', tucFilePath])   

    def enter_Other(self, *args, **keywords):
        self.parent.myStatus = 'TimeUseCodeOther'
        self.parent.display_selected_data("TimeUseCodeOther")
        self.parent.wStatus2.value = "d: dishwasher, W.ashing machine | T.umble dryer | H.ome"
        self.parent.wStatus2.display()

    def add_Dishwasher(self, *args, **keywords):
        # set Dishwasher to '1' for current period
        global timeIndex 
        Dishwasher[timeIndex] = 1
        npyscreen.notify_confirm('Dishwasher is go for period ' + str(timeIndex))

    def show_TimeUse(self, *args, **keywords):
        # time use action keys
        # self.parent.parentApp.switchForm('TimeUse')
        global TimeUseActionKeys
        TimeUseActionKeys = {
            "6": self.add_nTimeUse,
            'e': self.edit_TimeUse,     # open vim
            'a': self.enter_Other,     # show list of times for appliances, location and 'others'
            'd': self.add_Dishwasher,     # add Dishwasher use for current period
           #  'c': self.commit_TimeUse,     # upload to database
                }

        self.add_handlers(TimeUseActionKeys)

        self.parent.myStatus = 'Diaries'
        self.parent.display_selected_data("Diaries")
        self.parent.wStatus2.value =\
            "select code for " + str(timePeriod.time())
        self.parent.wStatus2.display()




    def add_TimeUse(self, *args, **keywords):
        # need to pass relevant parameters (or use globals ?!)
        global Activity1
        global idTimeUseCode 
        global timePeriod
        global timeIndex
        global timeUseActivity

        # *** Major change!!
        # *** Add the meta line
        # *** Upload the FILE in one go
        Activity1.append(idTimeUseCode)

        add_time_use_to_file(individual, idTimeUseCode, str(timePeriod.time()), timeUseActivity)
        timePeriod = next_period(timePeriod)
        timeIndex += 1
        self.parent.wStatus2.value =\
            str(timePeriod.time()) + ' ' + timeUseActivity +  ' set'
        self.parent.wStatus2.display()

    def add_nTimeUse(self, *args, **keywords):
        # try to pass number of entries as parameter
        global idTimeUseCode 
        global timePeriod
        for i in range(6):
            add_time_use_to_file(individual, idTimeUseCode, str(timePeriod.time()))
            timePeriod = next_period(timePeriod)

    def show_DataTypes(self, *args, **keywords):
        self.parent.myStatus = 'DataTypes'
        self.parent.display_selected_data("DataTypes")

    def show_Contact(self, *args, **keywords):
        self.parent.myStatus = 'Contact'
        self.parent.display_selected_data("Contact")

    def show_Individual(self, *args, **keywords):
        self.parent.myStatus = 'Individual'
        self.parent.display_selected_data("Individual")

    def show_MetaForm(self, *args, **keywords):
        self.parent.parentApp.switchForm('MetaForm')

    def show_NewContact(self, *args, **keywords):
        self.parent.parentApp.switchForm('NewContact')

    def show_NewIndividual(self, *args, **keywords):
        self.parent.parentApp.switchForm('NewIndividual')

    def formated_data_type(self, vl):
        return "%s (%s)" % (vl[1], str(vl[0]))

    def formated_contact(self, vl):
        return "%s %s, %s" % (vl[1], vl[2], str(vl[0]))

    def formated_word(self, vl):
        return "%s" % (vl[0])


class ActionControllerSearch(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^/.*', self.set_search, True)
        self.add_action('^:\d.*', self.speak, True)

    def set_search(self, command_line, widget_proxy, live):
        self.parent.value.set_filter(command_line[1:])
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()

    def speak(self, command_line, widget_proxy, live): # just for testing
        self.parent.value.set_filter("travel")
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()


    # NEEDED???
    def setMainMenu(self, command_line, widget_proxy, live):
        self.parent.setMainMenu()


class MeterMain(npyscreen.FormMuttActiveTraditionalWithMenus):
    ACTION_CONTROLLER = ActionControllerSearch
    MAIN_WIDGET_CLASS = ActionControllerData
    first_time = True
    myStatus = "Main"

    global cursor
    cursor = connectDatabase(dbHost)

    def getMenuText(self):                                      #menu_text
        global householdID
        householdID = str(householdID)
        contactID   = getContact(householdID)
        MenuText = []
        # CommandNumber=0
        MenuText.append("\n")
        for line in open("meterLogo.txt", "r"):
            # if (line[0] == "#"):
            #    MenuText.append("\t" + str(CommandNumber) + ".\t" + line[1:])
            #    CommandNumber+=1
            # else:
            MenuText.append("\t" + line)

        MenuText.append("\n")

        MenuText.append("\t\t\t _____________________________________________")  
        MenuText.append(formatBox("[M]odus:", operationModus + ' (' + getHouseholdCount() +')'))
        MenuText.append("\t\t\t _____________________________________________")  
        MenuText.append("\n")


        if (householdID != "0"):
            MenuText.append("\t\t\t _____________________________________________")  
            MenuText.append(formatBox("Contact:",  getNameOfContact(contactID) + ' (' + contactID + ')'))
            MenuText.append("\t\t\t _____________________________________________")  
            MenuText.append(formatBox("Date:", getDateChoice(householdID)))
            MenuText.append(formatBox("Household:", householdID))
            MenuText.append(formatBox("People:", getParticipantCounters(householdID)))

            if (operationModus in {'Issued', 'Processed'}):
                MenuText.append(formatBox("Diaries:",  getDeviceMetaIDs(householdID,'A')))
                metaIDs = "%s" % getDeviceMetaIDs(householdID,'E')
                MenuText.append(formatBox("E-Meter:", metaIDs))
                if (operationModus == 'Processed'):
                    MenuText.append(formatBox("Low:",  getReadingPeriods(householdID,Criteria['no reading'],60))) # last parameter is min duration to report
                    MenuText.append(formatBox("High:", getReadingPeriods(householdID,Criteria['high reading'],60))) # last parameter is min duration to report
                    MenuText.append(formatBox("[A]nalyse", '' ))

            if (operationModus == 'Upcoming'):
                MenuText.append(formatBox("[D]iaries:",  getDeviceMetaIDs(householdID,'A')))
                MenuText.append(formatBox("[E]-Meter:",   getDeviceMetaIDs(householdID,'E')))
                MenuText.append(formatBox("[>] Next", '' ))
            MenuText.append("\t\t\t _____________________________________________")  


        MenuText.append("\n")
        MenuText.append("Database: " + dbHost)
        MenuText.append("\n")
        if (operationModus == 'Issued'):
            MenuText.append("\t\t\t[P]rocess returned kit \t\t[E]mail reminder")
        elif (operationModus == 'Processed'):
            MenuText.append("\t\t\t[P]lot data\t\t\t[E]mail graph")

        MenuText.append("\t\t\t[S]how Households \t\t [>] Next Household")
        MenuText.append("\t\t\t[^X] Menu   [H]ome Screen    [/] Search     [X] Quit")

        return MenuText

    def setMainMenu(self):
        mainScreenText = self.getMenuText()
        self.myStatus = 'Main'
        self.value.set_values(mainScreenText)
        self.wMain.values = mainScreenText
        self.wMain.display()

    def beforeEditing(self):
        mainScreenText = self.getMenuText()
        self.value.set_values(mainScreenText)
        self.update_list()
        if self.first_time:
            self.initialise()
            self.first_time = False

    def initialise(self):
        # menu and sub-menues           #menu_bar
        global dataType
        self.m1 = self.add_menu(name="Data handling", shortcut="D")
        self.m1.addItemsFromList([
            ("Download from phone", data_download, "d"),
            ("Review Meta Data", data_review, "r"),
            ("Upload to database",  data_upload, "u"),
            ("Download and upload", data_download_upload, "D"),
        ])
        self.m2 = self.add_menu(name="Setup a batch", shortcut="B")
        self.m2.addItem(text='Show Households', onSelect=MeterApp._Forms['MAIN'].display_selected_data, shortcut='S', arguments=['Households'])
        # self.m2.addItem(text='Pre Parcel email', onSelect=pre_parcel_email, shortcut='M', arguments=[householdID])
        self.m2.addItem(text='eMeter ID', onSelect=phone_id_setup, shortcut='e', arguments='E')
        self.m2.addItem(text='aMeter ID', onSelect=phone_id_setup, shortcut='a', arguments='A')
        # self.m2.addItem(text='eMeter apk', onSelect=eMeter_setup, shortcut='E', arguments=None)
        self.m2.addItem(text='Flash eMeter', onSelect=flash_phone, shortcut='E', arguments='E')
        self.m2.addItem(text='Flash aMeter', onSelect=flash_phone, shortcut='A', arguments='A')
        self.m2.addItem(text='aMeter config', onSelect=aMeter_setup, shortcut='C', arguments=None)
        self.m2.addItem(text='Root phone', onSelect=root_phone, shortcut='R', arguments=None)

        self.m2 = self.add_menu(name="Work with data", shortcut="i")
        self.m2.addItem(text='Plot', onSelect=plot_data, shortcut='p', arguments=[householdID])

        self.m2 = self.add_menu(name="Emails", shortcut="e")
        self.m2.addItem(text='Email many', onSelect=email_many, shortcut='m', arguments=None)
        self.m2.addItem(text='Email blank', onSelect=compose_email, shortcut='b', arguments=['blank'])
        self.m2.addItem(text='Email confirm date', onSelect=compose_email, shortcut='c', arguments=['confirm'])
        self.m2.addItem(text='Email pack sent', onSelect=compose_email, shortcut='p', arguments=['parcel'])
        self.m2.addItem(text='Email graph', onSelect=compose_email, shortcut='g', arguments=['graph'])
        self.m2.addItem(text='Email on failure', onSelect=compose_email, shortcut='f', arguments=['fail'])

        self.m2.addItem(text='------No editing------', onSelect=self.IgnoreForNow, shortcut='', arguments=None)
        self.m2.addItem(text='Email blank', onSelect=compose_email, shortcut='B', arguments=['blank',False])
        self.m2.addItem(text='Email confirm date', onSelect=compose_email, shortcut='C', arguments=['confirm',False])
        self.m2.addItem(text='Email pack sent', onSelect=compose_email, shortcut='P', arguments=['parcel',False])
        self.m2.addItem(text='Email graph', onSelect=compose_email, shortcut='G', arguments=['graph',False])
        self.m2.addItem(text='Email on failure', onSelect=compose_email, shortcut='F', arguments=['fail',False])

        self.m2 = self.add_menu(name="Database management", shortcut="m")
        self.m2.addItem(text='Show tables', onSelect=self.show_Tables, shortcut='t')
        self.m2.addItem(text='Select contact', onSelect=self.list_contacts, shortcut='c')
        self.m2.addItem(text='New    contact', onSelect=self.add_contact, shortcut='n')
        self.m2.addItem(text='Select meta', onSelect=self.list_meta, shortcut='m')
        self.m2.addItem(text='Change database', onSelect=toggleDatabase, shortcut='d', arguments=[dbHost])
        self.m2.addItem(text='Backup database', onSelect=backup_database, shortcut='b')

        self.m3 = self.add_menu(name="Exit", shortcut="X")
        self.m3.addItem(text="Home", onSelect = MeterApp._Forms['MAIN'].setMainMenu,shortcut="h")
        self.m3.addItem(text="Exit", onSelect = self.exit_application, shortcut="X")

    def show_Tables(self, *args, **keywords):
        self.myStatus = 'Tables'
        self.display_tables()

    def list_household(self):
        MeterApp._Forms['MAIN'].display_selected_data("Household")

    def list_meta(self):
        MeterApp._Forms['MAIN'].display_selected_data("Meta")

    def list_contacts(self):
        MeterApp._Forms['MAIN'].display_selected_data("Contact")

    def IgnoreForNow(self):
        pass

    def diary_input(self):
        self.parentApp.switchForm('TimeUse')
        # MeterApp._Forms['MAIN'].display_selected_data("OpenDiaries")
        # MAIN_WIDGET_CLASS.show_TimeUse

    def toggleDishwasher(self):
        Dishwasher[timeIndex] = 1
        npyscreen.notify_confirm('Dishwasher toggle is go for period ' + str(timeIndex))

    def identifyHousehold(self):
        sqlq = "SELECT COUNT(*) FROM Household WHERE Contact_idContact = '" + contactID + "'"
        cursor.execute(sqlq)
        result = cursor.fetchone()
        # returns a tuple with format 'nL,' - extract value 'n':
        count = int(result[0])
        if (count == 0):
            # need to create household
            pass
        elif (count == 1):
            # set to the only option
            sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID + "'"
            cursor.execute(sqlq)
            result = cursor.fetchone()
            global householdID 
            householdID = str(int(result[0]))
            self.wStatus2.value =\
                "Household changed directly to " + householdID
            self.wStatus2.display()
            self.setMainMenu()
        else:
            MeterApp._Forms['MAIN'].display_selected_data("Household")

    def add_contact(self):
        if self.editing:
            self.parentApp.switchForm('NewContact')

    def afterEditing(self):
        if self.editing:
            self.parentApp.switchForm('NewContact')

    def change_data_type(self):
        if self.editing:
            self.parentApp.switchForm('DataType')

    def update_list(self):
        self.wStatus1.value = "METER " + self.myStatus
        self.wMain.values = self.value.get()

    def display_selected_data(self, displayModus):
        # pull SQL data and display                     #display_data
        self.myStatus = displayModus
        self.wStatus1.value = "METER " + self.myStatus + " selection"
        if (displayModus == "Contact"):
            sqlq = "SELECT * FROM Contact"
            cursor.execute(sqlq)
            result = cursor.fetchall()
        elif (displayModus == "TimeUseCode"):
            with open(tucFilePath) as inputFile:
                tucTuple = [tuple(line.split(',')) for line in inputFile.readlines()]
            sqlq = "SELECT * FROM " + self.myStatus
            cursor.execute(sqlq)
            result = tucTuple[-5:] + ['----------'] + list(cursor.fetchall())
            # XXX

        elif (displayModus == "TimeUseCodeOther"):
            result = [{'P\thh:mm\td\tw\tt\to\thome'}]
            for p in range(1,145):
                result = result + [{str(p) + '\t' + period_hhmm(p)}]

        elif (displayModus == "Diaries"):
            sqlq = "SELECT idMeta FROM Meta WHERE DataType = 'T' and SerialNumber is NULL"
            cursor.execute(sqlq)
            result = cursor.fetchall()

        elif (displayModus == "Households"):
            result = [{"{:<8}".format('HH ID') +\
                       "{:<7}".format('CT ID') +\
                       "{:<11}".format('Joined') +\
                       "{:<20}".format('Name') +\
                       "{:<7}".format('Status') +\
                       "{:<11}".format('Date') +\
                       "{:<7}".format('#') +\
                       "{:<25}".format('Comment') }]

            global operationModus
            fields ='idHousehold, timestamp, Contact_idContact, date_choice, CONVERT(comment USING utf8), status' 
            sqlq = "SELECT " + fields + " FROM Household WHERE " + Criteria[operationModus] +";"
            cursor.execute(sqlq)
            hh_result = cursor.fetchall()
            for hh in hh_result:
                thisHHid      = str(hh[0])
                thisTimeStamp = getDateTimeFormated(str(hh[1]))
                thisContact   = str(hh[2])
                thisDate      = str(hh[3])
                thisComment   = str(hh[4])
                thisStatus    = str(hh[5])
                result = result + [{\
                        "{:<7}".format(thisHHid) + '\t'\
                        "{:<7}".format(thisContact) + '\t'\
                        "{:<11}".format(thisTimeStamp +'\t') +\
                        "{:<20}".format(getNameOfContact(thisContact)) +\
                        "{:<7}".format(thisStatus) +\
                        "{:<11}".format(thisDate) +\
                        "{:<3}".format(str(getParticipantCount(thisHHid))) +\
                        "{:<25}".format(thisComment) }]


        elif (displayModus == "Household"):
            sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID + "'"
            cursor.execute(sqlq)
            result = cursor.fetchall()

        elif (displayModus == "Individual"):
            # list all individuals associated with the current contact
            # via the household ID for that contact. I.e. find all individuals where the household ID matched the household ID of the contact person
            # sqlq = "SELECT idIndividual FROM \
            sqlq = "SELECT * FROM \
	            (SELECT idHousehold FROM Household \
                    WHERE Contact_idContact = " + contactID + " ) a\
                    LEFT JOIN \
                    (SELECT * FROM Individual) b\
                    ON a.idHousehold = b.Household_idHousehold;"
            cursor.execute(sqlq)
            result = cursor.fetchall()
        else:
            sqlq = "SELECT * FROM " + self.myStatus
            cursor.execute(sqlq)
            result = cursor.fetchall()

        # result is populated, now display result
        displayList = []
        if (displayModus == "Contact"):
            for items in result:
                displayList.append(self.formated_contact(items))
        elif (displayModus == "DataType"):
            for items in result:
                displayList.append(self.formated_two(items))
        else:
            for items in result:
                displayList.append(self.formated_any(items))
        # update display
        self.value.set_values(displayList)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        self.wStatus1.display()
        # self.wStatus2.display()

    def formated_contact(self, vl):
        return "%s, %s %s" % (vl[0], vl[1], vl[2])

    def formated_any(self, tupelItems):
        returnString = ""
        for item in tupelItems:
            returnString += "%s \t\t" % (item)
        return returnString

    def formated_two(self, vl):
        return "%s, %s" % (vl[0], vl[1])

    def display_tables(self):
        self.myStatus = 'Tables'
        self.wStatus1.value = "METER " + self.myStatus
        # sqlq = "SELECT * FROM Contact"
        sqlq = "SHOW TABLES"
        cursor.execute(sqlq)
        result = cursor.fetchall()
        displayList = []
        for items in result:
            displayList.append(self.formated_any(items))

        # self.wMain.values = displayList
        self.value.set_values(displayList)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        # self.wMain.values = self.formated_word(result)
        # return result

    def show_TimeUseEntryScreen(self, *args, **keywords):
         global metaID
         self.myStatus = 'TimeUseCode'
         self.display_selected_data("TimeUseCode")
         self.wStatus2.value =\
             "Diary ID " + str(metaID) + " time " + str(timePeriod.time())
         self.wStatus2.display()


    def exit_application(self, command_line=None, widget_proxy=None, live=None):
        global cursor
        cursor.close()
        self.parentApp.setNextForm(None)
        self.editing = False
        self.parentApp.switchFormNow()


#---------------------------------------- 
#                   Diary Entry  
#---------------------------------------- 


class ActionControllerTimeUse(npyscreen.MultiLineAction):
    # action key shortcuts
    def __init__(self, *args, **keywords):
        super(ActionControllerTimeUse, self).__init__(*args, **keywords)
        global MenuActionKeys
        MenuActionKeys = {
            # 'd': self.toggleDevice(self.parent.Dishwasher),
            'd': self.toggleDishwasher,
            'w': self.toggleWashingMachine,
            'c': self.toggleOvenMicrowave,
            't': self.toggleTumbleDryer,
            'l': self.toggleLocation,
            'o': self.toggleOthers,
        }
        self.add_handlers(MenuActionKeys)


    def actionHighlighted(self, selectedLine, keypress):
        # choose action based on the display status and selected line
        timeUseArray = selectedLine.split('\t')         # the time use code is left of the two tabs and acts as ID
        global idTimeUseCode
        idTimeUseCode = str(timeUseArray[0])
        global timeUseActivity
        timeUseActivity = str(timeUseArray[2])


        self.parent.Activity1[self.parent.timeIndex] = idTimeUseCode
        # copy from above - unless toggled
#         if (self.parent.Dishwasher[self.parent.timeIndex] == -1):
#             self.parent.Dishwasher[self.parent.timeIndex] = 0       # has been switched off 
#         elif (self.parent.Dishwasher[self.parent.timeIndex] == 2):
#             self.parent.Dishwasher[self.parent.timeIndex] = 1       # has been switched on
#         else:
#             if (self.parent.timeIndex > 1):
#                 # remains unchanged
#                 self.parent.Dishwasher[self.parent.timeIndex] = self.parent.Dishwasher[self.parent.timeIndex-1]

        # copy from above - unless toggled
        t = self.parent.timeIndex
        if (t == 1):
            t0 = t    # if we are on the first item copy from self
        else:
            t0 = t-1

        self.parent.Dishwasher[t]     = self.carryOver(self.parent.Dishwasher[t],     self.parent.Dishwasher[t0])
        self.parent.WashingMachine[t] = self.carryOver(self.parent.WashingMachine[t], self.parent.WashingMachine[t0])
        self.parent.TumbleDryer[t]    = self.carryOver(self.parent.TumbleDryer[t],    self.parent.TumbleDryer[t0])
        self.parent.OvenMicrowave[t]  = self.carryOver(self.parent.OvenMicrowave[t],  self.parent.OvenMicrowave[t0])
        # self.parent.Dishwasher[t]     = self.carryOver(self.parent.Dishwasher[t],     self.parent.Dishwasher[t0])
        # self.carryOver(self.parent.Dishwasher[t],     self.parent.Dishwasher[t0])

        self.parent.Activity1[self.parent.timeIndex] = idTimeUseCode
        # add_time_use_to_file(individual, idTimeUseCode, str(timePeriod.time()), timeUseActivity)

        self.parent.timePeriod = next_period(self.parent.timePeriod)
        self.parent.timeIndex += 1

        # XXX adopt previos location and Others


        self.parent.wStatus2.value =\
            str(self.parent.timePeriod.time()) + ' ' + timeUseActivity +  ' set'
        self.parent.wStatus2.display()
        self.parent.updateScreen()

    def carryOver(self, a, a0):
        # -1 toggled off #  0 off #  1 on #  2 toggled on
        if (a == -1):
            a = 0       # has been switched off 
        elif (a == 2):
            a = 1       # has been switched on
        else:
            a = a0      # remains unchanged
        return a

    def toggleDevice(self, device):
        a = device[self.parent.timeIndex]
        if (self.parent.timeIndex > 1):
            a0 = device[self.parent.timeIndex-1]
            # npyscreen.notify_confirm('check ' + str(a) + ' and ' + str(a0))
            if (a0 < 1):     # off / switched off
                a = 2       # switched on 
            else:
                a = -1      # switched off
        else:
            a = 2       # switched on (on the assumption that device was initialised as 'off'
        return a

        

    def toggleDishwasher(self, void):
        self.parent.Dishwasher[self.parent.timeIndex] = self.toggleDevice(self.parent.Dishwasher)
        self.parent.updateScreen()
        # if (self.parent.timeIndex > 1):
        #     if (self.parent.Dishwasher[self.parent.timeIndex-1] < 1):     # off / switched off
        #         self.parent.Dishwasher[self.parent.timeIndex] = 2       # switched on 
        #     else:
        #         self.parent.Dishwasher[self.parent.timeIndex] = -1      # switched off
        # else:
        #     self.parent.Dishwasher[self.parent.timeIndex] = 2       # switched on 
        # self.parent.updateScreen()

    def toggleWashingMachine(self, void):
        if (self.parent.timeIndex > 1):
            if (self.parent.WashingMachine[self.parent.timeIndex-1] < 1):     # off / switched off
                self.parent.WashingMachine[self.parent.timeIndex] = 2       # switched on 
            else:
                self.parent.WashingMachine[self.parent.timeIndex] = -1      # switched off
        else:
            self.parent.WashingMachine[self.parent.timeIndex] = 2       # switched on 
        self.parent.updateScreen()

    def toggleTumbleDryer(self, void):
        if (self.parent.timeIndex > 1):
            if (self.parent.TumbleDryer[self.parent.timeIndex-1] < 1):     # off / switched off
                self.parent.TumbleDryer[self.parent.timeIndex] = 2       # switched on 
            else:
                self.parent.TumbleDryer[self.parent.timeIndex] = -1      # switched off
        else:
            self.parent.TumbleDryer[self.parent.timeIndex] = 2       # switched on 
        self.parent.updateScreen()

    def toggleOvenMicrowave(self, void):
        if (self.parent.timeIndex > 1):
            if (self.parent.OvenMicrowave[self.parent.timeIndex-1] < 1):     # off / switched off
                self.parent.OvenMicrowave[self.parent.timeIndex] = 2       # switched on 
            else:
                self.parent.OvenMicrowave[self.parent.timeIndex] = -1      # switched off
        else:
            self.parent.OvenMicrowave[self.parent.timeIndex] = 2       # switched on 
        self.parent.updateScreen()

    def toggleLocation(self, void):
        if (self.parent.timeIndex > 1):
           self.parent.Location[self.parent.timeIndex] += 1       # next location
        if (self.parent.Location[self.parent.timeIndex] > 3):
            self.parent.Location[self.parent.timeIndex] == 0      # start over
        self.parent.updateScreen()

    def toggleOthers(self, void):
        if (self.parent.timeIndex > 1):
           self.parent.Others[self.parent.timeIndex] += 1       # next location
        if (self.parent.Others[self.parent.timeIndex] > 5):
            self.parent.Others[self.parent.timeIndex] == 0      # start over
        self.parent.updateScreen()

class TimeUseForm(npyscreen.FormMuttActiveTraditional):
     ACTION_CONTROLLER = ActionControllerSearch
     MAIN_WIDGET_CLASS = ActionControllerTimeUse

     # Time use arrays
     timePeriod = datetime.datetime(1,1,1,4,0,0) # 4am start
     timeIndex = 1  # counts in parallel to timePeriod from 1 (=4am) to 144 (=3:50am)
     Activity1       = [-1]*144        # keeps time codes for editing before uploading
     Activity2       = [-1]*144        # secondary activities
     Dishwasher      = [0]*144       # 0= not in use, 1= in use
     WashingMachine  = [0]*144
     TumbleDryer     = [0]*144
     OvenMicrowave   = [0]*144
     Location        = [0]*144       # 1= home, 2= travel, 3=away, 0= unspecified
     Others          = [0]*144       # how many people were with you?
 
     tucDisplay = []

     def beforeEditing(self):
        self.initialise()
 
     def initialise(self):
        sqlq = "SELECT * FROM TimeUseCode"
        cursor.execute(sqlq)
        result = [' - codes - '] + list(cursor.fetchall())
        for items in result:
            self.tucDisplay.append(self.formated_any(items))

        # update display
        self.value.set_values(self.tucDisplay)
        # self.value.set_values(displayList)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        self.wStatus1.display()

     def updateScreen(self):
        diaryDisplay = []
        if (self.timeIndex < 15):
            lowerBound = 1
            upperBound = 15
        else:
            lowerBound = self.timeIndex-14
            upperBound = self.timeIndex+1
        for i in range(lowerBound, upperBound):
            dw = '    '
            wm = '    '
            td = '    '
            om = '    '
            lc = '      '
            os = '   '
            if (self.Dishwasher[i] == -1):
                dw = ' vv '
            if (self.Dishwasher[i] == 0):
                dw = '    '
            if (self.Dishwasher[i] == 1):
                dw = ' dw '
            if (self.Dishwasher[i] == 2):
                dw = ' ^^ '

            if (self.WashingMachine[i] == -1):
                wm = ' vv '                     # end
            if (self.WashingMachine[i] == 0):   # off
                wm = '    '
            if (self.WashingMachine[i] == 1):   # on
                wm = ' wm '
            if (self.WashingMachine[i] == 2):   # start
                wm = ' ^^ '

            if (self.TumbleDryer[i] == -1):
                td = ' vv '
            if (self.TumbleDryer[i] == 0):
                td = '    '
            if (self.TumbleDryer[i] == 1):
                td = ' td '
            if (self.TumbleDryer[i] == 2):
                td = ' ^^ '

            if (self.OvenMicrowave[i] == -1):
                om = ' vv '
            if (self.OvenMicrowave[i] == 0):
                om = '    '
            if (self.OvenMicrowave[i] == 1):
                om = ' om '
            if (self.OvenMicrowave[i] == 2):
                om = ' ^^ '

            if (self.Location[i] == 1):
                lc = ' home '
            elif (self.Location[i] == 2):
                lc = ' trvl '
            elif (self.Location[i] == 3):
                lc = ' away '


            diaryDisplay.append(str(self.Activity1[i]) + ' ' +  str(self.Activity2[i]) + dw + wm + td + om + lc + str(self.Others[i]))
        for item in self.tucDisplay:
            diaryDisplay.append(item)

        # update display
        self.value.set_values(diaryDisplay)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        self.wStatus1.display()

     def formated_any(self, tupelItems):
        returnString = ""
        for item in tupelItems:
            returnString += "%s \t\t" % (item)
        return returnString
 

class newContactForm(npyscreen.Form):
    # gets fields from database, collects new entries
    def create(self):
        # get Household fields
        self.ColumnName = []
        self.ColumnEntry = []
        sqlq = "SHOW columns from Contact;"
        global cursor
        cursor.execute(sqlq)
        tabledata = cursor.fetchall()
        for field in tabledata:
            self.ColumnName.append(field[0])
        for item in range(0, len(self.ColumnName)):
            self.ColumnEntry.append(self.add(npyscreen.TitleText,
                                    name=self.ColumnName[item]))
        # self.ColumnName.pop(0)   # to leave out the ID column
        # cursor.close()

    def afterEditing(self):
        global cursor
        global contactID
        global householdID

        # combine all column names into comma separated string with ``
        sqlColumnString = "`"+self.ColumnName[0]+"`"
        for item in self.ColumnName[1:]:
            sqlColumnString = sqlColumnString + (",`"+item+"`")

        sqlEntryString = "'"+self.ColumnEntry[0].value+"'"
        for item in self.ColumnEntry[1:]:
            sqlEntryString = sqlEntryString + (",'"+item.value+"'")

        # create contact
        sqlq = "INSERT INTO `Contact`(" + sqlColumnString + ") \
            VALUES ("+sqlEntryString+")"
        cursor.execute(sqlq)
        dbConnection.commit()
        contactID = cursor.lastrowid
        
        # create household
        sqlq = "INSERT INTO `Household`(Contact_idContact, security_code) \
            VALUES ("+str(contactID)+", 123)"
        cursor.execute(sqlq)
        dbConnection.commit()
        householdID = cursor.lastrowid
        self.parentApp.setNextFormPrevious()


class newIndividualForm(npyscreen.Form):
    # gets fields from database, collects new entries
    def create(self):
        # get fields
        self.ColumnName = []
        self.ColumnEntry = []
        sqlq = "SHOW columns from Individual;"
        global cursor
        cursor.execute(sqlq)
        tabledata = cursor.fetchall()
        for field in tabledata:
            self.ColumnName.append(field[0])
        self.ColumnName.pop(0)   # to leave out the ID column
#         self.ColumnName.pop(0)   # to leave out the idHousehold column
        for item in range(0, len(self.ColumnName)):
            self.ColumnEntry.append(self.add(npyscreen.TitleText,
                                    name=self.ColumnName[item]))

    def afterEditing(self):
        # combine all column names into comma separated string with ``
        sqlColumnString = "`"+self.ColumnName[0]+"`"
        for item in self.ColumnName[1:]:
            sqlColumnString = sqlColumnString + (",`"+item+"`")

        sqlEntryString = "'"+self.ColumnEntry[0].value+"'"
        for item in self.ColumnEntry[1:]:
            sqlEntryString = sqlEntryString + (",'"+item.value+"'")

        sqlq = "INSERT INTO `Individual`(" + sqlColumnString + ") \
            VALUES ("+sqlEntryString+")"
        global cursor
        cursor.execute(sqlq)
        dbConnection.commit()
        global individual
        individual = str(cursor.lastrowid)
        self.parentApp.setNextFormPrevious()


class metaFileInformation(npyscreen.Form):
    # The MetaForm
    # display all .meta files in /METER/
    fileList = []
    reject_fileList = []

    selectIndex = []
    selectCounter = 0
    metaIDs = []
    collectionDate = []
    dataType = []
    duration = []
    displayString = []

    reject_Index = []
    reject_Counter = 0
    reject_contactID = []
    reject_collectionDate = []
    reject_dataType = []
    reject_duration = []
    reject_displayString = []

    def create(self):
        self.FileSelection = self.add(npyscreen.TitleMultiSelect, max_height=9,
                                      value=self.selectIndex,
                                      name="Which files should be uploaded?",
                                      values=self.displayString,
                                      scroll_exit=True)
        self.FileRejection = self.add(npyscreen.TitleMultiSelect, max_height=15,
                                      value=self.reject_Index,
                                      name="These files will be deleted (uncheck to save them)?",
                                      values=self.reject_displayString, scroll_exit=True)
    def beforeEditing(self):
        self.selectCounter = 0
        self.selectIndex = []
        self.displayString =[]
        self.reject_Index = []
        self.reject_displayString = []
        # set up file names
        global filePath

        allCSVfiles = filePath + '*.csv'
        CSVfileList = glob.glob(allCSVfiles)

        for DataFile in CSVfileList:
            recordsInFile = sum(1 for line in open(DataFile))
            thisFileName = DataFile.split('.csv')[0]
            if (recordsInFile > 80000):
                global householdID
                # only full 24 hour recordings are of interest
                # (that would be 86400 seconds)

                # the split() takes the Watt column after first ',' before '\n'
                meanPower =  sum(float(line.split(',')[1].split('\n')[0]) for line in open(DataFile)) / recordsInFile

                thisMeta = getMetaData(thisFileName + '.meta', "Meta ID")
                householdID = getHouseholdForMeta(thisMeta) 
                thisDateChoice = getDateChoice(householdID)
                self.selectIndex.append(self.selectCounter)
                self.fileList.append(thisFileName)
                self.metaIDs.append(thisMeta)

                self.collectionDate.append(getMetaData(thisFileName + '.meta', "Date"))
                self.dataType.append(getMetaData(thisFileName+'.meta', "Data type"))
                thisDuration = ("%.1f" % (recordsInFile / 3600.0))

                self.displayString.append(str(self.selectCounter) + '. ID: ' +
                                     thisMeta + ' ' + self.dataType[-1] +
                                     ' on ' + self.collectionDate[-1] + ' (' +thisDateChoice+ ') for ' +
                                     thisDuration + ' h ('+ ("%.1f" % meanPower) +'W)')
                self.selectCounter += 1

            elif ('act' in DataFile):
                self.selectIndex.append(self.selectCounter)
                self.fileList.append(thisFileName)
                self.metaIDs.append(os.path.basename(DataFile).split('_')[0])        # filename is metaID+'_act.csv'
                self.collectionDate.append(getDateOfFirstEntry(DataFile,1))           # take date from first entry in column 1 (2nd col)
                self.dataType.append("A")
                self.duration.append(recordsInFile)
                self.displayString.append(str(self.selectCounter) + '. ID: ' +
                                     self.metaIDs[-1] + ' ' + self.dataType[-1] +
                                     ' with ' +
                                     str(self.duration[-1]) + ' records')
                self.selectCounter += 1

            elif ('ind' in DataFile):
                self.selectIndex.append(self.selectCounter)
                self.fileList.append(thisFileName)
                self.metaIDs.append(os.path.basename(DataFile).split('_')[0])        # filename is metaID+'_ind.csv'

                self.collectionDate.append(getDateOfFirstEntry(DataFile,0))           # take date from first entry in column 0 (1nd col)
                self.dataType.append("I")
                self.duration.append(recordsInFile)
                self.displayString.append(str(self.selectCounter) + '. ID: ' +
                                     self.metaIDs[-1] + ' ' + self.dataType[-1] +
                                     ' with ' + str(self.duration[-1]) + ' records')
                self.selectCounter += 1

            else:
                self.reject_Index.append(self.reject_Counter)
                self.reject_fileList.append(thisFileName)
                self.reject_contactID.append(getMetaData(thisFileName +
                                        '.meta', "Contact ID"))
                self.reject_collectionDate.append(getMetaData(thisFileName +
                                             '.meta', "Date"))
                self.reject_dataType.append(getMetaData(thisFileName +
                                       '.meta', "Data type"))
                self.reject_duration.append(round(recordsInFile / 3600.0, 2))
                self.reject_displayString.append(str(self.reject_Counter) + '.\t ID: ' +
                                            self.reject_contactID[-1] + ' ' +
                                            self.reject_dataType[-1] + ' on ' +
                                            self.reject_collectionDate[-1] +
                                            ' for ' + str(self.reject_duration[-1]) +
                                            ' hours')
                self.reject_Counter += 1
        self.FileSelection.values = self.displayString
        self.FileRejection.values = self.reject_displayString


    def afterEditing(self):
        for i in self.FileSelection.value:
            uploadDataFile(self.fileList[i],self.dataType[i],self.metaIDs[i],self.collectionDate[i])   # insert to database

        for FileIndex in self.FileRejection.value:                                      # delete all other files
            call('mv ' + self.reject_fileList[FileIndex] +
                 '.meta ~/.Trash/', shell=True)
            call('mv ' + self.reject_fileList[FileIndex] +
                 '.csv ~/.Trash/', shell=True)

        # tidy up any left over files
        call('mv ' + filePath + '*.csv ' + archivePath, shell=True)
        call('mv ' + filePath + '*.meta ' + archivePath, shell=True)

        # switch to "Processed" and display the most recent addition
        global operationModus
        operationModus = modi[0]
        self.parentApp.setNextFormPrevious()


class selectionForm(npyscreen.Form):
# show all Serial Numbers that emerged from the search in Meta for a given household
    # in time this could be a more generic form....
    def create(self):
        selectIndex = []
        displayString = ['nothing']
        reject_Index = []
        reject_displayString = []
        self.SelectionOptions = self.add(npyscreen.TitleSelectOne, max_height=9,
                                      value=selectIndex,
                                      name="Which Number should be used?",
                                      values=displayString,
                                      scroll_exit=True)

    def beforeEditing(self):
        global SerialNumbers
        self.SelectionOptions.values = SerialNumbers

    def getResult():
        return self.SelectionOptions.value

    def afterEditing(self):
        global MetaID
        MetaID = self.SelectionOptions.value
        self.parentApp.setNextFormPrevious()


class MeterForms(npyscreen.NPSAppManaged):
    def onStart(self):
        # npyscreen.setTheme(npyscreen.Themes.ColorfulTheme)
        self.addForm('MAIN', MeterMain, lines=36)
        # self.addForm('MAIN', TimeUseForm, name='Time Use Entry', lines=36)
        self.addForm('NewContact', newContactForm, name='New Contact')
        self.addForm('NewIndividual', newIndividualForm, name='New Individual')
        self.addForm('MetaForm', metaFileInformation, name='Meta Data')
        self.addForm('SelectionForm', selectionForm, name='Selection Form')
        self.addForm('TimeUse', TimeUseForm, name='Time Use Entry')

if __name__ == "__main__":
    MeterApp = MeterForms()
    MeterApp.run()
    exit()
