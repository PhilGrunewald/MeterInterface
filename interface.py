#!/usr/bin/python

# Shortcuts:
#-----------
#action_keys        single key commands
#menu_text          main screen text
#menu_bar           the pop up menu
#display_data       display data depending on displayModus
#action_highlighted action based on line selected (enter) depending on displayModus
#statusUpdate       list of and setting of household status

# For plotting
import flask                  # serve python
import json                   # used for reading activities.json
import urllib                 # to read json from github
import numpy as np            # used for mean
import pandas as pd           # to reshape el readings

from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

from bokeh.plotting import figure, curdoc, vplot, show
from bokeh.plotting import figure, show, output_file
from bokeh.models import Range1d, Circle

from meter import *         # db connection and npyscreen features
from meter_ini import *     # reads the database and file path information from meter_ini.py

app = flask.Flask(__name__)
app.config['DEBUG'] = True


modi = [ 'Processed', 'Issued', 'Upcoming', 'Future' , 'No date yet']

Criteria = {
        'Processed':    'status > 5 ORDER BY date_choice DESC',
        'Issued':       'status = 5',
        'Upcoming':     'date_choice > CURDATE() AND date_choice < CURDATE() + INTERVAL "21" DAY ORDER BY date_choice ASC',
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

def plot_data(_householdID):
    # get readings for a given metaID
    # XXX this fetches only one - could be more than one...
    metaID = getMetaIDs(_householdID,'E')

    # READ ACTIVITIES.JSON
    ## THis worked fine for a while and suddenly I got "Error 503 backend read error" from github
    activity_file = urllib.urlopen('https://raw.githubusercontent.com/PhilGrunewald/MeterApp/master/www/js/activities.json').read()
    activities = json.loads(activity_file)
    # activity_file = "/Users/phil/Sites/MeterApp/www/js/activities.json"
    #with open(activity_file, "r") as f:
    #       activities = json.loads(f.read())

    # GET ELECTRICTY READINGS
    sqlq = "SELECT dt,watt FROM Electricity_1min WHERE Meta_idMeta = %s;" % metaID

    result = getSQL(sqlq)
    watt=[]
    date_time=[]
    for item in result:
        #date_time.append(item[0])
        #watt.append(item[1])
        date_time.append(item['dt'])
        watt.append(item['watt'])

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
    result = getSQL(sqlq)

    for item in result:
        tuc_time.append(item['dt_activity'])
        tuc_key.append(item['activity'])
        tuc_location.append(item['location'])
        thisCat = activities['activities'][item['activity']]['category']
        tuc_category.append(thisCat)
        if (str(item['location']) == "1"):
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
    os.system("scp " + plotFilePath + " phil@109.74.196.205:/var/www/energy-use.org/public_html/data/")

def data_download():
    # pull files from phone
    call('adb pull /sdcard/METER/ ' + filePath, shell=True)
    cmd = 'adb shell ls /sdcard/Meter/'
    s = subprocess.check_output(cmd.split())
    call('adb shell rm -rf /sdcard/Meter/*.csv', shell=True)
    call('adb shell rm -rf /sdcard/Meter/*.meta', shell=True)
    updateIDfile('0')              # set to 0 to avoid confusion if phone comes on again
    MeterApp.switchForm('MetaForm')

def data_review():
    MeterApp.switchForm('MetaForm')

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
    metaID = getMetaIDs(_householdID,'E')        # only fetches the first (should only be one...)
    if (metaID != ''):
        sqlq = "SELECT idElectricity FROM Electricity WHERE %s\
                AND Meta_idMeta = %s ORDER BY dt;" % (_condition,metaID)
        eIDs = getSQL(sqlq)
        if eIDs:
            prevID   =  int("%s" % eIDs[0]['idElectricity'])
            startIDs = [prevID]
            endIDs   = []
            durations= []
        
            for eID in eIDs:
                eID = int("%d" % eID['idElectricity'])
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

def upload_1min_readings(hhID):
    # sqlq = "SELECT Meta.idMeta \ From Meta \ Join Household \ On Household.idHOusehold = Meta.Household_idHousehold \ where Household.status >5 AND Household.status < 10 \ AND DataType = 'E' AND Household.Contact_idContact < 5001;"
    # sqlq = "SELECT distinct(Meta_idMeta) FROM Electricity;" # used for initial catchup on all that is in Electricity table

    sqlq="SELECT idMeta \
            From Meta \
            WHERE DataType = 'E' AND \
            Household_idHousehold =%s" % hhID
    EmetaIDs = getSQL(sqlq)

    dbConnection = getConnection()

    for idMeta in EmetaIDs:
        sqlq = "select * from Meter.Electricity where Meta_idMeta=%s" % idMeta['idMeta']
        df_elec       = pd.read_sql(sqlq, con=dbConnection)
        df_elec.index = pd.to_datetime(df_elec.dt)                           # index by time
        df_elec_resampled = df_elec.resample('1min',label='left').median()   # downsample, label left such that time refers to the next minute
        del df_elec_resampled['idElectricity']                               # remove index, so that a new one is auto-incremented
        df_elec_resampled.to_sql(con=dbConnection, name='Electricity_1min', if_exists='append', flavor='mysql') # pandas is brutal, if not append it rewrites the table!!
        # df_elec_resampled.to_csv("%s/el_%s_%s.csv" % (filePath,idMeta[0])) # create a csv copy

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
        executeSQL(sqlq)
        updateHouseholdStatus(householdID,6)
        upload_1min_readings(householdID)
    else:
        csv_data = csv.reader(file(dataFile))
        if (dataType == 'I'):
            sqlq = "INSERT INTO Individual(Meta_idMeta) VALUES('"+str(metaID)+"')"
            executeSQL(sqlq)                             # create an entry
            commit()
            individualID = cursor.lastrowid                  # get the id of the entry just made
            for row in csv_data:                             # populate columns
                sqlq = "UPDATE Individual SET " + row[1] + " = '" + row[2] + "'\
                        WHERE idIndividual = '"+str(individualID)+"';"
                executeSQL(sqlq)
        if (dataType == 'A'):
            for row in csv_data:                                                       # insert each line into Activities
                sqlq = "INSERT INTO Activities(Meta_idMeta,dt_activity,dt_recorded,tuc,category,activity,location,people,enjoyment,path) \
                        VALUES('"+row[0]+"', '"+row[1]+"', '"+row[2]+"', '"+row[3]+"', '"+row[4]+"', '"+row[5]+"', '"+row[6]+"', '"+row[7]+"', '"+row[8]+"', '"+row[9]+"')"
                executeSQL(sqlq)
    # update meta entry - this MUST already exist!
    # we don't want 'I' in the Meta table - only E or A
    if (dataType == 'I'):
        dataType = 'A'
    sqlq = "UPDATE Meta SET \
            `DataType`='"+ dataType +"', \
            `CollectionDate`='"+ collectionDate +"'\
            WHERE `idMeta`='" +metaID+"';"
    executeSQL(sqlq)
    commit()


def getDeviceMetaIDs(householdID, deviceType):
    # check if eMeter has been configured
    sqlq = "SELECT idMeta FROM Meta WHERE DataType = '%s' AND Household_idHousehold = '%s';" % (deviceType,householdID)
    results = getSQL(sqlq)
    metaIDs = ''
    if (results):
        for result in results:
            metaIDs = metaIDs + ("{:<6}".format("%s" % result['idMeta']))
    return metaIDs

def getParticipantCounters(householdID):
    counters = getParticipantCount(householdID)
    clist = ''
    for counter in range(counters):
        clist = clist + ("{:<6}".format("%s" % (counter + 1)))
    return clist


def getComment(householdID):
    # get the status for this household
    sqlq = "SELECT CONVERT(comment USING utf8) FROM Household WHERE idHousehold = '%s';" % householdID 
    result = getSQL(sqlq)[0]
    Comment
    return ("%s" % result['CONVERT(comment USING utf8)'])

def getStatus(householdID):
    # get the status for this household
    sqlq = "SELECT status FROM Household WHERE idHousehold = '%s';" % householdID 
    result = getSQL(sqlq)[0]
    return ("%s" % result['status'])

def getParticipantCount(householdID):
    # get number of diaries required
    sqlq ="SELECT age_group2, age_group3, age_group4, age_group5, age_group6\
            FROM Household \
            WHERE idHousehold = '" + householdID + "';"
    result = getSQL(sqlq)[0]
    return int(result['age_group2']) + int(result['age_group3']) + int(result['age_group4']) + int(result['age_group5']) + int(result['age_group6'])

def getHousehold():
    ## DISUSED
    # get the next hh matching the modus criteria
    global householdID
    sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE %s;" % Criteria[operationModus]
    result = getSQL(sqlq)[0]
    if (result):
        householdID =  ("%s" % result['idHousehold'])

def getPreviousHousehold(void):
    # get the next hh matching the modus criteria
    global householdID
    sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE idHousehold < %s AND %s;" % (householdID,Criteria[operationModus])
    result = getSQL(sqlq)[0]
    if (result):
        householdID =  ("%s" % result['idHousehold'])
    MeterApp._Forms['MAIN'].setMainMenu()

def getNextHousehold(void):
    # get the next hh matching the modus criteria
    global householdID
    sqlq = "SELECT idHousehold, Contact_idContact FROM Household WHERE idHousehold > %s AND %s;" % (householdID,Criteria[operationModus])
    result = getSQL(sqlq)[0]
    if (result):
        householdID =  ("%s" % result['idHousehold'])
    MeterApp._Forms['MAIN'].setMainMenu()

def updateDataQuality(idMeta,Quality):
    # set Quality in Meta table
    # called when compose_email('graph')
    # XXX add for diaries
    sqlq = "UPDATE Meta \
            SET `Quality`= %s \
            WHERE `idMeta` = %s;" % (Quality,idMeta)
    executeSQL(sqlq)
    commit()



def updateHouseholdStatus(householdID, status):
    # update status of household                            #statusUpdate
    status
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
    # 10: no el data recorder
    sqlq = "UPDATE Household \
            SET `status`="+ str(status) +"\
            WHERE `idHousehold` ='" + str(householdID) + "';"
    executeSQL(sqlq)
    commit()


def phone_id_setup(meterType):
    # 2 Nov 15 - assumes that the apps are already installed
    global metaID
    global householdID
    # 1) get household ID (assuming a 1:1 relationship!)
    # sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '"\
    #     + str(contactID) + "'"
    # executeSQL(sqlq)
    # householdID = ("%s" % cursor.fetchone())

    # 2) create a meta id entry for an 'eMeter'

    sqlq = "SELECT date_choice FROM Household WHERE idHousehold = '%s'"  %householdID
    result = getSQL(sqlq)[0]
    dateChoice = ("%s" % result['date_choice'])

    sqlq = "INSERT INTO Meta(DataType, Household_idHousehold, CollectionDate) \
           VALUES ('%s', '%s', '%s')" % (meterType,householdID,dateChoice)
    metaID = ("%s" % executeSQL(sqlq))
    commit()
    updateConfigFile(metaID,dateChoice)
    updateIDfile(metaID) # XXX currently douplicated with config file - eMeter could use json file, too...

    if (meterType == 'E'):
        # only need this once per household
        print_letter()
        updateHouseholdStatus(householdID,5)
    else:
        # Booklet sticker

        dt   = getHHdtChoice(householdID)
        dt2  = dt + datetime.timedelta(days = 1)
        date = dt.strftime("%-d %b")
        day1 = dt.strftime("%a")
        day2 = dt2.strftime("%a")

        templateText = getTemplate(letterPath + "from_to.md")
        templateText = templateText.replace("[day1]", day1)
        templateText = templateText.replace("[day2]", day2)
        templateText = templateText.replace("[date]", date)
        templateText = templateText.replace("[id]", metaID)

        printSticker(templateText,letterPath + "aMeter")

    MeterApp._Forms['MAIN'].wStatus2.value =\
        "Phone was assigned ID " + metaID
    MeterApp._Forms['MAIN'].wStatus2.display()
    MeterApp._Forms['MAIN'].setMainMenu()

def printSticker(text,fileName):
    myFile = open("%s.md" % (fileName), "w")
    myFile.write(text)
    myFile.close()
    call("pandoc -V geometry:paperwidth=8.8cm -V geometry:paperheight=5cm -s %s.md -o %s.pdf" % (fileName,fileName), shell=True)
    call('lp -d MeterLabel -o landscape ' + fileName + '.pdf', shell=True)


def updateConfigFile(_id,_dateChoice):
    today = datetime.datetime.now()
    dateFormat = '%Y-%m-%d'
    dateChoice_dt = datetime.datetime.strptime(_dateChoice,dateFormat)
    if (dateChoice_dt > today):     # only for testing
        dateChoice_dt = today
    startDate = dateChoice_dt.strftime("%Y-%m-%d")
    dateChoice_dt += datetime.timedelta(days=1)
    endDate   = dateChoice_dt.strftime("%Y-%m-%d")
    jstring = {"id": _id}
    jstring.update({"start": "%s" %startDate})
    jstring.update({"end": "%s" %endDate})  # XXX needs date + 1 Day
    times1 = [
            "17:30:00",
            "18:00:00",
            "18:30:00"]
    times2 = [
            "08:00:00",
            "08:30:00",
            "17:30:00",
            "18:00:00",
            "18:30:00"]
    dts = []
    for time in times1:
        dts.append("%s %s" %(jstring['start'],time))
    for time in times2:
        dts.append("%s %s" %(jstring['end'],time))
    jstring.update({"times": dts})
    config_file = open(configFilePath, "w")
    config_file.write(json.dumps(jstring, indent=4, separators=(',', ': ')))
    config_file.close()
    call('adb push ' + configFilePath + ' /sdcard/METER/', shell=True)

def updateIDfile(_id):
    idFile = open(idFilePath, 'w+')
    idFile.write(str(_id))
    idFile.close()
    # XXX only needs doing once, but flashing doesn't seem to create this folder
    call('adb shell mkdir /sdcard/METER', shell=True)
    call('adb push ' + idFilePath + ' /sdcard/METER/', shell=True)
    ## Android 6 (Pixi4) requires:
    # adb shell "date `date +%m%d%H%M%Y.%S`"
    call('adb shell date -s `date "+%Y%m%d.%H%M%S"`',  shell=True)
    # shut down phone (unless id is 0, i.e. the phone still needs setting up)
    if (_id != '0'):
        call('adb shell reboot -p',  shell=True)


def setSerialNumber(SerialNumber):
    # command typed number is set as serial number for current metaID
    metaID = getMetaIDs(householdID,'E')
    sqlq = "UPDATE Meta \
            SET SerialNumber = '%s'\
            WHERE idMeta = '%s'" % (SerialNumber,metaID)
    message(sqlq)
    executeSQL(sqlq)
    commit()



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
    # call('adb install -r ./apk/Insecure.apk',  shell=True)
    # to configure a phone, install insecure and tick the two boxes to root at start
    call('adb install -r ./apk/Flashify.apk',  shell=True)
    call('adb push ./apk/recovery.img /sdcard/',  shell=True)
    message("Complete process\n\
            1) connect to WiFi\n\
            2) run KingoRoot\n\
            3) Flashify > Recovery image > choose a file \"/sdcard/recovery.img\" >yup (2min)\n\
            4) <OK> this message to flash\n\)")
    flash_phone("E")

def flash_phone(meterType):
    # restore phone from Master copy
    if (meterType == 'E'):
        call('adb push ./flash_eMeter/ /sdcard/',  shell=True)
    elif (meterType == 'A'):
        call('adb push ./flash_aMeter/ /sdcard/',  shell=True)
    call('adb reboot recovery',  shell=True)
    message("Phone restarting\n\
            1) Restore \n\
            2) Select \"... KitKat\" swipe (2min) \n\
            3) Reboot System\n\
            4) Reconnect USB (!)\n\
            5) <OK> this message to configure ID")
    updateIDfile('0')

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

def getMetaIDs(hhID, deviceType):
    # check if eMeter has been configured
    sqlq = "SELECT idMeta FROM Meta WHERE DataType = '%s' AND Household_idHousehold = '%s';" % (deviceType,hhID)
    result = getSQL(sqlq)
    if (result):
        return ("%s" % result[0]['idMeta'])
    else:
        return ''


def getHHdtChoice(hhID):
    # reads a sql date in format "2016-12-31" and returns datetime object
    sqlq = "SELECT date_choice FROM Household WHERE idHousehold = '%s';" % hhID
    result = getSQL(sqlq)[0]
    dateStr = ("%s" % result['date_choice'])
    if (dateStr != 'None'):
        f = '%Y-%m-%d'
        return datetime.datetime.strptime(dateStr, f)
    else:
        return "None"

def getDateChoice(hhID):
    # return collection data as a string: "Sun, 31 Dec"
    this_dt = getHHdtChoice(hhID)
    if (this_dt != 'None'):
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

def compose_email(type,edit=True):
    # Contact participant with editabel email
    # edit = False -> send immediately
    global householdID
    # get contact details
    contactID = getContact(householdID)
    metaID    = getMetaIDs(householdID,'E')
    sqlq = "SELECT Name, Surname, Address1,Address2,Town,Postcode,email \
            FROM Contact \
            WHERE idContact = '%s';" % contactID
    result = getSQL(sqlq)[0]
    
    thisName    = ("%s %s" % (result['Name'], result['Surname']))
    thisAddress = ("%s</br>%s</br>%s %s" % (result['Address1'],result['Address2'],result['Town'],result['Postcode']))
    thisAddress = thisAddress.replace("None </br>", "")
    thisDate    = getDateChoice(householdID)
    thisEmail   = ("%s" % (result['email']))
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
        updateDataQuality(metaID,1)
    elif (type == 'fail'):
        updateDataQuality(metaID,0)

    
    if (edit):
        call('vim ' + emailFilePath, shell=True)
        MeterApp._Forms['MAIN'].wMain.display() # XXX does not have the desired effect of removing the light 'vim' background
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
    results = getSQL(sqlq)
    for result in results:
        emailText = templateText.replace("[name]", result['Name'])
        emailAddress = result['email']
        emailFile = open(emailPathPersonal, "w+")
        emailFile.write(emailText)
        emailFile.close()
        call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + ' < ' + emailPathPersonal, shell=True)

