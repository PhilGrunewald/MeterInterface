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
import npyscreen as nps

from meter import *         # db connection and npyscreen features
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
emailFilePath = emailPath + "email_many.html"
attachment = ''

dateTimeToday = datetime.datetime.now()
str_date = dateTimeToday.strftime("%Y-%m-%d")

#     def connectDatabase(_dbHost):
#     global dbConnection
#     global dbHost
#     dbHost = _dbHost
#     try:
#         dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName, cursorclass = MySQLdb.cursors.DictCursor)
#         cursor = dbConnection.cursor()
#     except:
#         dbHost='localhost'
#         dbConnection = MySQLdb.connect(host=dbHost, user=dbUser, passwd= dbPass, db=dbName, cursorclass = MySQLdb.cursors.DictCursor)
#         cursor = dbConnection.cursor()
#     return cursor

# def executeSQL(_sqlq):
#     # to safeguard against dropped connections
#     global cursor
#     try:
#         cursor.execute(_sqlq)
#     except:
#         message("Need to reconnect to datahase")
#         cursor = connectDatabase(dbHost)
#         cursor.execute(_sqlq)
# 
# def getSQL(_sqlq):
#     # to safeguard against dropped connections
#     global cursor
#     try:
#         cursor.execute(_sqlq)
#     except:
#         message("Need to reconnect to datahase")
#         cursor = connectDatabase(dbHost)
#         cursor.execute(_sqlq)
#     return cursor.fetchall()
#     # return list(cursor.fetchall())
# 
# def toggleDatabase(void):
#     global cursor
#     global dbHost
#     if (dbHost == 'localhost'):
#         dbHost = '109.74.196.205'
#     else:
#         dbHost = 'localhost'
#     cursor = connectDatabase(dbHost)
#     MeterApp._Forms['MAIN'].setMainMenu()

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

# def getNameEmail(criterium):
#     global table
#     if (table == "Contact"):
#         sqlq = "SELECT Contact.idContact,Contact.Name,Contact.email\
#                 From Contact\
#                 Join Household\
#                 ON Household.Contact_idContact = Contact.idContact\
#                 WHERE %s" % criterium
#     else:
#         sqlq = "Select *\
#                 FROM %s\
#                 WHERE %s" % (table,criterium)
#     result = getSQL(sqlq)
#     return result
# 
# def getRecipientCount(criterium):
#     return len(getNameEmail(criterium))
# 
# 
# def getNameOfContact(thisContactID):
#     # get Contact name for a given Contact
#     sqlq ="SELECT Name,Surname\
#             FROM Contact \
#             WHERE idContact = '" + thisContactID + "';"
#     executeSQL(sqlq)
#     result = cursor.fetchone()
#     return str(result[0]) + ' ' + str(result[1])
# 
# def getStatus(householdID):
#     # get the status for this household
#     sqlq = "SELECT status FROM Household WHERE idHousehold = '" + householdID + "'"
#     executeSQL(sqlq)
#     return ("%s" % (cursor.fetchone()))
# 
# def getDateTimeFormated(dts):
#     # DateTimeString as received from database: return 31 Jan 16
#     # http://strftime.org/
#     if (dts != 'None'):
#         f = '%Y-%m-%d %H:%M:%S'
#         this_dt = datetime.datetime.strptime(dts, f)
#         return this_dt.strftime("%-d %b %y")
#     else:
#         return "None"


def editMessage():
    # compose message
    # emailFilePath = emailPath + "email_many.html"
    call('vim ' + emailFilePath, shell=True)

