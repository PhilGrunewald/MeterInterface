#!/usr/bin/python
# revision history
# 22 May 15:	PG added print by date

import os
import csv
import MySQLdb
import datetime			# needed to read TIME from SQL

from subprocess import call
import subprocess
from sys import stdin
import glob # for reading files in directory
from xml.etree import ElementTree as et # to modify the sting xml file for android
import npyscreen


filePath='/Users/pg1008/Documents/Data/METER/'

dbHost = 'localhost'
dbUser = 'root'
dbName = 'Meter'

dbHostCEGADS = '109.74.196.205'
dbUserCEGADS = 'phil'
dbPassCEGADS = 'SSartori12'
dbNameCEGADS = 'EnergyLocal'

contactID = '78'
dataType = 'E'
dateSelection = '2015-02-27'


dbConnection = MySQLdb.connect(host= dbHost, user= dbUser, db=dbName)
dbConnectionCEGADS = MySQLdb.connect(host= dbHostCEGADS, user= dbUserCEGADS,passwd=dbPassCEGADS, db=dbNameCEGADS)

CEGADSdb = dbConnectionCEGADS.cursor()
cursor = dbConnection.cursor()

def getMetaData(MetaFile, ItemName):
	# extract content from meta file (or any other file)
	content = ""
	for line in open(MetaFile):
		if ItemName in line:
			content = line.split(ItemName + ": ",1)[1] 
	return content.strip()

def backup_database():
	call('mysqldump -u ' + dbUser + ' --databases ' + dbName +' > ~/Documents/Data/SQL/'+dbName+'.sql', shell=True)

def data_plot():
	# get readings for a given contact and data type
	global contactID
	global dataType
	global filePath
	gnuPath = filePath + 'plots/'
	gnufile_E	 = '/Users/pg1008/Documents/Software/gnuplot/meter_E.gp'
	gnufile_E_PV = '/Users/pg1008/Documents/Software/gnuplot/meter_E_PV.gp'

	sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID + "'"
	cursor.execute(sqlq)
	householdID = ("%s" % cursor.fetchone())

	sqlq = "SELECT idMeta FROM Meta WHERE Household_idHousehold = '" + str(householdID) +"' AND DataType = '" + dataType +"'"
	cursor.execute(sqlq)
	###metaID = ("%s" % cursor.fetchone())
	metaIDall = cursor.fetchall()

	for collectionItem in metaIDall:
		metaID = "%s" % (collectionItem)


		# sqlq = "SELECT CollectionDate FROM Meta WHERE Household_idHousehold = '" + str(householdID) +"' AND DataType = '" + dataType +"'"
		# above seemed daft way to do it, since we have the metaID
		sqlq = "SELECT CollectionDate FROM Meta WHERE idMeta = '" + metaID + "'"
		cursor.execute(sqlq)
		# CollectionDate = ("%s" % cursor.fetchone())
		CollectionDateAll = ("%s" % cursor.fetchall())

		for collectionItem in CollectionDateAll:
			CollectionDate = "%s" % (collectionItem)  # this way we end up with the latest (right?)

		# Check if this is 'E', weather there are other records for this day
		### XXX add "if dataType=E"
		sqlq = "SELECT idMeta FROM Meta WHERE Household_idHousehold = '" + str(householdID) +"' AND DataType = 'PV' AND CollectionDate = '"+ CollectionDate +"'"
		cursor.execute(sqlq)
		# XXX ERROR HERE !!! not piccking up PV....
		result = cursor.fetchone()

		if result is None:					# there is no PV -> just do this record
			# Write data to temp file
			sqlq = "SELECT Time,Watt FROM Electricity WHERE Meta_idMeta = " + str(metaID) 
			cursor.execute(sqlq)
			data = cursor.fetchall()
			data_file = open(gnuPath + "temp_data.csv", "w+")
			data_file.write("Time, Electricity\n")
			for row in data:
				data_file.write("%s,%s\n" % (row[0], row[1]))
			data_file.close()
			gnufile=gnufile_E
		else:											# there is PV - include it in the 3rd column
			metaID2 = ("%s" % result)
			sqlq = """SELECT a.Time,a.Watt as a_watt,b.Watt as b_watt FROM
				(SELECT Watt, Time FROM Electricity where Electricity.Meta_idMeta = """ + str(metaID) + """) a
				LEFT JOIN (SELECT Watt, Time FROM Electricity where Electricity.Meta_idMeta = """ + str(metaID2)+ """) b
				ON a.Time = b.Time"""
			cursor.execute(sqlq)
			data = cursor.fetchall()
			data_file = open(gnuPath + "temp_data.csv", "w+")
			data_file.write("Time, Electricity, PV\n")
			for row in data:
				data_file.write("%s,%s,%s\n" % (row[0], row[1], row[2]))
			data_file.close()
			gnufile=gnufile_E_PV

		gnucommand ='gnuplot -e \'filename="' + gnuPath + 'temp_data.csv"; filenameonly="' + gnuPath + CollectionDate + '_' + contactID + '"; \' ' + gnufile
		call(gnucommand, shell=True)