def getTemplate(fileName):
    templateFile = open(fileName, "r")
    templateText = templateFile.read()
    templateFile.close()
    return templateText


def print_letter():
    # personal letter as pdf
    global householdID
    contactID = getContact(householdID)
    participantCount = ("%s" % getParticipantCount(str(householdID)))

    # The letter
    dateToday = datetime.datetime.now()
    todayDate = dateToday.strftime("%e %B %Y")

    sqlq = "SELECT Name, Surname, Address1,Address2,Town,Postcode FROM Contact WHERE idContact = '%s';" % contactID
    result = getSQL(sqlq)[0]
    thisName    = ("%s %s" % (result['Name'],result['Surname']))
    thisAddress = ("%s\n\n%s\n\n%s %s" % (result['Address1'],result['Address2'],result['Town'],result['Postcode']))
    thisAddress = thisAddress.replace("None\n\n", "")

    dt   = getHHdtChoice(householdID)
    dt2  = dt + datetime.timedelta(days = 1)
    date = dt.strftime("%-d %b")
    weekday = dt.strftime("%A")
    nextday = dt2.strftime("%A")

    templateText = getTemplate(letterPath + "letter_narrow.md")
    templateText = templateText.replace("[address]", thisAddress)
    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[today]", todayDate)
    templateText = templateText.replace("[date]", "%s" % date)
    templateText = templateText.replace("[weekday]", "%s" % weekday)
    templateText = templateText.replace("[nextday]", "%s" % nextday)
    templateText = templateText.replace("[participantCount]", participantCount)

    if (participantCount != "1"):
        templateText = templateText.replace("[s]", "s")
        templateText = templateText.replace("{multiple booklets}", " -- one for each household member above the age of eight. Do encourage the others to join you. The more people fill in their booklet, the better our understanding of electricity use becomes")
    else:
        templateText = templateText.replace("[s]", "")
        templateText = templateText.replace("{multiple booklets}", "") 

    myFile = open(letterPath + "temp_letter.md", "w+")
    myFile.write(templateText)
    myFile.close()

    letterFile = letterPath + contactID + "_letter"

    call('pandoc  --variable classoption=twocolumn -V geometry:margin=0.6in -V fontsize=11pt -s ' + letterPath + "temp_letter.md -o" + letterFile + ".pdf", shell=True)
    call('lp -d Xerox_Phaser_3250 ' + letterFile + '.pdf', shell=True)

    # ADDRESS LABEL
    # produces postage label and personal letter

    address = getTemplate(letterPath + "_address.md")
    address = address.replace("[Name]",      thisName)
    address = address.replace("[Address1]", "%s" % result['Address1'])
    address = address.replace("[Address2]", "%s" % result['Address2'])
    address = address.replace("[Town]",     "%s" % result['Town'])
    address = address.replace("[Postcode]", "%s" % result['Postcode'])
    address = address.replace("None", "")

    printSticker(address,letterPath + "address")

