#!/usr/bin/python
""" send emails to participants with their graph


WARNING: used on server!
Called from upload .. api/data_approved.php

"""

import os,sys               # to get path
from subprocess import call
import datetime             # format date into string
import meter_db as mdb      # for sql queries
import locale

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

    thisName    = ("%s" % (result['Name']))
    thisEmail   = ("%s" % (result['email']))
    thisStatus   = ("%s" % (result['status']))

    # prepare the custom email
    thisPath = os.path.dirname(os.path.abspath(__file__))
    if (thisStatus == 'de'):
        emailPath = os.path.join(thisPath, "emails/email_graph_de.html")
        locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
    else:
        emailPath = os.path.join(thisPath, "emails/email_graph.html")
    dtChoice    = mdb.getHHdtChoice(householdID)
    thisDate    = dtChoice.strftime("%A, %-d %B")

    templateFile = open(emailPath, "r")
    templateText = templateFile.read()
    templateFile.close()
    templateText = templateText.replace("[householdID]", householdID)
    templateText = templateText.replace("[contactID]", contactID)
    templateText = templateText.replace("[name]", thisName)
    templateText = templateText.replace("[date]", thisDate)
    templateText = templateText.replace("[securityCode]", mdb.getSecurityCode(householdID))

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
    

idHH = sys.argv[1]
sendEmail(idHH) 
mdb.setStatus(idHH,7) # 7 = sent graph
print "sent graph email to HH {}".format(idHH)