def data_download():
	# pull files from phone
	call('adb pull /sdcard/METER/ ~/Documents/Data/METER/', shell=True)
	cmd = 'adb shell ls /sdcard/Meter/'
	s = subprocess.check_output(cmd.split())
	call('adb shell rm -rf /sdcard/Meter/*.csv', shell=True)
	call('adb shell rm -rf /sdcard/Meter/*.meta', shell=True)

def data_upload():
	# set up file names
	global filePath
	ArchivePath='/Users/pg1008/Documents/Data/METER_Archive/'
	allMetafiles= filePath + '*.meta'
	#print glob.glob(allMetafiles)
	fileList = glob.glob(allMetafiles)
	# XXX do as list iteration...
	MetaFile = fileList[0]
	DataFile, void = MetaFile.split('.meta')
	DataFile = DataFile + '.csv'
	#print DataFile 
	#print MetaFile

	# read Meta file information
	#---------------------------
	if os.path.exists(MetaFile):
		deviceSN = getMetaData(MetaFile, "Device ID")
		contactID = getMetaData(MetaFile, "Contact ID")
		dataType = getMetaData(MetaFile, "Data type")
		offset = getMetaData(MetaFile, "Offset")
		collectionDate = getMetaData(MetaFile, "Date")
	
	############### CONTACT CHECK
	#-----------------------------
	# does the contact specified in the meta file exist?
	sqlq = "SELECT idContact FROM Contact WHERE idContact = '" + contactID +"'"
	global	cursor
	cursor.execute(sqlq)
	if cursor.fetchone():
		npyscreen.notify_confirm('Now processing data for contact ' + contactID)
	else:
		npyscreen.notify_confirm('Creating new contact for unknown contact!')
		sqlq = "INSERT INTO Contact(idContact) VALUES ('"+contactID+"')"
		cursor.execute(sqlq)
		dbConnection.commit()
	
	############### HOUSEHOLD CHECK
	#-----------------------------
	# does a household record for this contact exist yet?
	sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID +"'"
	cursor.execute(sqlq)
	if cursor.fetchone():
		householdID = cursor.fetchone()
		#print 'Now processing data for household' + householdID
	else:
		#print 'Creating new household entry for contact ' + contactID
		# Create a placeholder household (details can be populated when processing the relevant meta file
		sqlq = "INSERT INTO Household(Contact_idContact, HouseType_idHouseType, HeatingSystem_idHeatingSystem, BillingType_idBillingType) VALUES ('" + contactID +"', '1','1','1')"
		# XXX the above '1's are placeholders for unknown foreign keys!!
		cursor.execute(sqlq)
		householdID = cursor.lastrowid
	
	############### META CHECK
	#-----------------------------
	# does a meta record for this data and this household exist yet?
	sqlq = "SELECT idMeta FROM Meta WHERE (SerialNumber = '" + deviceSN + "' AND CollectionDate = '" + collectionDate + "' AND Household_idHousehold = '"+ str(householdID) +"')"
	cursor.execute(sqlq)
	if cursor.fetchone():
		#print 'These data were already imported'
		MetaID = cursor.fetchone()
	else:
		# create a new meta entry
		sqlq = "INSERT INTO meta(CollectionDate , DataType , SerialNumber , Household_idHousehold) VALUES ('" + collectionDate + "', '" + dataType + "', '" + deviceSN + "', '"+ str(householdID) +"');"
		cursor.execute(sqlq)
		# get the id of the entry just made
		MetaID = cursor.lastrowid
		# insert electricity DataFile into database
		csv_data = csv.reader(file(DataFile))
		for row in csv_data:
			sqlq = "INSERT INTO Electricity(Time, Watt, Meta_idMeta ) VALUES('" + row[0] + "', '" + row[1] + "', '"+ str(MetaID) +"')"
			cursor.execute(sqlq)
		dbConnection.commit()
		upload_10min_readings(MetaID)
	
	#close the connection to the database.
	#-------------------------------------
	dbConnection.commit()
	#cursor.close()
	cmd_moveToArchive='mv ' + DataFile + ' ' + ArchivePath
	call(cmd_moveToArchive , shell=True)
	cmd_moveToArchive='mv ' + MetaFile + ' ' + ArchivePath
	call(cmd_moveToArchive , shell=True)