# ------------------------------------------------------------------------------
# --------------------------FORMS-----------------------------------------------
# ------------------------------------------------------------------------------

class ActionControllerData(nps.MultiLineAction):
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
            '>': getNextHousehold,
            '<': getPreviousHousehold,

            'P': self.btnP,
            # 'P': self.data_download,
            'S': self.showHouseholds,
            "M": toggleOperationModus,
            "q": self.show_MainMenu,
            "Q": self.parent.exit_application,
            # "t": self.show_DataTypes,
            # "c": self.show_Contact,
            # "a": self.show_NewContact,
            # "I": self.show_Individual,
            # "m": self.show_MetaForm,
            # "s": self.show_MainMenu,
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

        elif (self.parent.myStatus == 'DataTypes'):
            dataTypeArray = selectedLine.split('\t')
            dataType = str(dataTypeArray[0])
            self.parent.wStatus2.value =\
                "Data type changed to " + str(dataTypeArray[2])
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

    def btnA(self, *args, **keywords):
        updateIDfile('0')              # set to 0 to avoid confusion if phone comes on again
        #print_letter()
        # pass
        # upload_1min_readings(householdID)

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

    def formated_data_type(self, vl):
        return "%s (%s)" % (vl[1], str(vl[0]))

    def formated_contact(self, vl):
        return "%s %s, %s" % (vl[1], vl[2], str(vl[0]))

    def formated_word(self, vl):
        return "%s" % (vl[0])


