#!/usr/bin/python

import sys
sys.path.append('../Analysis/res/')
from subprocess import call
import meter_db as mdb      # for sql queries
import meter_tools as mt    # for generic function

debug = True

def sendEmail(householdID):
    """
    use mutt to send and email to a given HH
    """
    contactID = mdb.getContact(householdID)
    print contactID
    sqlq = """
            SELECT Name, Surname, Address1, Address2, Town, Postcode, email
            FROM Contact
            WHERE idContact = '{}';
            """.format(contactID)
    result = mdb.getSQL(sqlq)[0]

    thisName    = ("%s %s" % (result['Name'], result['Surname']))
    thisAddress = ("%s</br>%s</br>%s %s" % (result['Address1'], result['Address2'], result['Town'], result['Postcode']))
    thisAddress = thisAddress.replace("None </br>", "")
    dtChoice    = mdb.getHHdtChoice(householdID)
    thisDate    = mt.getDateTimeFormatedText(dtChoice)
    thisEmail   = ("%s" % (result['email']))
    thisAddress = thisAddress.replace("None</br>", "")
    participantCount = ("%s" % mdb.getParticipantCount(str(householdID)))
    # prepare the custom email

    templateFile = open("./emails/email_confirm.html", "r")
    templateText = templateFile.read()
    templateFile.close()
    templateText = templateText.replace("[householdID]", householdID)
    templateText = templateText.replace("[contactID]", contactID)
    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[address]", thisAddress)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[securityCode]", mdb.getSecurityCode(householdID))
    templateText = templateText.replace("[participantCount]", participantCount)

    # email file
    emailFilePath = "./emails/tempEmail.htmail"
    emailFile = open(emailFilePath, "w+")
    emailFile.write(templateText)
    emailFile.close()

    # Subject
    subjectLine = templateText.splitlines()[0]
    templateText = templateText[templateText.find('\n') + 1:]     # find line break and return all from there - i.e. remove first line

    if debug:
        call('mutt -e "set content_type=text/html" -s "[TESTING]' + subjectLine + '" philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath, shell=True)
    else:
        call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + thisEmail + ' -b meter@energy.ox.ac.uk < ' + emailFilePath, shell=True)
    
    # Status
    # XXX updateHouseholdStatus(householdID, 3)

def getUpcoming():
    """
    find participant due in the next two weeks and send them the confirmation email
    this is called every day at 10am
    """
    idHHs = mdb.getUpcomingHH()
    for idHH in idHHs:
        sendEmail("{}".format(idHH['idHousehold']))

getUpcoming()
# sendEmail(str(2))