def get_time_period(timestr):
	# convert into one of 144 10minute periods of the day
	factors = [6,0.1,0.00167]
	return sum([a*b for a,b in zip(factors, map(int,timestr.split(':')))])

def time_in_seconds(timestr):
	# '00:01:01' -> 61
	factors = [3600,60,1]
	return sum([a*b for a,b in zip(factors, map(int,timestr.split(':')))])

def upload_10min_readings(idMeta=20):
	sqlq = "SELECT Time,Watt FROM Electricity WHERE Meta_idMeta = '" + str(idMeta) +"' ORDER BY Time"
	cursor.execute(sqlq)
	eReadings = cursor.fetchall()

	period = 1
	thisPeriodSum = 0
	thisPeriodCounter = 1

	for thisLine in eReadings:
		if get_time_period("%s" % (thisLine[0])) < period:
			thisPeriodSum = thisPeriodSum + float(thisLine[1])
			thisPeriodCounter += 1
		else:															# entered the next period -> write average of last period and reset
			if (thisPeriodCounter == 1):		# if no readings, set value to -1 as error flag
				thisPeriodSum = -1
			sqlq = "INSERT INTO Electricity_periods(Period,Watt,Meta_idMeta) VALUES ('" + str(period) + "', '" + str(thisPeriodSum/thisPeriodCounter)+ "', '"+str(idMeta)+"')"
			cursor.execute(sqlq)
			period += 1
			thisPeriodSum = float(thisLine[1])
			thisPeriodCounter = 1
	# one more time at the end to make sure we get the last period as well
	if (thisPeriodCounter == 1):		# if no readings, set value to -1 as error flag
		thisPeriodSum = -1
	sqlq = "INSERT INTO Electricity_periods(Period,Watt,Meta_idMeta) VALUES ('" + str(period) + "', '" + str(thisPeriodSum/thisPeriodCounter)+ "', '"+str(idMeta)+"')"
	cursor.execute(sqlq)


