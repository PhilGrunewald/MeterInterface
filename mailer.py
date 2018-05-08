#!/usr/bin/python

# SQL to mark all mailing list people who are also participants (to avoid duplication)
# update Mailinglist m join Contact c on m.email = c.email set m.status = 'participant';

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
from interface_ini import *     # reads the database and file path information from meter_ini.py

tables = ['Contact', 'Mailinglist', 'OE_mail']

subsections = {'Contact': ['18Mar28','renters', 'TestC', 'All', 'No date', 'Pre trial', 'Post trial'],
               'OE_mail': ['Test',  '1st round', 'reminder'],
               'Mailinglist': ['Workshop','All', 'Panel', 'Updates', 'Test']} 

Criteria = {
            'All':       'email <> \'%@%\'',
        'No date':   'Household.status = 1',
        'Pre trial': 'Household.status = 2',
        'Post trial':'Household.status >= 3',
        'Panel':     'status = \'panel\'',
        'Updates':   'status = \'updates\'',
        'Workshop':  'status IN (\'updates\', \'panel\', \'participant\')',
        'TestC':     'idContact = 0',
        'Test':      'status = \'test\'',
        '1st round': 'status = \'2e\'',
        '2nd round': 'status = \'2\'',
        'renters'  : 'own > 1 and Household.status < 4 and date_choice < CURDATE()',
        'reminder': 'confirmed = "yes" or confirmed = "panel"',
        'early':     'Contact.status = \'early\'',
        '17Nov24':  'idContact IN (\'5133\', \'5148\', \'5152\', \'5162\', \'5173\', \'5179\', \'5191\', \'5218\', \'5255\', \'5261\', \'5263\', \'5266\', \'5273\', \'5288\', \'5299\', \'5325\', \'5354\', \'5365\', \'5366\', \'5369\', \'5377\', \'5379\', \'5381\', \'5396\', \'5401\', \'5428\', \'5571\', \'5588\', \'5589\', \'5615\', \'5616\', \'5623\', \'5656\', \'5711\')',


        '17Oct30': 'idHousehold IN (\'7941\', \'7945\', \'7962\', \'7966\', \'7967\', \'7976\', \'7987\', \'7993\', \'8006\', \'8315\', \'8070\', \'8078\', \'8081\', \'8089\', \'8107\', \'8119\', \'8129\', \'8146\', \'8148\', \'8176\', \'8185\', \'8188\', \'8189\', \'8192\', \'8200\', \'8202\', \'8204\', \'8221\', \'8228\', \'8257\', \'8261\', \'8697\', \'8408\', \'8431\', \'8450\', \'8468\', \'8535\', \'8538\', \'8539\', \'8550\', \'8585\', \'8640\')',

        '17Nov15': 'idContact IN (\'5128\',\'5131\',\'5133\',\'5148\',\'5152\',\'5154\',\'5162\',\'5173\',\'5174\',\'5179\',\'5191\',\'5196\',\'5213\',\'5215\',\'5218\',\'5226\',\'5227\',\'5229\',\'5230\',\'5234\',\'5245\',\'5248\',\'5251\',\'5253\',\'5255\',\'5259\',\'5261\',\'5262\',\'5263\',\'5266\',\'5270\',\'5273\',\'5283\',\'5284\',\'5285\',\'5288\',\'5296\',\'5299\',\'5300\',\'5301\',\'5309\',\'5312\',\'5321\',\'5324\',\'5325\',\'5327\',\'5348\',\'5354\',\'5356\',\'5360\',\'5362\',\'5363\',\'5364\',\'5365\',\'5366\',\'5369\',\'5377\',\'5379\',\'5380\',\'5381\',\'5382\',\'5396\',\'5401\',\'5402\',\'5420\',\'5428\',\'5442\',\'5495\',\'5537\',\'5571\',\'5572\',\'5587\',\'5588\',\'5589\',\'5592\',\'5601\',\'5612\',\'5615\',\'5616\',\'5618\',\'5623\',\'5628\',\'5648\',\'5649\',\'5656\',\'5659\',\'5711\')',
            # these took part before 2017, i.e. with paper diary
            '18Jan10': 'idContact IN (\'5124\',\'5126\',\'5127\',\'5129\',\'5130\',\'5138\',\'5139\',\'5145\',\'5147\',\'5155\',\'5156\',\'5157\',\'5159\',\'5167\',\'5168\',\'5170\',\'5175\',\'5176\',\'5177\',\'5178\',\'5180\',\'5181\',\'5182\',\'5187\',\'5188\',\'5189\',\'5190\',\'5192\',\'5193\',\'5194\',\'5199\',\'5202\',\'5203\',\'5204\',\'5205\',\'5209\',\'5210\',\'5212\',\'5216\',\'5217\',\'5219\',\'5220\',\'5221\',\'5222\',\'5223\',\'5224\',\'5228\',\'5231\',\'5233\',\'5236\',\'5237\',\'5238\',\'5239\',\'5240\',\'5241\',\'5242\',\'5243\',\'5244\',\'5256\',\'5264\',\'5268\',\'5276\',\'5280\',\'5281\',\'5282\',\'5286\',\'5287\',\'5290\',\'5291\',\'5292\',\'5294\',\'5295\',\'5302\',\'5304\',\'5306\',\'5308\',\'5314\',\'5315\',\'5316\',\'5326\',\'5329\',\'5331\',\'5333\',\'5335\',\'5336\',\'5339\',\'5345\',\'5352\',\'5353\',\'5355\',\'5367\',\'5371\',\'5372\',\'5529\')',
            # Households who did not confirm between jan and mar 2018
                '18Mar6': 'idHousehold IN (\'8741\',\'8781\',\'8839\',\'8844\',\'8845\',\'8855\',\'8858\',\'8864\',\'8865\',\'8927\',\'8930\',\'9171\',\'9183\',\'9187\',\'9205\',\'9229\',\'9344\',\'9347\')',

            # Household ID for Contacts where max status is 3 (i.e. never got beyond confirm)
                    '18Mar28': 'idHousehold IN (\'8041\',\'8049\',\'8074\',\'8107\',\'8183\',\'8332\',\'8541\',\'8839\',\'8066\',\'8086\',\'8148\',\'8203\',\'8865\',\'9205\',\'8186\',\'8845\',\'8927\',\'8011\',\'8028\',\'8044\',\'8060\',\'8068\',\'8078\',\'8101\',\'8120\',\'8187\',\'8205\',\'9380\',\'8102\',\'8121\',\'8132\',\'8141\',\'8271\',\'8557\',\'8030\',\'8103\',\'8178\',\'8409\',\'8855\',\'8930\',\'9578\',\'7985\',\'8063\',\'8145\',\'8170\',\'8499\',\'8577\',\'8781\',\'9183\',\'9383\',\'8116\',\'8578\',\'8858\')'
        # 'xMas':   'Household.status > 1 AND Contact.status <> "unsubscribed" page_number > 0 AND email <> \'%@%\'',
        # 'xxx':     'Contact.status = \'test1\''
        }
