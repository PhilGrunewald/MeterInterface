#!/usr/bin/python

import os,sys               # to get path
from subprocess import call
import datetime             # format date into string
import meter_db as mdb      # for sql queries

def sendEmail(householdID):
    """
    use mutt to send and email to a given HH
    """
    contactID = mdb.getContact(householdID)
    sqlq = """
            SELECT Name, Surname, Address1, Address2, Town, Postcode, email, status
            FROM Contact
            WHERE idContact = '{}';
            """.format(contactID)
    result = mdb.getSQL(sqlq)[0]

    # thisName    = ("%s %s" % (result['Name'], result['Surname']))
    thisName    = ("%s" % (result['Name']))
    thisAddress = ("%s</br>%s</br>%s %s" % (result['Address1'], result['Address2'], result['Town'], result['Postcode']))
    thisAddress = thisAddress.replace("None </br>", "")
    dtChoice    = mdb.getHHdtChoice(householdID)
    thisDate    = dtChoice.strftime("%a, %-d %b")
    thisEmail   = ("%s" % (result['email']))
    thisStatus   = ("%s" % (result['status']))
    thisAddress = thisAddress.replace("None</br>", "")
    participantCount = ("%s" % mdb.getParticipantCount(str(householdID)))
    # prepare the custom email

    thisPath = os.path.dirname(os.path.abspath(__file__))
    if (thisStatus == 'de'):
        emailPath = os.path.join(thisPath, "emails/email_confirm_de.html")
    else
        emailPath = os.path.join(thisPath, "emails/email_confirm.html")
    templateFile = open(emailPath, "r")
    templateText = templateFile.read()
    templateFile.close()
    templateText = templateText.replace("[householdID]", householdID)
    templateText = templateText.replace("[contactID]", contactID)
    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[address]", thisAddress)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[securityCode]", mdb.getSecurityCode(householdID))
    templateText = templateText.replace("[participantCount]", participantCount)

    # Subject
    subjectLine = templateText.splitlines()[0]
    templateText = templateText[templateText.find('\n') + 1:]     # find line break and return all from there - i.e. remove first line
    
    # email file
    emailFilePath = os.path.join(thisPath, "tempEmail.htmail")

    emailFile = open(emailFilePath, "w+")
    emailFile.write(templateText)
    emailFile.close()

    # call('mutt -e "set content_type=text/html" -s "[TESTING]' + subjectLine + '" philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath, shell=True)
    call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" ' + thisEmail + ' -b meter@energy.ox.ac.uk < ' + emailFilePath, shell=True)
    

def getUpcoming():
    """
    find participant due in the next two weeks and send them the confirmation email
    this is called every day at 10am
    """
    idHHs = mdb.getHH_to_confirm()
    for idHH in idHHs:
        HH = idHH['idHousehold']
        mdb.setStatus(HH,3) # 3 = awaiting confirmation
        sendEmail("{}".format(HH))
        print "sent confirmation request to HH {}".format(HH)

getUpcoming()