def uploadFile(fileName):  ## SUPERSEEDED???
	# set up file names
	filePath='/Users/pg1008/Documents/Data/METER/'
	ArchivePath='/Users/pg1008/Documents/Data/METER_Archive/'

	MetaFile = fileName + '.meta'
	DataFile = fileName + '.csv'

	# read Meta file information
	#---------------------------
	if os.path.exists(MetaFile):
		deviceSN = getMetaData(MetaFile, "Device ID")
		contactID = getMetaData(MetaFile, "Contact ID")
		dataType = getMetaData(MetaFile, "Data type")
		offset = getMetaData(MetaFile, "Offset")
		collectionDate = getMetaData(MetaFile, "Date")
	
	############### CONTACT CHECK
	#-----------------------------
	# does the contact specified in the meta file exist?
	sqlq = "SELECT idContact FROM Contact WHERE idContact = '" + contactID +"'"
	global	cursor
	cursor.execute(sqlq)
	if cursor.fetchone():
		npyscreen.notify_confirm('Now processing data for contact ' + contactID)
	else:
		npyscreen.notify_confirm('Creating new contact for unknown contact!')
		sqlq = "INSERT INTO Contact(idContact) VALUES ('"+contactID+"')"
		cursor.execute(sqlq)
		dbConnection.commit()
	
	############### HOUSEHOLD CHECK
	#-----------------------------
	# does a household record for this contact exist yet?
	sqlq = "SELECT idHousehold FROM Household WHERE Contact_idContact = '" + contactID +"'"
	cursor.execute(sqlq)

	householdID = cursor.fetchone()
	if householdID is None:
		# Create a placeholder household (details can be populated when processing the relevant meta file
		sqlq = "INSERT INTO Household(Contact_idContact, HouseType_idHouseType, HeatingSystem_idHeatingSystem, BillingType_idBillingType) VALUES ('" + contactID +"', '1','1','1')"
		# XXX the above '1's are placeholders for unknown foreign keys!!
		cursor.execute(sqlq)
		householdID = cursor.lastrowid
	else:
		householdID = ("%s" % householdID)			# introduced for when HH DOES exist and is a tuple, not an integer


	############### META CHECK
	#-----------------------------
	# does a meta record for this data and this household exist yet?
	sqlq = "SELECT idMeta FROM Meta WHERE (SerialNumber = '" + deviceSN + "' AND CollectionDate = '" + collectionDate + "' AND Household_idHousehold = '"+ str(householdID) +"')"
	cursor.execute(sqlq)
	MetaID = cursor.fetchone()

	if MetaID is None:
		# create a new meta entry
		sqlq = "INSERT INTO meta(CollectionDate , DataType , SerialNumber , Household_idHousehold) VALUES ('" + collectionDate + "', '" + dataType + "', '" + deviceSN + "', '"+ str(int(householdID)) +"');" # WATCH THIS: removed [0] from householdID (this was to make a case work where the household was newly created!	
		#	the str(int(x[0]) term is to turn the tuple of a 'long integer' i.e. '123L,' in to a simple integer and then string

		cursor.execute(sqlq)
		# XXX add DataType PV/E/TU...
		# get the id of the entry just made
		MetaID = cursor.lastrowid
		#print 'Created meta entry number' + str(MetaID)
		####################### Enter data
		# insert electricity DataFile into database
		csv_data = csv.reader(file(DataFile))
		for row in csv_data:
			sqlq = "INSERT INTO Electricity(Time, Watt, Meta_idMeta ) VALUES('" + row[0] + "', '" + row[1] + "', '"+ str(MetaID) +"')"
			cursor.execute(sqlq)
	
	#close the connection to the database.
	#-------------------------------------
	dbConnection.commit()
	#cursor.close()
	cmd_moveToArchive='mv ' + DataFile + ' ' + ArchivePath
	call(cmd_moveToArchive , shell=True)
	cmd_moveToArchive='mv ' + MetaFile + ' ' + ArchivePath
	call(cmd_moveToArchive , shell=True)

def data_download_upload(self):
	data_download()
	data_upload()

def phone_setup():
	# collect the contact ID and sensor type and write complied data to phone
	#print "\n[+] Please enter Contact ID:" 
	#contactID = '78' #stdin.readline()
	#print "\n[+] Please select data type: [E]lectricity, [P]V, [T]ime-use" 
	#dataType = 'E' #stdin.readline()


	# set up device
	xmlFile = '/Users/pg1008/Documents/Software/Android/DMon/res/values/strings.xml'
	tree = et.parse(xmlFile)
	root = tree.getroot()
	for rank in root.iter('string'):
		if rank.attrib['name'] == 'contactID':
			rank.text = contactID
		if rank.attrib['name'] == 'dataType':
			rank.text = dataType
	tree.write(xmlFile)
	call('ant debug -f ~/Documents/Software/Android/DMon/build.xml', shell=True)
	call('adb uninstall com.Phil.DEMon', shell=True)
	call('adb install ~/Documents/Software/Android/DMon/bin/MainActivity-debug.apk', shell=True)
	call('adb install ~/Documents/Software/Android/AutoStart_2.1.apk', shell=True)

def email_graph():
	# attach graph to a personalised email
	plotFile = filePath + "plots/" + dateSelection + "_" + contactID + ".pdf"
	if os.path.exists(plotFile):
		sqlq = "SELECT Name,Email FROM Contact WHERE idContact = '" + contactID +"'"
		CEGADSdb.execute(sqlq)
		result = CEGADSdb.fetchone()
		thisName=("%s" % (result[0]))
		thisEmail=("%s" % (result[1]))
		dateArray = dateSelection.split('-')
		thisDate = ("%s " "%s " "%s" % (dateArray[2],dateArray[1],dateArray[0]))

		emailPath = filePath + "emails/"
		templateFile = open(emailPath + "emailTemplate.md", "r")
		templateText = templateFile.read()
		templateFile.close()

		templateText=templateText.replace("[name]", thisName)
		templateText=templateText.replace("[date]", thisDate)

		emailFilePath = emailPath + "tempEmail.mail"
		emailFile = open(emailFilePath, "w+")
		emailFile.write(templateText)
		emailFile.close()

		call('mutt -s "SWELL: Your electricity profile from ' + thisDate + '" ' + thisEmail + ' -a '+ plotFile +' < ' + emailFilePath, shell=True)
		#call('mutt -s "SWELL: Your electricity profile from ' + thisDate + '" ' + thisEmail + ' energy@WeSET.org -a '+ plotFile +' < ' + emailFilePath)
	else:
		npyscreen.notify_confirm('Please create a graph for contact ' + contactID + ' first')