table = tables[0]
subsection = subsections[table][2]
emailFilePath = emailPath + "email_many.html"
# attachment = '/Users/phil/Documents/Oxford/OxfordEnergy/17_06_ChatthamHouse_Transport/InvitesR4/Invitation_University_of_Oxford_201732[id].pdf'
# attachment = '/Users/phil/Documents/Oxford/OxfordEnergy/17_06_ChatthamHouse_Transport/Details_of_Transport_meeting.pdf'
attachment = ''

dateTimeToday = datetime.datetime.now()
str_date = dateTimeToday.strftime("%Y-%m-%d")

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

def editMessage():
    # compose message
    # emailFilePath = emailPath + "email_many.html"
    call('vim ' + emailFilePath, shell=True)

def sendTo(condition,attach):
    # compose message
    # emailRCFilePath = emailPath + ".emailrc"
    # account = emailFilePath + "phil"
    account = emailFilePath + "infoEnergy"
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
    idField = "id%s" % table
    for result in results:
        emailText = templateText.replace("[name]", "%s" % result["Name"])
        if ("idHH" in result):
            emailText = emailText.replace("[householdID]", "%s" % result["idHH"])
        if ("sc" in result):
            emailText = emailText.replace("[securityCode]", "%s" % result["sc"])
        emailText = emailText.replace("[id]", "%s" % result[idField])
        thisAttach = attach.replace("[id]", "%s" % result[idField])

        emailAddress = "%s" % result["email"]
        emailFile = open(emailPathPersonal, "w+")
        emailFile.write(emailText)
        emailFile.close()
        call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + thisAttach + ' < ' + emailPathPersonal, shell=True)
        # call('mutt -F "'+account+'" -e "set content_type=text/html" -s "' + subjectLine + '" ' + emailAddress + thisAttach + ' < ' + emailPathPersonal, shell=True)


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
    cursor = connectDatabase("energy-use.org")

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
        MenuText.append("Database: " + getHost())
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