class ActionControllerSearch(nps.ActionControllerSimple):
    def create(self):
        self.add_action('^/.*', self.set_search, True)
        self.add_action('^:\d.*', self.set_serialNumber, False)

    def set_search(self, command_line, widget_proxy, live):
        self.parent.value.set_filter(command_line[1:])
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()

    def set_serialNumber(self, command_line, widget_proxy, live): # just for testing
        setSerialNumber(command_line[1:])


    # NEEDED???
    def setMainMenu(self, command_line, widget_proxy, live):
        self.parent.setMainMenu()


class MeterMain(nps.FormMuttActiveTraditionalWithMenus):
    ACTION_CONTROLLER = ActionControllerSearch
    MAIN_WIDGET_CLASS = ActionControllerData
    first_time = True
    myStatus = "Main"

    global cursor
    cursor = connectDatabaseOLD(dbHost)

    def getMenuText(self):                                      #menu_text
        global householdID
        dbHost = getHost()
        householdID = str(householdID)
        contactID   = getContact(householdID)
        MenuText = []
        MenuText.append("\n")
        for line in open("meterLogo.txt", "r"):
            MenuText.append("\t" + line)
        MenuText.append("\n")
        hits = getHouseholdCount(Criteria[operationModus])
        MenuText.append("\t\t\t _____________________________________________")  
        MenuText.append(formatBox("[M]odus:", "%s (%s)" % (operationModus, hits)))
        MenuText.append("\t\t\t _____________________________________________")  
        MenuText.append("\n")
        if (householdID != "0"):
            MenuText.append("\t\t\t _____________________________________________")  
            MenuText.append(formatBox("Contact:",  getNameOfContact(contactID) + ' (' + contactID + ')'))
            MenuText.append("\t\t\t _____________________________________________")  
            MenuText.append(formatBox("Date:", getDateChoice(householdID)))
            MenuText.append(formatBox("Household:", householdID))
            MenuText.append(formatBox("Status:", getStatus(householdID)))
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
        ])
        self.m2 = self.add_menu(name="Setup a batch", shortcut="B")
        self.m2.addItem(text='Show Households', onSelect=MeterApp._Forms['MAIN'].display_selected_data, shortcut='S', arguments=['Households'])
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
        self.m2.addItem(text='Request return', onSelect=compose_email, shortcut='r', arguments=['request_return'])

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
        self.m2.addItem(text='Change database', onSelect=self.toggleDatabase, shortcut='d')
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

    def toggleDatabase(self):
        toggleDatabase()
        MeterApp._Forms['MAIN'].setMainMenu()

    def identifyHousehold(self):
        global householdID 
        message('XXX check code to hande multiple housholds for one contact')
        sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID + "'"
        result = getSQL(sqlq)[0]
        householdID = str(int(result['idHousehold']))
        self.wStatus2.value =\
            "Household changed directly to " + householdID
        self.wStatus2.display()
        self.setMainMenu()

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
            result = getSQL(sqlq)

        elif (displayModus == "Households"):
            result = ["{:<8}".format('HH ID') +\
                       "{:<7}".format('CT ID') +\
                       "{:<11}".format('Joined') +\
                       "{:<20}".format('Name') +\
                       "{:<7}".format('Status') +\
                       "{:<11}".format('Date') +\
                       "{:<7}".format('#') +\
                       "{:<25}".format('Comment') ]

            global operationModus
            fields ='idHousehold, timestamp, Contact_idContact, date_choice, CONVERT(comment USING utf8), status' 
            sqlq = "SELECT " + fields + " FROM Household WHERE " + Criteria[operationModus] +";"
            # executeSQL(sqlq)
            hh_result = getSQL(sqlq)
            for hh in hh_result:
                thisHHid      = str(hh['idHousehold'])
                thisTimeStamp = getDateTimeFormated(str(hh['timestamp']))
                thisContact   = str(hh['Contact_idContact'])
                thisDate      = str(hh['date_choice'])
                thisComment   = str(hh['CONVERT(comment USING utf8)'])
                thisStatus    = str(hh['status'])
                result = result + [\
                        "{:<7}".format(thisHHid) + '\t'\
                        "{:<7}".format(thisContact) + '\t'\
                        "{:<11}".format(thisTimeStamp +'\t') +\
                        "{:<20}".format(getNameOfContact(thisContact)) +\
                        "{:<7}".format(thisStatus) +\
                        "{:<11}".format(thisDate) +\
                        "{:<3}".format(str(getParticipantCount(thisHHid))) +\
                        "{:<25}".format(thisComment) ]


        elif (displayModus == "Household"):
            sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID + "'"
            result = getSQL(sqlq)

        else:
            sqlq = "SELECT * FROM " + self.myStatus
            result = getSQL(sqlq)

        # result is populated, now display result
        displayList = []
        if (displayModus == "Contact"):
            for items in result:

                keys = items.keys()
                values = [items[key] for key in keys]
                # displayList.append(self.formated_contact(items))
                displayList.append(self.formated_any(values))
        elif (displayModus == "DataType"):
            for items in result:
                displayList.append(self.formated_two(items))
        else:
            for items in result:
                # displayList.append(self.formated_any(items))
                displayList.append(items)
        # update display
        self.value.set_values(displayList)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        self.wStatus1.display()

        commit()
        # global dbConnection
        # dbConnection.commit()
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
        sqlq = "SHOW TABLES"
        results = getSQL(sqlq)
        displayList = []
        for items in results:
            displayList.append(items['Tables_in_Meter'])

        # self.wMain.values = displayList
        self.value.set_values(displayList)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        # self.wMain.values = self.formated_word(result)
        # return result

    def exit_application(self, command_line=None, widget_proxy=None, live=None):
        global cursor
        cursor.close()
        self.parentApp.setNextForm(None)
        self.editing = False
        self.parentApp.switchFormNow()