def print_address_label(void):
	# produces postage label and personal letter
	sqlq = "SELECT Name,Address,Postcode,Town FROM Contact WHERE idContact = '" + contactID +"'"
	CEGADSdb.execute(sqlq)
	result = CEGADSdb.fetchone()
	#addressDetails = ""
	#for item in result:
	#	addressDetails += "%s \n\n" % (item)
	addressDetails = "**To:** \n\n \ \ \ **%s**\n\n \ \ \ **%s**\n\n \ \ \ **%s %s**" % (result)
	addressBlock = "\ \n\n %s\n\n %s\n\n%s %s" % (result)

	returnAddress = "_Please return for free to_ \n\n\ \n\n \ \ \ Dr Philipp Grunewald \n\n \ \ \ University of Oxford \n\n \ \ \ OUCE, South Parks Road \n\n \ \ \ **OX1 3QY** Oxford\n\n\ "
	fromAddress = "\n\n\ \n\n _Dr Grunewald, University of Oxford, OX1 3QY Oxford_	\n\n"
	fromLetter = "\n\n\ \n\n _Dr Philipp Grunewald, Deputy Director of Energy Research, University of Oxford_\n\n _01865 275864, philipp.grunewald@ouce.ox.ac.uk_\n\n"
	letterPath = filePath + "letters/"
	myFile = open(letterPath + "address.md", "a")
	myFile.write(fromAddress)
	myFile.write(addressDetails)
	myFile.write("\n\n\ \n\n\ \n\n\ ")
	myFile.write("\n\n\ \n\n\ \n\n\ \n\n\ \n")
	myFile.write(returnAddress)
	myFile.write("\n\n\ \n\n\ \n\n")
	myFile.close()
	call('pandoc -V geometry:margin=0.5in ' + letterPath + "address.md -o" + letterPath + "address.pdf ", shell= True)

	# The letter
	thisName=("%s" % (result[0]))
	letterFile=letterPath + contactID + "_letter."
	letterTemplate= letterPath + "letter.md"
	templateFile = open(letterTemplate, "r")
	templateText = templateFile.read()
	templateFile.close()
	templateText=templateText.replace("[date]", "**Monday**, 4 May")
	if (dataType=='PV'):
		templateText=templateText.replace("[s]", "s")
		templateText=templateText.replace("[is are]", "are")
		templateText=templateText.replace("[This These]", "These")
		templateText=templateText.replace("[it them]", "them")
		templateText=templateText.replace("[PV]", " and a separate recorder for your PV system")
	else:
		templateText=templateText.replace("[s]", "")
		templateText=templateText.replace("[is are]", "is")
		templateText=templateText.replace("[This These]", "This")
		templateText=templateText.replace("[it them]", "it")
		templateText=templateText.replace("[PV]", "")


	myFile = open(filePath + "temp_letter.md", "w+")
	myFile.write("\pagenumbering{gobble}")
	myFile.write(fromLetter)
	myFile.write(addressBlock)
	myFile.write("\n\n\ \n\n\ \n\n Dear " + thisName +",\n\n")
	myFile.write("\n\n\ \n\n **Subject: Energy Local Electricity Recorder for Monday, 4 May 2015**\n\n\ \n\n")
	myFile.write(templateText)
	myFile.write("\n\n\ \n\n\ \n\n")
	myFile.close()
	call('pandoc -V geometry:margin=1.2in ' + filePath + "temp_letter.md -o" + letterFile + "pdf ", shell= True)

	
#-------------------------------------------------------------------------------
#---------------------------FORMS-----------------------------------------------
#-------------------------------------------------------------------------------