def sendTo(condition,attach):
    # compose message
    emailRCFilePath = emailPath + ".emailrc"
    templateFile = open(emailFilePath, "r")
    templateText = templateFile.read()
    templateFile.close()

    subjectLine = templateText.splitlines()[0]
    templateText = templateText[templateText.find('\n')+1:]     # find line break and return all from there - i.e. remove first line

    # personalise
    emailPathPersonal = emailPath + "email_personal.html"

    # get all recipients
    results = getNameEmail(table,condition)
    message("About to send %s emails from %s" % (len(results), condition))
    if attach != '':
        attach = " -a %s " % attach
    for result in results:
        emailText = templateText.replace("[name]", "%s" % result["Name"])
        emailAddress = "%s" % result["email"]
        emailFile = open(emailPathPersonal, "w+")
        emailFile.write(emailText)
        emailFile.close()
        call('mutt -F "'+emailRCFilePath+'" -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + attach + ' < ' + emailPathPersonal, shell=True)


# def formatBox(col1, col2):
#     return "\t\t\t|\t\t" + "{:<22}".format(col1) + "{:<20}".format(col2) + "|"
# 
# def formatList(col1, col2):
#     return ["\t\t\t" + "{:<25}".format(col1) + "{:<30}".format(col2)]

def message(msgStr):
    # shorthand to display debug information
    nps.notify_confirm(msgStr,editw=1)


# ------------------------------------------------------------------------------
# --------------------------FORMS-----------------------------------------------
# ------------------------------------------------------------------------------

class ActionControllerData(nps.MultiLineAction):
    # action key shortcuts                                      #action_keys
    def __init__(self, *args, **keywords):
        super(ActionControllerData, self).__init__(*args, **keywords)
        global MenuActionKeys
        MenuActionKeys = {
            "A": self.btnA,
            "M": toggleTable,
            'E': self.btnE,
            "R": self.btnR,
            "T": self.btnT,
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

        elif (self.parent.myStatus == 'FileSelection'):
            # items are padded out with spaces to produce neat columns. These are removed with .strip()
            global emailFilePath
            dataArray   = selectedLine.split('\t')
            emailFile   = str(dataArray[1]).strip()
            emailFilePath = emailPath + emailFile
            self.parent.wStatus2.value = "Template file: %s" % emailFile
            self.parent.wStatus2.display()
            self.parent.setMainMenu()

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

    def btnA(self, *args, **keywords):
        self.parent.spawn_file_dialog()

    def btnT(self, *args, **keywords):
        self.parent.displayTemplates()

    def btnR(self, *args, **keywords):
        MeterApp._Forms['MAIN'].display_selected_data()

    def btnE(self, *args, **keywords):
        editMessage()

    def show_MainMenu(self, *args, **keywords):
        self.parent.setMainMenu()


class ActionControllerSearch(nps.ActionControllerSimple):
    def create(self):
        self.add_action('^/.*\..*', self.set_command, False)
        self.add_action('^/.*', self.set_search, True)
        self.add_action('^:a.*', self.set_command, False)
        self.add_action('^:show', self.show, False)

    def set_search(self, command_line, widget_proxy, live):
        self.parent.value.set_filter(command_line[1:])
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()

    def show(self, command_line, widget_proxy, live):
        MeterApp._Forms['MAIN'].display_selected_data()

    def set_command(self, command_line, widget_proxy, live):
        global attachment
        entries = command_line.split(' ')
        attachment = entries[0]
        message("Attaching: %s" % entries[0])
        # XXX find out how to clear the 'command status' / display main screen (switch form?)

    # NEEDED???
    def xxsetMainMenu(self, command_line, widget_proxy, live):
        self.parent.setMainMenu()

class MeterMail(nps.FormMuttActiveTraditionalWithMenus):
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

        MenuText.append("\t\t\t ____________________________________________")  
        MenuText.append(formatBox("[M]ail list:", table)) 
        MenuText.append(formatBox("[S]election:", subsection)) 
        templateFileName = os.path.basename(emailFilePath)
        MenuText.append(formatBox("[T]emplate:", templateFileName)) 
        attachFileName = os.path.basename(attachment)
        MenuText.append(formatBox("[A]tttachment:", attachFileName)) 
        MenuText.append(formatBox("Recipients:", getRecipientCount(table,Criteria[subsection]))) 
        MenuText.append("\t\t\t ____________________________________________")  
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
        self.m2.addItem(text='Select message', onSelect=MeterApp._Forms['MAIN'].displayTemplates, shortcut='M')
        self.m2.addItem(text='Edit message', onSelect=editMessage, shortcut='e')
        self.m2.addItem(text='Recipents', onSelect=MeterApp._Forms['MAIN'].display_selected_data, shortcut='R')
        self.m2.addItem(text="Send message", onSelect = self.sendMessage, shortcut="S")

        self.m3 = self.add_menu(name="Exit", shortcut="X")
        self.m3.addItem(text="File", onSelect = self.spawn_file_dialog,shortcut="F")
        self.m3.addItem(text="Home", onSelect = MeterApp._Forms['MAIN'].setMainMenu,shortcut="h")
        self.m3.addItem(text="Exit", onSelect = self.exit_application, shortcut="X")

    def spawn_file_dialog(self):
        global attachment
        attachment = nps.selectFile()
        MeterApp._Forms['MAIN'].setMainMenu()

    def sendMessage(self):
        # send to selection
        # global subsection
        condition = Criteria[subsection]
        sendTo(condition,attachment)

    def displayTemplates(self):
        self.myStatus = 'FileSelection'
        allEmailFiles = emailPath + '*.html'
        EmailFileList = glob.glob(allEmailFiles)
        displayText = []
        for file in EmailFileList:
            displayText = displayText + ["\t" + os.path.basename(file) + "\n"]

        self.value.set_values(displayText)
        self.wMain.values = self.value.get()  # XXX testj
        self.wMain.display()
        self.wStatus1.display()

    def display_selected_data(self):
        # pull SQL data and display                     #display_data
        global subsection
        result = getNameEmail(table,Criteria[subsection])

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



class MeterForms(nps.NPSAppManaged):
    def onStart(self):
        self.addForm('MAIN', MeterMail)

if __name__ == "__main__":
    MeterApp = MeterForms()
    MeterApp.run()
    exit()
