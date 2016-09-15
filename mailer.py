#!/usr/bin/python

import os
import csv
import MySQLdb
import MySQLdb.cursors
import datetime            # needed to read TIME from SQL

from subprocess import call
import subprocess
from sys import stdin
import glob                 # for reading files in directory
from xml.etree import ElementTree as et  # to modify sting xml file for android
import npyscreen

from meter_ini import *     # reads the database and file path information from meter_ini.py

tables = ['Contact', 'Mailinglist']

subsections = {'Contact': ['All', 'No date', 'Pre trial', 'Post trial'],
               'Mailinglist': ['All', 'Panel', 'Updates', 'Test']} 

Criteria = {
        'All':       'email <> \'%@%\'',
        'No date':   'Household.status < 2',
        'Pre trial': 'Household.status > 1 AND Household.status < 6',
        'Post trial':'Household.status > 5',
        'Panel':     'status = \'panel\'',
        'Updates':     'status = \'updates\'',
        'Test':     'status = \'test\''
        }
table = tables[0]
subsection = subsections[table][0]

dateTimeToday = datetime.datetime.now()
str_date = dateTimeToday.strftime("%Y-%m-%d")

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

def executeSQL(_sqlq):
    # to safeguard against dropped connections
    global cursor
    try:
        cursor.execute(_sqlq)
    except:
        npyscreen.notify_confirm("Need to reconnect to datahase")
        cursor = connectDatabase(dbHost)
        cursor.execute(_sqlq)

def getSQL(_sqlq):
    # to safeguard against dropped connections
    global cursor
    try:
        cursor.execute(_sqlq)
    except:
        npyscreen.notify_confirm("Need to reconnect to datahase")
        cursor = connectDatabase(dbHost)
        cursor.execute(_sqlq)
    return cursor.fetchall()
    # return list(cursor.fetchall())

def toggleDatabase(void):
    global cursor
    global dbHost
    if (dbHost == 'localhost'):
        dbHost = '109.74.196.205'
    else:
        dbHost = 'localhost'
    cursor = connectDatabase(dbHost)
    MeterApp._Forms['MAIN'].setMainMenu()

def toggleTable(void):
    global subsection
    global tables
    global table
    tableIndex = tables.index(table)
    tableIndex = (tableIndex+1) % len(tables)
    table = tables[tableIndex]
    subsection = subsections[table][0]
    MeterApp._Forms['MAIN'].setMainMenu()

def togglesubsection(void):
    global subsection
    global table
    modusNumber = subsections[table].index(subsection)
    modusNumber = (modusNumber+1) % len(subsections[table])
    subsection = subsections[table][modusNumber]
    MeterApp._Forms['MAIN'].setMainMenu()

def getNameEmail(criterium):
    global table
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

def getRecipientCount(criterium):
    return len(getNameEmail(criterium))


def getNameOfContact(thisContactID):
    # get Contact name for a given Contact
    sqlq ="SELECT Name,Surname\
            FROM Contact \
            WHERE idContact = '" + thisContactID + "';"
    executeSQL(sqlq)
    result = cursor.fetchone()
    return str(result[0]) + ' ' + str(result[1])

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
    executeSQL(sqlq)
    result = cursor.fetchone()
    thisName    = ("%s %s" % (result[0:2]))
    thisAddress = ("%s</br>%s</br>%s %s" % (result[2:6]))
    thisAddress = thisAddress.replace("None </br>", "")
    thisDate    = getDateChoice(householdID)
    thisEmail   = ("%s" % (result[6]))
    CcEmail     = 'philipp.grunewald@ouce.ox.ac.uk'

    thisAddress = thisAddress.replace("None</br>", "")

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
        pass
        # call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + thisEmail + ' -b philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath, shell=True)

def editMessage():
    # compose message
    emailFilePath = emailPath + "email_many.html"
    call('vim ' + emailFilePath, shell=True)


def sendTo(condition):
    # compose message
    emailFilePath = emailPath + "email_many.html"
    templateFile = open(emailFilePath, "r")
    templateText = templateFile.read()
    templateFile.close()

    subjectLine = templateText.splitlines()[0]
    templateText = templateText[templateText.find('\n')+1:]     # find line break and return all from there - i.e. remove first line

    # personalise
    emailPathPersonal = emailPath + "email_personal.html"

    # get all recipients
    results = getNameEmail(condition)
    for result in results:
        emailText = templateText.replace("[name]", "%s" % result["Name"])
        emailAddress = "%s" % result["email"]
        emailFile = open(emailPathPersonal, "w+")
        emailFile.write(emailText)
        emailFile.close()
        print 'mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + ' < ' + emailPathPersonal
        # XXX call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + ' < ' + emailPathPersonal, shell=True)


def pre_parcel_email(householdID):
    # send an email to check contact details are right
    contactID = getContact(householdID)

    # get contact details
    sqlq = "SELECT Name, Surname, Address1,Address2,Town,Postcode,email FROM Contact WHERE idContact = '"\
        + contactID + "'"
    executeSQL(sqlq)
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