class ActionControllerData(npyscreen.MultiLineAction):

	def __init__(self, *args, **keywords):
		super(ActionControllerData, self).__init__(*args, **keywords)
		global MenuActionKeys
		MenuActionKeys = {
			'1' : self.phone_setup,
			'p' : self.phone_setup,
			'A' : print_address_label,
			'd' : self.data_download,
		 	"u" : self.data_upload,
		 	"D" : data_download_upload,

		 	"t" : self.show_DataTypes,
		 	"c" : self.show_Contact,
		 	"a" : self.show_NewContact,
			'T' : self.show_Tables,

		 	"m" : self.show_MetaForm,
		 	"g" : self.show_Plot,
		 	"e" : email_graph,

		 	"B" : self.backup_database,
		 	"s" : self.show_MainMenu,

		 	"M" : self.show_MainMenu,
		 	"X" : self.parent.exit_application,
		}
		self.add_handlers(MenuActionKeys)

	
	def actionHighlighted(self, selectedLine, keypress):
		#choose action based on the display status and selected line
		if (self.parent.myStatus == 'Main'):
			self.parent.wMain.values = ['Selection: ', selectedLine, '\tM\t\t to return to the main menu']
			self.parent.wMain.display()
			global MenuActionKeys
			MenuActionKeys[selectedLine[1]]()

		elif (self.parent.myStatus == 'Contact'):
			global contactID
			dataArray=selectedLine.split(',')
			contactID = str(dataArray[0])
			self.parent.wStatus2.value = "Contact changed to " + str(dataArray[1])
			self.parent.wStatus2.display()
			self.parent.setMainMenu()
		elif (self.parent.myStatus == 'Tables'):
			self.parent.wMain.values = ['Table ', selectedLine, 'was selected!']
			self.parent.wMain.display()
			self.parent.display_selected_data(selectedLine)
		elif (self.parent.myStatus == 'DataTypes'):
			global dataType
			dataTypeArray=selectedLine.split(',')
			dataType = str(dataTypeArray[0])
			self.parent.wStatus2.value = "Data type changed to " + str(dataTypeArray[1])
			self.parent.wStatus2.display()
			self.parent.setMainMenu()

	def backup_database(self, *args, **keywords):
		self.parent.myStatus='Backing up...'
		backup_database()

	def phone_setup(self, *args, **keywords):
		phone_setup()

	def show_Tables(self, *args, **keywords):
		self.parent.myStatus='Tables'
		self.parent.display_tables()

	def show_MainMenu(self, *args, **keywords):
		self.parent.setMainMenu()

	def data_download(self, *args, **keywords):
		data_download()

	def data_upload(self, *args, **keywords):
		data_upload()

	def show_DataTypes(self, *args, **keywords):
		self.parent.myStatus='DataTypes'
		self.parent.display_selected_data("DataTypes")

	def show_Contact(self, *args, **keywords):
		self.parent.myStatus='Contact'
		self.parent.display_selected_data("Contact")

	def show_MetaForm(self, *args, **keywords):
		self.parent.parentApp.switchForm('MetaForm')

	def show_NewContact(self, *args, **keywords):
		self.parent.parentApp.switchForm('NewContact')

	def show_Plot(self, *args, **keywords):
		self.parent.myStatus='Plotting'
		data_plot()


	def formated_data_type(self, vl):
		return "%s (%s)" % (vl[1], str(vl[0]))

	def formated_contact(self, vl):
		return "%s %s, %s" % (vl[1], vl[2], str(vl[0]))

	def formated_word(self, vl):
		return "%s" % (vl[0])
	
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


