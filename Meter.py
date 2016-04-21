#!/usr/bin/python

## 
# ADD -- SELECT individual
# show upcomming deployments
# upload_10min_readings is not called - use Numpi smoothing for 10 min readings

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

timePeriod = datetime.datetime(1,1,1,4,0,0) # 4am start
contactID = '0'
metaID = '1026'
individual = '0'
householdID = '0'
dataType = 'E'
participantCount = '0'
aMeterCount = '0'
eMeterCount = '0'

dateTimeToday = datetime.datetime.now()
str_date = dateTimeToday.strftime("%Y-%m-%d")

SerialNumbers   = []

dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName)
cursor = dbConnection.cursor()

def getMetaData(MetaFile, ItemName):
    # extract content from meta file (or any other file)
    content = ""
    for line in open(MetaFile):
        if ItemName in line:
            content = line.split(ItemName + ": ", 1)[1]
    return content.strip()

def backup_database():
    call('mysqldump -u ' + dbUser + ' -h ' + dbHost + ' -p --databases ' + dbName +
         ' > ' + filePath + 'database/' + str_date + '_' + dbName + '.sql', shell=True)
    npyscreen.notify_confirm('Database backed up as ' + str_date + dbName + '.sql')

def plot_data():
    # get readings for a given metaID
    global metaID

    # READ ACTIVITIES.JSON
    activity_file = urllib.urlopen('https://raw.githubusercontent.com/PhilGrunewald/MeterApp/master/www/js/activities.json').read()
    activities =json.loads(activity_file)

    # GET ELECTRICTY READINGS
    sqlq = "SELECT * FROM Electricity where Meta_idMeta = "+str(metaID)+" and idElectricity % 10 =0;"
    cursor.execute(sqlq)
    result = list(cursor.fetchall())
    watt=[]
    date_time=[]

    for item in result:
        watt.append(item[1])
        date_time.append(item[3])

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

    sqlq = "SELECT tuc_time,activity,location FROM TimeUse WHERE Meta_idMeta = "+str(999)+";"
    cursor.execute(sqlq)
    result = list(cursor.fetchall())

    for item in result:
        tuc_time.append(item[0])
        tuc_key.append(item[1])
        tuc_location.append(item[2])
        thisCat = activities['activities'][item[1]]['category']
        tuc_category.append(thisCat)
        if (str(item[2]) == "home"):
            tuc_colour.append(tuc_colours[thisCat])
            tuc_size.append(4000)
        else:
            tuc_colour.append(tuc_colours_dim[thisCat])
            tuc_size.append(6000)

    #p = figure(width=800, height=350,  x_axis_type="datetime")
    p = figure(width=800, height=350, tools="tap", x_axis_type="datetime")
    p.xaxis.axis_label = str(item[2]) + 'Time'
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

    # time_bar = p.square(x=tuc_time, 
    #                     y=tuc_size, 
    #                     size = 5, 
    #                     color= tuc_colour,
    #                     nonselection_color="purple"
    #                     )

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

    output_file(plotPath + metaID + '.html', title= metaID + ' data')
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    
    script, div = components(p, INLINE)
    show(p)
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
    # return encode_utf8(html)

def email_graph():
    # send email with link to graph

    sqlq = "SELECT Name,Email FROM Contact WHERE idContact = '" +\
        contactID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    thisName = ("%s" % (result[0]))
    thisEmail = ("%s" % (result[1]))

    sqlq = "SELECT CollectionDate FROM Meter.Meta WHERE idMeta = '" + metaID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    strCollectionDate = ("%s" % (result[0]))
    dateArray = strCollectionDate.split('-')
    CollectionDate = datetime.date(int(dateArray[0]), int(dateArray[1]), int(dateArray[2]))
    thisDate = CollectionDate.strftime("%A, %e %B")

    templateFile = open(emailPath + "emailTemplate.md", "r")
    templateText = templateFile.read()
    templateFile.close()

    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[metaID]", metaID)

    emailFilePath = emailPath + "tempEmail.mail"
    emailFile = open(emailFilePath, "w+")
    emailFile.write(templateText)
    emailFile.close()
    call('mutt -s "[Meter] Your electricity profile" ' + thisEmail + ' < ' + emailFilePath, shell=True)

def data_download():
    # pull files from phone
    call('adb pull /sdcard/METER/ ' + filePath, shell=True)
    cmd = 'adb shell ls /sdcard/Meter/'
    s = subprocess.check_output(cmd.split())
    call('adb shell rm -rf /sdcard/Meter/*.csv', shell=True)
    call('adb shell rm -rf /sdcard/Meter/*.meta', shell=True)
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