class newContactForm(nps.Form):
    # gets fields from database, collects new entries
    def create(self):
        # get Household fields
        self.ColumnName = []
        self.ColumnEntry = []
        sqlq = "SHOW columns from Contact;"
        tabledata = getSQL(sqlq)
        for field in tabledata:
            self.ColumnName.append(field['Field'])
        self.ColumnName.pop()       # remove 'recorded' field (auto completed)
        
        for item in range(0, len(self.ColumnName)):
            self.ColumnEntry.append(self.add(nps.TitleText,
                                    name=self.ColumnName[item]))
        # self.ColumnName.pop(0)   # to leave out the ID column
        # cursor.close()

    def afterEditing(self):
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
        contactID = executeSQL(sqlq)
        commit()
        
        # create household
        sqlq = "INSERT INTO `Household`(Contact_idContact, security_code) \
            VALUES (%s, 123);" % contactID
        householdID = executeSQL(sqlq)
        commit()
        self.parentApp.setNextFormPrevious()


class metaFileInformation(nps.Form):
    # The MetaForm
    # display all .meta files in /METER/
    def create(self):
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

        self.FileSelection = self.add(nps.TitleMultiSelect, max_height=9,
                                      value=selectIndex,
                                      name="Which files should be uploaded?",
                                      values=displayString,
                                      scroll_exit=True)
        self.FileRejection = self.add(nps.TitleMultiSelect, max_height=15,
                                      value=reject_Index,
                                      name="These files will be deleted (uncheck to save them)?",
                                      values=reject_displayString, scroll_exit=True)

    def beforeEditing(self):
        self.fileList = []      # added to not carry over old file lists
        self.reject_fileList = []

        self.selectIndex = []
        self.selectCounter = 0
        self.metaIDs = []
        self.collectionDate = []
        self.dataType = []
        self.duration = []
        self.displayString = []

        self.reject_Index = []
        self.reject_Counter = 0
        self.reject_contactID = []
        self.reject_collectionDate = []
        self.reject_dataType = []
        self.reject_duration = []
        self.reject_displayString = []

        self.FileSelection.values = self.displayString
        self.FileRejection.values = self.reject_displayString

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


class MeterForms(nps.NPSAppManaged):
    def onStart(self):
        # nps.setTheme(npyscreen.Themes.ColorfulTheme)
        self.addForm('MAIN', MeterMain, lines=36)
        self.addForm('NewContact', newContactForm, name='New Contact')
        self.addForm('MetaForm', metaFileInformation, name='Meta Data')

if __name__ == "__main__":
    MeterApp = MeterForms()
    MeterApp.run()
    exit()