def formatBox(col1, col2):
    return "\t\t\t|\t\t" + "{:<22}".format(col1) + "{:<20}".format(col2) + "|"

def formatList(col1, col2):
    return ["\t\t\t" + "{:<25}".format(col1) + "{:<30}".format(col2)]

def message(msgStr):
    # shorthand to display debug information
    npyscreen.notify_confirm(msgStr)


# ------------------------------------------------------------------------------
# --------------------------FORMS-----------------------------------------------
# ------------------------------------------------------------------------------

class ActionControllerData(npyscreen.MultiLineAction):
    # action key shortcuts                                      #action_keys
    def __init__(self, *args, **keywords):
        super(ActionControllerData, self).__init__(*args, **keywords)
        global MenuActionKeys
        MenuActionKeys = {
            "A": toggleTable,
            'E': self.btnE,
            "R": self.btnR,
            "S": togglesubsection,
            "q": self.show_MainMenu,
            "Q": self.parent.exit_application,
        }
        self.add_handlers(MenuActionKeys)


    def actionHighlighted(self, selectedLine, keypress):
        # choose action based on the display status and selected line           #action_highlighted

        if (self.parent.myStatus == 'Main'):
            self.parent.wMain.values = ['Selection: ', selectedLine,
                                        '\tM\t\t to return to the main menu']
            self.parent.wMain.display()
            global MenuActionKeys
            MenuActionKeys[selectedLine[1]]()

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

    def btnR(self, *args, **keywords):
        MeterApp._Forms['MAIN'].display_selected_data()

    def btnE(self, *args, **keywords):
        editMessage()

    def show_MainMenu(self, *args, **keywords):
        self.parent.setMainMenu()


class ActionControllerSearch(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^/.*', self.set_search, True)

    def set_search(self, command_line, widget_proxy, live):
        self.parent.value.set_filter(command_line[1:])
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()

    # NEEDED???
    def setMainMenu(self, command_line, widget_proxy, live):
        self.parent.setMainMenu()

class MeterMail(npyscreen.FormMuttActiveTraditionalWithMenus):
    ACTION_CONTROLLER = ActionControllerSearch
    MAIN_WIDGET_CLASS = ActionControllerData
    first_time = True
    myStatus = "Main"

    global cursor
    cursor = connectDatabase(dbHost)

    def getMenuText(self):                                      #menu_text
        MenuText = []
        # CommandNumber=0
        MenuText.append("\n")
        for line in open("meterLogo.txt", "r"):
            MenuText.append("\t" + line)
        MenuText.append("\n")

        MenuText.append("\t\t\t _____________________________________________")  
        MenuText.append(formatBox("[A]ddress table:", table)) 
        MenuText.append(formatBox("[S]election:", subsection)) 
        MenuText.append(formatBox("Recipients:", getRecipientCount(Criteria[subsection]))) 
        MenuText.append("\t\t\t _____________________________________________")  
        MenuText.append("\n")
        MenuText.append("Database: " + dbHost)
        MenuText.append("\n")
        MenuText.append("\t\t\t[^X] Menu   [R]ecipients    [E]dit message    [/] Search     [Q]uit")
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

    def update_list(self):
        self.wStatus1.value = "METER " + self.myStatus
        self.wMain.values = self.value.get()

    def initialise(self):
        # menu and sub-menues           #menu_bar
        global dataType
        self.m2 = self.add_menu(name="Email", shortcut="B")
        self.m2.addItem(text='Edit message', onSelect=editMessage, shortcut='e')
        self.m2.addItem(text='Recipents', onSelect=MeterApp._Forms['MAIN'].display_selected_data, shortcut='R')
        self.m2.addItem(text="Send message", onSelect = self.sendMessage, shortcut="S")

        self.m3 = self.add_menu(name="Exit", shortcut="X")
        self.m3.addItem(text="Home", onSelect = MeterApp._Forms['MAIN'].setMainMenu,shortcut="h")
        self.m3.addItem(text="Exit", onSelect = self.exit_application, shortcut="X")

    def sendMessage(self):
        # send to selection
        global subsection
        condition = Criteria[subsection]
        sendTo(condition)


    def display_selected_data(self):
        # pull SQL data and display                     #display_data
        global subsection
        result = getNameEmail(Criteria[subsection])

        self.myStatus = subsection
        self.wStatus1.value = subsection + " from " + table 
        displayText = formatList('Name','e-mail')

        for recipient in result:
                displayText = displayText + formatList(recipient["Name"],recipient["email"])

        # update display
        self.value.set_values(displayText)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        self.wStatus1.display()

    def exit_application(self, command_line=None, widget_proxy=None, live=None):
        global cursor
        cursor.close()
        self.parentApp.setNextForm(None)
        self.editing = False
        self.parentApp.switchFormNow()



class MeterForms(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm('MAIN', MeterMail)

if __name__ == "__main__":
    MeterApp = MeterForms()
    MeterApp.run()
    exit()