def uploadFile(fileName):  
    # called from MetaForm - after editing - for each file
    global cursor
    global metaID
    global dataType
    global householdID
    global archivePath

    MetaFile = fileName + '.meta'
    DataFile = fileName + '.csv'

    # read Meta file information
    # ---------------------------
    if os.path.exists(MetaFile):
        deviceSN = getMetaData(MetaFile, "Device ID")
        metaID = getMetaData(MetaFile, "Meta ID")  # 17 Nov 15 phones are now set up with the prepared entry ID in the meta file
        dataType = getMetaData(MetaFile, "Data type")
        #    offset = getMetaData(MetaFile, "Offset")
        collectionDate = getMetaData(MetaFile, "Date")
    else:
        deviceSN = 'not found'
        metaID = '0'
        dataType = '?'
        collectionDate = '00-01-01'


    # ############## MetaID CHECK
    # -----------------------------
    # Was a meta entry made when this phone was set up?

    sqlq = "SELECT Household_idHousehold FROM Meta WHERE idMeta = '" + metaID + "'"
    cursor.execute(sqlq)
    thisHousehold = cursor.fetchone()

    if thisHousehold is None:
        # create a new meta entry
        sqlq = "INSERT INTO Meta(CollectionDate, DataType, SerialNumber,\
            Household_idHousehold) VALUES \
            ('" + collectionDate + "', '" + dataType + "', '" + deviceSN +\
             "', '" + householdID + "');"
        cursor.execute(sqlq)
        dbConnection.commit()
        # get the id of the entry just made
        metaID = cursor.lastrowid
        npyscreen.notify_confirm('This phone was not properly registered in the database. Household ' + householdID + ' recording is now listed as meta entry ' + str(metaID))
    else:
        # update meta entry
        # XXX what to do if more than one recording was taken? at the moment only one meta entry with the most recent date...
        sqlq = "UPDATE Meta SET \
                `DataType`='"+ dataType +"', \
                `SerialNumber`='"+ deviceSN +"', \
                `CollectionDate`='"+ collectionDate +"'\
                WHERE `idMeta`='" +metaID+"';"
        cursor.execute(sqlq)
        npyscreen.notify_confirm('meta updated')
        
    # ###################### Enter data
    # insert electricity DataFile into database
    csv_data = csv.reader(file(DataFile))
    for row in csv_data:
        sqlq = "INSERT INTO Electricity(Time, Watt, Meta_idMeta ) \
        VALUES('" + row[0] + "', '" + row[1] + "', '" + str(metaID) + "')"
        cursor.execute(sqlq)

    # close the connection to the database.
    # -------------------------------------
    dbConnection.commit()
    # cursor.close()
    cmd_moveToArchive = 'mv ' + DataFile + ' ' + archivePath
    call(cmd_moveToArchive, shell=True)
    cmd_moveToArchive = 'mv ' + MetaFile + ' ' + archivePath
    call(cmd_moveToArchive, shell=True)


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

def getParticipantCount(householdID):
    # get number of diaries required
    sqlq ="SELECT age_group2, age_group3, age_group4, age_group5, age_group6\
            FROM Household \
            WHERE idHousehold = '" + householdID + "';"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    return int(result[0]) + int(result[1]) + int(result[2]) + int(result[3]) + int(result[4])

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

def markHouseholdAsIssued(householdID):
    # update status of household to '1 = kit issued / in the field'
    # to be done when on eMeter and all aMeters are issued
    sqlq = "UPDATE Household \
            SET `status`=1\
            WHERE `idHousehold` ='" + householdID + "';"
    cursor.execute(sqlq)
    dbConnection.commit()

def markHouseholdAsProcessed(householdID):
    # update status of household to '2 = kit processed into database'
    # to be done when on eMeter and all aMeters have been downloaded into db
    sqlq = "UPDATE Household \
            SET `status`=2\
            WHERE `idHousehold` ='" + householdID + "';"
    cursor.execute(sqlq)
    dbConnection.commit()