class MeterMain(npyscreen.FormMuttActiveTraditionalWithMenus):
	ACTION_CONTROLLER = ActionControllerSearch
	MAIN_WIDGET_CLASS = ActionControllerData
	first_time = True
	myStatus="Main"

	def getMenuText(self):
		MenuText=[]
		#CommandNumber=0
		for line in open("/Users/pg1008/Documents/Software/Android/MainMenu.txt", "r"):
			#if (line[0] == "#"):
			#	MenuText.append("\t" + str(CommandNumber) + ".\t" + line[1:])
			#	CommandNumber+=1
			#else:
			MenuText.append("\t" + line)
		MenuText.append("\n")
		MenuText.append("\n")
		MenuText.append("Contact:  \t" + str(contactID))
		MenuText.append("Data type:\t" + str(dataType))
		MenuText.append("Date:\t" + str(dateSelection))

		return MenuText

	def setMainMenu(self):
		mainScreenText=self.getMenuText()
		self.myStatus='Main'
		self.value.set_values(mainScreenText)
		self.wMain.values = mainScreenText
		self.wMain.display()

	def beforeEditing(self):
		mainScreenText=self.getMenuText()
		self.value.set_values(mainScreenText)
		self.update_list()
		if self.first_time:
			self.initialise()
			self.first_time = False
	
	def initialise(self):
		global dataType
				#self.m1 = self.add_menu(name="Data handling", shortcut="D")
				#self.m1.addItemsFromList([
				#	("Download from phone",	data_download, "d"),
				#	("Upload to database",	data_upload, "u"),
				#	("Download and upload",	data_download_upload, "D"),
				#])
				## The menus are created here.
				#self.m2 = self.add_menu(name="Phone setup", shortcut="p")
				#self.m2.addItemsFromList([
				#	("Set up new phone", phone_setup, "p"),
				#	("Set sensor type (currently " + str(dataType) +")", self.change_data_type, "s"),
				#])
			
				#self.m2 = self.add_menu(name="Database management", shortcut="m")
				#self.m2.addItemsFromList([
				#	("Add new contact", self.add_contact, "p"),
				#	("Display table",	self.display_data, "s"),
				#	#("Display Contact",   self.display_table_data, "c"),
				#	("Display Contact",   self.XXdisplay_selected_data, "c"),
				#	("Backup database",   backup_database, "c"),
				#])
				#self.m3 = self.add_menu(name="Exit", shortcut="X")
				#self.m3.addItem(text="Exit", onSelect = self.exit_application)

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
		self.wStatus2.value = "Command line"
		#self.wMain.add(npyscreen.TitleText, name = "Entrypoint")
		self.wMain.values = self.value.get()

	def display_selected_data(self,displayModus):
		# pull SQL data and display 
		self.myStatus=displayModus
		self.wStatus1.value = "METER " + self.myStatus + " selection"
		self.wStatus2.value = "Select " + self.myStatus + " from selection"
		if (displayModus == "Contact"):
			sqlq = "SELECT * FROM Contact"
			CEGADSdb.execute(sqlq)
			result = CEGADSdb.fetchall()
		else:
			sqlq = "SELECT * FROM " + self.myStatus
			cursor.execute(sqlq)
			result = cursor.fetchall()
		displayList=[]
		if (displayModus == "Contact"):
			for items in result:
				displayList.append(self.formated_contact(items))
		elif (displayModus == "DataTypes"):
			for items in result:
				displayList.append(self.formated_two(items))
		else:
			for items in result:
				displayList.append(self.formated_any(items))

		self.value.set_values(displayList)
		self.wMain.values = self.value.get()  # XXX testj 
		self.wMain.display()

	def formated_contact(self, vl):
		return "%s, %s %s" % (vl[0],vl[1],vl[2])

	def formated_any(self, tupelItems):
		returnString = ""
		for item in tupelItems:
			returnString += "%s \t\t" % (item)
		return returnString

	def formated_two(self, vl):
		return "%s, %s" % (vl[0],vl[1])

	def display_tables(self):
		self.myStatus='Tables'
		self.wStatus1.value = "METER " + self.myStatus 
		#sqlq = "SELECT * FROM Contact"
		sqlq = "SHOW TABLES"
		cursor.execute(sqlq)
		result = cursor.fetchall()
		displayList=[]
		for items in result:
			displayList.append(self.formated_any(items))
		
		# self.wMain.values = displayList
		self.value.set_values(displayList)
		self.wMain.values = self.value.get()  # XXX testj 
		self.wMain.display()
		#self.wMain.values = self.formated_word(result)
		# return result

	def exit_application(self, command_line=None, widget_proxy=None, live=None):
		global cursor
		cursor.close()
		self.parentApp.setNextForm(None)
		self.editing = False
		self.parentApp.switchFormNow()

class newContactForm(npyscreen.Form):
	#gets fields from database, collects new entries
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
			self.ColumnEntry.append(self.add(npyscreen.TitleText, name = self.ColumnName[item]))
		# self.ColumnName.pop(0)   # to leave out the ID column
		#cursor.close()

	def afterEditing(self):
		# combine all column names into comma separated string with ``
		sqlColumnString = "`"+self.ColumnName[0]+"`"
		for item in self.ColumnName[1:]:
			sqlColumnString = sqlColumnString + (",`"+item+"`")

		sqlEntryString = "'"+self.ColumnEntry[0].value+"'"
		for item in self.ColumnEntry[1:]:
			sqlEntryString = sqlEntryString + (",'"+item.value+"'")

		sqlq = "INSERT INTO `Contact`(" + sqlColumnString + ") VALUES ("+sqlEntryString+")"
		global cursor
		cursor.execute(sqlq)
		dbConnection.commit()
		self.parentApp.setNextFormPrevious()

