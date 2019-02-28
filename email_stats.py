#!/usr/bin/python

import os
from subprocess import call
import meter_db as mdb      # for sql queries

def getCount(status, condition):
    sqlq = """
            SELECT COUNT(*) AS c
            FROM Household
            WHERE status = '{}'
            AND {}
            ;
            """.format(status, condition)
    return mdb.getSQL(sqlq)[0]['c']

def getGermans():
    sqlq = """
           SELECT idHousehold, date_choice, Name, Address1, Address2, Town, Postcode, email, phone, age_group2, age_group3, age_group4, age_group5, age_group6
             FROM Contact
             JOIN Household
             ON idContact = Contact_idContact
             WHERE Contact.status = 'de'
             AND Household.status = '1';
            """
    germans = mdb.getSQL(sqlq)
    # email file
    thisPath = os.path.dirname(os.path.abspath(__file__))
    emailFilePath = os.path.join(thisPath, "germansConfirmed.txt")
    f= open(emailFilePath,"w")
    for g in germans:
        people = int(g['age_group2']) +int(g['age_group3']) +int(g['age_group4']) +int(g['age_group5']) +int(g['age_group6'])
        f.write("HH: {} ({} recorders)\n{}\n{}\n{}\n{}\n{} {}\n{}\n---------------------\n\n".format(g['idHousehold'],people,g['date_choice'],g['Name'],g['Address1'],g['Address2'],g['Postcode'],g['Town'],g['email']))
        # print "HH: {} ({} recorders)\n{}\n{}\n{}\n{}\n{} {}\n{}\n---------------------\n".format(g['idHousehold'],people,g['date_choice'],g['Name'],g['Address1'],g['Address2'],g['Postcode'],g['Town'],g['email'])
    f.close

    # call('mutt -s "[Meter] 5 German pipeline" philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath, shell=True)
    print 'mutt -s "[Meter] 5 German pipeline" philipp.grunewald@ouce.ox.ac.uk < ' + emailFilePath
    # call('mutt -s "[Meter] 5 German pipeline" meter@energy.ox.ac.uk < ' + emailFilePath, shell=True)

def sendEmail():
    """
    use mutt to send and email with key counts
    """
    due_urgent = getCount(4,'date_choice < CURDATE() + INTERVAL "6" DAY')
    due_today  = getCount(4,'date_choice = CURDATE() + INTERVAL "6" DAY')
    due_future = getCount(4,'date_choice > CURDATE() + INTERVAL "6" DAY')
    await_confirm = getCount(3,'date_choice > CURDATE() + INTERVAL "6" DAY')
    pipeline = getCount(2,'date_choice > CURDATE() + INTERVAL "7" DAY')

    subjectLine = "[Meter] due {}, today {}, confirmed {}, await {}, pipeline {}".format(due_urgent, due_today, due_future, await_confirm, pipeline)
    print subjectLine
    call('mutt -e "set content_type=text/html" -s "' + subjectLine + '" meter@energy.ox.ac.uk < "./"', shell=True)

if __name__ == "__main__":
    # sendEmail()
    getGermans()