def phone_id_setup(meterType):
    # 2 Nov 15 - assumes that the apps are already installed
    global metaID
    global contactID
    # 1) get household ID (assuming a 1:1 relationship!)
    # npyscreen.notify_confirm('1: ' + meterType)
    sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '"\
        + str(contactID) + "'"
    cursor.execute(sqlq)
    householdID = ("%s" % cursor.fetchone())

    # npyscreen.notify_confirm('2: ' + str(householdID))
    # 2) create a meta id entry for an 'eMeter'
    sqlq = "INSERT INTO Meta(DataType, Household_idHousehold) \
           VALUES ('"+ meterType +"', '" + householdID + "')"
    cursor.execute(sqlq)
    dbConnection.commit()
    metaID = str(cursor.lastrowid)

    # npyscreen.notify_confirm('3: ' + str(metaID))
    
    idFile = open(idFilePath, 'w+')
    idFile.write(str(metaID))
    idFile.close()
    call('adb push ' + idFilePath + ' /sdcard/METER/', shell=True)
    MeterApp._Forms['MAIN'].wStatus2.value =\
        "Phone was assigned ID " + metaID
    MeterApp._Forms['MAIN'].wStatus2.display()
    MeterApp._Forms['MAIN'].setMainMenu()

def aMeter_setup():
    # compile and upload the cordova activity app
    call('/Users/phil/Sites/MeterApp/platforms/android/cordova/run', shell=True)
    # install AutoStart app
    call('adb install ~/Software/Android/AutoStart_2.1.apk',
         shell=True)
    # configure phone for recording
    phone_id_setup('A')

def eMeter_setup():
    # Compile
    call('ant debug -f ~/Software/Android/DMon/build.xml', shell=True)
    # remove old copy
    call('adb uninstall com.Phil.DEMon', shell=True)
    # install new
    call('adb install \
        ~/Software/Android/DMon/bin/MainActivity-debug.apk',
         shell=True)
    # install AutoStart app
    call('adb install ~/Software/Android/AutoStart_2.1.apk', shell=True)

    # create the METER folder
    call('adb shell mkdir /sdcard/METER', shell=True)
    # configure phone for recording
    phone_id_setup('E')



def print_address_label(void):
    # produces postage label and personal letter
    sqlq = "SELECT Name,Address1,Postcode,Address2 FROM Contact WHERE idContact = '"\
        + contactID + "'"
    cursor.execute(sqlq)
    result = cursor.fetchone()
    # addressDetails = ""
    # for item in result:
    #    addressDetails += "%s \n\n" % (item)
    addressDetails = \
        "**To:** \n\n \ \ \ **%s**\n\n \ \ \ **%s**\n\n \ \ \ **%s %s**" %\
        (result)
    addressBlock = "\ \n\n %s\n\n %s\n\n%s %s" % (result)

    returnAddress = "_Please return for free to_ \n\n\ \n\n\ \ \ \ Dr Philipp Grunewald \n\n\ \ \ \ University of Oxford \n\n\ \ \ \ OUCE, South Parks Road \n\n\ \ \ \ **OX1 3QY** Oxford\n\n\ "
    fromAddress = "\n\n\ \n\n\ _Dr Grunewald, University of Oxford, OX1 3QY Oxford_    \n\n"
    fromLetter = "\n\n\ \n\n\ _Dr Philipp Grunewald, Environmental Change Institute, University of Oxford_\n\n"
    letterPath = filePath + "letters/"
    myFile = open(letterPath + "address.md", "a")
    myFile.write(fromAddress)
    myFile.write(addressDetails)
    myFile.write("\n\n\ \n\n\ \n\n\ ")
    myFile.write("\n\n\ \n\n\ \n\n\ \n\n\ \n")
    myFile.write(returnAddress)
    myFile.write("\n\n\ \n\n\ \n\n")
    myFile.close()
    call('pandoc -V geometry:margin=0.5in ' + letterPath + "address.md -o" +
         letterPath + "address.pdf ", shell=True)

    # The letter
    thisName = ("%s" % (result[0]))
    letterFile = letterPath + contactID + "_letter."
    letterTemplate = letterPath + "letter.md"
    templateFile = open(letterTemplate, "r")
    templateText = templateFile.read()
    templateFile.close()
    templateText = templateText.replace("[date]", "**Wednesday**, 13 April 2016")
    if (dataType == 'PV'):
        templateText = templateText.replace("[s]", "s")
        templateText = templateText.replace("[is are]", "are")
        templateText = templateText.replace("[This These]", "These")
        templateText = templateText.replace("[it them]", "them")
        templateText = templateText.replace("[PV]", \
            " and a separate recorder for your PV system")
    else:
        templateText = templateText.replace("[s]", "")
        templateText = templateText.replace("[is are]", "is")
        templateText = templateText.replace("[This These]", "This")
        templateText = templateText.replace("[it them]", "it")
        templateText = templateText.replace("[PV]", "")

    myFile = open(filePath + "temp_letter.md", "w+")
    myFile.write("\pagenumbering{gobble}")
    myFile.write('![](/Users/phil/Documents/Oxford/Meter/Illustrations/Logos/meter_banner.pdf)')
    myFile.write(fromLetter)
    myFile.write(addressBlock)
    myFile.write("\n\n\ \n\n\ \n\n Dear " + thisName + ",\n\n")
    myFile.write("\n\n\ \n\n **Subject: Wednesday, 13 April: Your diary and electricity collection day **\n\n\ \n\n")
    myFile.write(templateText)
    # myFile.write('![](/Users/pg1008/Pictures/Signatures/Signature_PG.png =50x50)')
    #  myFile.write("\n\n\ \n\n\ \n\n")
    myFile.close()
    call('pandoc -V geometry:margin=1.2in ' + filePath + "temp_letter.md -o" +
         letterFile + "pdf ", shell=True)