class metaFileInformation(npyscreen.Form):
	# display all .meta files in /METER/
	fileList=[]
	reject_fileList=[]

	def afterEditing(self):
		for FileIndex in self.FileSelection.value:
			uploadFile(self.fileList[FileIndex])

		for FileIndex in self.FileRejection.value:
			call('mv ' + self.reject_fileList[FileIndex] + '.meta ~/.Trash/', shell=True)
			call('mv ' + self.reject_fileList[FileIndex] + '.csv ~/.Trash/', shell=True)

		self.parentApp.setNextFormPrevious()

	def create(self):
		# set up file names
		filePath='/Users/pg1008/Documents/Data/METER/'
		allMetafiles= filePath + '*.meta'
		allCSVfiles= filePath + '*.csv'
		#self.fileList = glob.glob(allMetafiles)
		CSVfileList = glob.glob(allCSVfiles)

		selectIndex=[]
		selectCounter=0
		contactID=[]
		collectionDate=[]
		dataType=[]
		duration=[]
		displayString=[]

		reject_Index=[]
		reject_Counter=0
		reject_contactID=[]
		reject_collectionDate=[]
		reject_dataType=[]
		reject_duration=[]
		reject_displayString=[]

		for DataFile in CSVfileList:
			recordsInFile = sum(1 for line in open(DataFile))
			thisFileName= DataFile.split('.csv')[0]
			if (recordsInFile > 80000):									# only full 24 hour recordings are of interest (that would be 86400 seconds)
				selectIndex.append(selectCounter)
				self.fileList.append(thisFileName)
				contactID.append(getMetaData(thisFileName+'.meta', "Contact ID"))
				collectionDate.append(getMetaData(thisFileName+'.meta', "Date"))
				dataType.append(getMetaData(thisFileName+'.meta', "Data type"))
				duration.append(round(recordsInFile / 3600.0,2))
				displayString.append(str(selectCounter) +'. ID: ' + contactID[-1] + ' ' + dataType[-1] + ' on ' + collectionDate[-1] + ' for ' + str(duration[-1]) + ' hours')
				selectCounter+=1
			else:
				reject_Index.append(reject_Counter)
				self.reject_fileList.append(thisFileName)
				reject_contactID.append(getMetaData(thisFileName+'.meta', "Contact ID"))
				reject_collectionDate.append(getMetaData(thisFileName+'.meta', "Date"))
				reject_dataType.append(getMetaData(thisFileName+'.meta', "Data type"))
				reject_duration.append(round(recordsInFile / 3600.0,2))
				reject_displayString.append(str(reject_Counter) + '.\t ID: ' + reject_contactID[-1] + ' ' + reject_dataType[-1] + ' on ' + reject_collectionDate[-1] + ' for ' + str(reject_duration[-1]) + ' hours')
				reject_Counter+=1

		self.FileSelection	= self.add(npyscreen.TitleMultiSelect, max_height=9, value = selectIndex, name="Which files should be uploaded?", values = displayString, scroll_exit=True)
		self.FileRejection	= self.add(npyscreen.TitleMultiSelect, max_height=15, value = reject_Index, name="These files will be deleted (uncheck to save them)?", values = reject_displayString, scroll_exit=True)

		#self.MetaFileSelection	= self.add(npyscreen.TitleSelectOne, max_height=9, value = [0,], name="Pick Meta File", values = filePathNoExtension , scroll_exit=True)
		#self.SerialNuberSelection	= self.add(npyscreen.TitleSelectOne, max_height=9, value = [1,], name="Pick Device Serial Number", values = deviceSNs, scroll_exit=True)

class MeterForms(npyscreen.NPSAppManaged):
	def onStart(self):
		#npyscreen.setTheme(npyscreen.Themes.ColorfulTheme)
		self.addForm('MAIN', MeterMain, lines=36 )
		self.addForm('NewContact', newContactForm, name ='New Contact')
		self.addForm('MetaForm', metaFileInformation, name ='Meta Data')

if __name__ == "__main__":
	MeterApp = MeterForms()
	MeterApp.run()
	exit()