# ------------------------------------------------------------------------------
# --------------------------FORMS-----------------------------------------------
# ------------------------------------------------------------------------------

class ActionControllerData(npyscreen.MultiLineAction):
    # action key shortcuts
    def __init__(self, *args, **keywords):
        super(ActionControllerData, self).__init__(*args, **keywords)
        global MenuActionKeys
        MenuActionKeys = {
            # '1': self.eMeter_setup,
            #   'p': self.eMeter_setup,
            'xA': print_address_label,
            'a': self.aMeter_id_setup,
            'e': self.eMeter_id_setup,
            'I': getNextHouseholdForParcel,
            'P': self.data_download,
            # "u": self.data_upload,
            # "D": data_download_upload,

            # "C": self.show_TimeUse,
            # "t": self.show_DataTypes,
            # "c": self.show_Contact,
            # "a": self.show_NewContact,
            # "i": self.show_NewIndividual,
            # "I": self.show_Individual,
            # 'T': self.show_Tables,

            # "m": self.show_MetaForm,

            # "s": self.show_MainMenu,

            "M": self.show_MainMenu,
            "X": self.parent.exit_application,
            # '5': self.add_nTimeUse ,
            # '0': self.upload_time_use_file,
        }
        self.add_handlers(MenuActionKeys)


    def actionHighlighted(self, selectedLine, keypress):
        global householdID 
        global contactID
        global str_date 
        global metaID
        global individual 
        global paticipantCount
        global eMeterCount
        global aMeterCount
        # choose action based on the display status and selected line
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
            metaID = str(dataArray[0])
            self.parent.wStatus2.value =\
                "Diary ID " + str(dataArray[0]) + " for Household " + str(dataArray[2]) + " selected"
            self.parent.wStatus2.display()
            # self.parent.setMainMenu()
            self.parent.show_TimeUseEntryScreen()


        elif (self.parent.myStatus == 'upcomingHousehold'):
            dataArray   = selectedLine.split('\t\t')
            householdID = str(dataArray[0])
            contactID   = str(dataArray[1])
            str_date    = str(dataArray[2])
            self.parent.wStatus2.value =\
                "Household changed to " + householdID +\
                "for Contact " + contactID +\
                "on " + str_date
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
            global dataType
            dataTypeArray = selectedLine.split('\t')
            dataType = str(dataTypeArray[0])
            self.parent.wStatus2.value =\
                "Data type changed to " + str(dataTypeArray[2])
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

    def eMeter_setup(self, *args, **keywords):
        eMeter_setup()

    def show_Tables(self, *args, **keywords):
        self.parent.myStatus = 'Tables'
        self.parent.display_tables()

    def show_MainMenu(self, *args, **keywords):
        self.parent.setMainMenu()

    def eMeter_id_setup(self, *args, **keywords):
        phone_id_setup('E')

    def aMeter_id_setup(self, *args, **keywords):
        phone_id_setup('A')
        
    def data_download(self, *args, **keywords):
        data_download()

    def data_upload(self, *args, **keywords):
        data_upload()

    def upload_time_use_file(self, *args, **keywords):
        identifyIndividual()
        self.parent.parentApp.switchForm('SelectionForm')
        # @@@@@@@@@@@@@@ test only
        global individual
        # individual = self.parent.parentApp.Form.SelectionForm.getResult()

        individual = MeterApp._Forms['SelectionForm'].SelectionOptions.value
        # identifyMetaID(
        # upload_time_use_file()

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

    def getMenuText(self):
        MenuText = []
        # CommandNumber=0
        MenuText.append("\n")
        for line in open("meterLogo.txt", "r"):
            # if (line[0] == "#"):
            #    MenuText.append("\t" + str(CommandNumber) + ".\t" + line[1:])
            #    CommandNumber+=1
            # else:
            MenuText.append("\t" + line)
        participantCount = ("%s" % getParticipantCount(str(householdID)))
        eMeterCount = ("%s" % getDeviceCount(str(householdID),'E'))
        aMeterCount = ("%s" % getDeviceCount(str(householdID),'A'))
        if (participantCount == aMeterCount):
            markHouseholdAsIssued(householdID)
        MenuText.append("\n")
        MenuText.append("\n")
        MenuText.append("Date:       " + str(str_date))
        MenuText.append("Contact:    " + str(contactID))
        MenuText.append("Household:  " + str(householdID))
        MenuText.append("<e>Meters:  " + str(eMeterCount))
        MenuText.append("<a>Meters:  " + str(aMeterCount) + "/" + str(participantCount))
        MenuText.append("\n")
        MenuText.append("Meta ID:    " + str(metaID) + "  Type: " + str(dataType))
        MenuText.append("\n")
        # upcomming Households
        sqlq = "SELECT count(idHousehold) FROM Meter.Household where date_choice > CURDATE() AND date_choice < CURDATE() + INTERVAL '14' DAY AND status < 1;"
        cursor.execute(sqlq)
        result = cursor.fetchone()
        strUpcomingHH = ("%s" % (result[0]))
        MenuText.append("Next 2 weeks: " + strUpcomingHH + "\t\t<I>ssue")
        sqlq = "SELECT count(idMeta) FROM Meta WHERE DataType = 'E' AND CollectionDate IS NULL;"
        cursor.execute(sqlq)
        result = cursor.fetchone()
        eMeterInField = ("%s" % (result[0]))
        sqlq = "SELECT count(idMeta) FROM Meta WHERE DataType = 'A' AND CollectionDate IS NULL;"
        cursor.execute(sqlq)
        result = cursor.fetchone()
        aMeterInField = ("%s" % (result[0]))
        MenuText.append("In the field: " + eMeterInField + "/" +aMeterInField+ " a/e\t\t<P>rocess")

        MenuText.append("\n")
        MenuText.append("\n")
        MenuText.append("Individual: " + str(individual))
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
        # menu and sub-menues
        global dataType
        self.m1 = self.add_menu(name="Data handling", shortcut="D")
        self.m1.addItemsFromList([
            ("Download from phone", data_download, "d"),
            ("Review Meta Data", data_review, "r"),
            ("Upload to database",  data_upload, "u"),
            ("Download and upload", data_download_upload, "D"),
        ])
        self.m2 = self.add_menu(name="Setup a batch", shortcut="B")
        self.m2.addItem(text='select Household', onSelect=MeterApp._Forms['MAIN'].display_selected_data, shortcut='h', arguments=['upcomingHousehold'])
        self.m2.addItem(text='eMeter ID', onSelect=phone_id_setup, shortcut='a', arguments='E')
        self.m2.addItem(text='aMeter ID', onSelect=phone_id_setup, shortcut='e', arguments='A')
        self.m2.addItem(text='eMeter config', onSelect=eMeter_setup, shortcut='E', arguments=None)
        self.m2.addItem(text='aMeter config', onSelect=aMeter_setup, shortcut='E', arguments=None)

        self.m2 = self.add_menu(name="Input returned data", shortcut="i")
        self.m2.addItemsFromList([
            ("Process eMeter phone", self.IgnoreForNow, "i"),
            ("Find household", self.identifyHousehold, "h"),
            # ("Add a diary", self.addDiary, "h"),
            ("Input a diary", self.diary_input, "d"),
        ])

        self.m2 = self.add_menu(name="Database management", shortcut="m")
        self.m2.addItem(text='Plot', onSelect=plot_data, shortcut='p', arguments=None)
        self.m2.addItem(text='Email', onSelect=email_graph, shortcut='e', arguments=None)
        self.m2.addItemsFromList([
            ("Add new contact", self.add_contact, "p"),
            # ("Display table",    self.display_data, "s"),
            # ("Display Contact",   self.display_table_data, "c"),
            # ("Display Contact",   self.XXdisplay_selected_data, "c"),
            ("List Contacts", self.list_contacts, "c"),
            ("Backup database",   backup_database, "c"),
        ])
        self.m3 = self.add_menu(name="Exit", shortcut="X")
        self.m3.addItem(text="Home", onSelect = MeterApp._Forms['MAIN'].setMainMenu,shortcut="h")
        self.m3.addItem(text="Exit", onSelect = self.exit_application, shortcut="X")

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
        # pull SQL data and display
        self.myStatus = displayModus
        self.wStatus1.value = "METER " + self.myStatus + " selection"
        # self.wStatus2.value = "Now Phil, Select " + self.myStatus + " from selection"
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

        elif (displayModus == "upcomingHousehold"):
            result = [{'HH\t\tContact\t\tDate'}]
            sqlq = "SELECT idHousehold, Contact_idContact, date_choice FROM Meter.Household where date_choice > CURDATE() AND date_choice < CURDATE() + INTERVAL '14' DAY AND status < 1;"
            cursor.execute(sqlq)
            result = cursor.fetchall()

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
#---------------------------------------- 
#---------------------------------------- 
#                   Diary Entry  
#---------------------------------------- 
#---------------------------------------- 
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


    def create(self):
        selectIndex = []
        displayString = ['nothing']
        reject_Index = []
        reject_displayString = []
        self.FileSelection = self.add(npyscreen.TitleMultiSelect, max_height=9,
                                      value=selectIndex,
                                      name="Which files should be uploaded?",
                                      values=displayString,
                                      scroll_exit=True)
        self.FileRejection = self.add(npyscreen.TitleMultiSelect, max_height=15,
                                      value=reject_Index,
                                      name="These files will be deleted (uncheck to save them)?",
                                      values=reject_displayString, scroll_exit=True)


    def beforeEditing(self):
        # set up file names
        global filePath
        # filePath = '/Users/pg1008/Documents/Data/METER/'

        # allMetafiles = filePath + '*.meta'
        allCSVfiles = filePath + '*.csv'
        # self.fileList = glob.glob(allMetafiles)
        CSVfileList = glob.glob(allCSVfiles)

        selectIndex = []
        selectCounter = 0
        contactID = []
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

        for DataFile in CSVfileList:
            recordsInFile = sum(1 for line in open(DataFile))
            thisFileName = DataFile.split('.csv')[0]
            if (recordsInFile > 80000):
                # only full 24 hour recordings are of interest
                # (that would be 86400 seconds)
                selectIndex.append(selectCounter)
                self.fileList.append(thisFileName)
                contactID.append(getMetaData(thisFileName +
                                 '.meta', "Meta ID"))
                collectionDate.append(getMetaData(thisFileName +
                                      '.meta', "Date"))
                dataType.append(getMetaData(thisFileName+'.meta', "Data type"))
                duration.append(round(recordsInFile / 3600.0, 2))
                displayString.append(str(selectCounter) + '. ID: ' +
                                     contactID[-1] + ' ' + dataType[-1] +
                                     ' on ' + collectionDate[-1] + ' for ' +
                                     str(duration[-1]) + ' hours')
                selectCounter += 1
            else:
                reject_Index.append(reject_Counter)
                self.reject_fileList.append(thisFileName)
                reject_contactID.append(getMetaData(thisFileName +
                                        '.meta', "Contact ID"))
                reject_collectionDate.append(getMetaData(thisFileName +
                                             '.meta', "Date"))
                reject_dataType.append(getMetaData(thisFileName +
                                       '.meta', "Data type"))
                reject_duration.append(round(recordsInFile / 3600.0, 2))
                reject_displayString.append(str(reject_Counter) + '.\t ID: ' +
                                            reject_contactID[-1] + ' ' +
                                            reject_dataType[-1] + ' on ' +
                                            reject_collectionDate[-1] +
                                            ' for ' + str(reject_duration[-1]) +
                                            ' hours')
                reject_Counter += 1
        self.FileSelection.values = displayString
        self.FileRejection.values = reject_displayString


    def afterEditing(self):
        for FileIndex in self.FileSelection.value:
            uploadFile(self.fileList[FileIndex])

        for FileIndex in self.FileRejection.value:
            call('mv ' + self.reject_fileList[FileIndex] +
                 '.meta ~/.Trash/', shell=True)
            call('mv ' + self.reject_fileList[FileIndex] +
                 '.csv ~/.Trash/', shell=True)
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
