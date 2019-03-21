#!/usr/bin/python
""" sends separate emails about German and UK participants who have confirmed participation and need their parcel sending

WARNING: used daily as cron job on server!

email contains
contact details
number of aMeters needed
ID for eMeter

ToDo: add the participants comment.
"""

import os
from subprocess import call
import meter_db as mdb      # for sql queries

def getCount(status, condition):
    sqlq = """
            SELECT COUNT(*) AS c
             FROM Contact
               JOIN Household
               ON idContact = Contact_idContact
             WHERE Household.status = '{}'
             AND {}
            ;
            """.format(status, condition)
    return mdb.getSQL(sqlq)[0]['c']


def getSubjectline(locale):
    region ="<> 'de'"
    if (locale == 'DE'):
        region ="= 'de'"

    due          = getCount(4,'date_choice <= CURDATE() + INTERVAL "6" DAY AND Contact.status {}'.format(region))
    confirmed     = getCount(4,'date_choice > CURDATE() + INTERVAL "6" DAY AND Contact.status {}'.format(region))
    await_confirm = getCount(3,'date_choice > CURDATE() + INTERVAL "6" DAY AND Contact.status {}'.format(region))
    pipeline      = getCount(2,'date_choice > CURDATE() + INTERVAL "7" DAY AND Contact.status {}'.format(region))
    noDate        = getCount(1,'Contact.status {}'.format(region))

    subjectLine = "[Meter] due {}, confirmed {}/{}, date {}/{}".format(due, confirmed, int(confirmed)+int(await_confirm), pipeline, int(pipeline)+int(noDate))
    return subjectLine


def emailConfirmed():
    sqlq = """
           SELECT idHousehold, date_choice, Name, Address1, Address2, Town, Postcode, email, phone, age_group2, age_group3, age_group4, age_group5, age_group6, Contact.status AS st
             FROM Contact
             JOIN Household
             ON idContact = Contact_idContact
             WHERE Household.status = '4'
             ORDER BY date_choice;
            """
    hhConfirmed = mdb.getSQL(sqlq)
    # email file
    thisPath = os.path.dirname(os.path.abspath(__file__))
    emailFilePathUK = os.path.join(thisPath, "UKConfirmed.txt")
    emailFilePathDE = os.path.join(thisPath, "DEConfirmed.txt")
    UK = open(emailFilePathUK,"w")
    DE = open(emailFilePathDE,"w")
    anyUK = False
    anyDE = False
    for g in hhConfirmed:
        hhString = ""

        people = int(g['age_group2']) +int(g['age_group3']) +int(g['age_group4']) +int(g['age_group5']) +int(g['age_group6'])
        hhString+="{}\n{}\n{}\n{} {}\n{}\nHH: {}\nDate: {}\naMeters: {}\neMeter ".format(g['Name'],g['Address1'],g['Address2'],g['Postcode'],g['Town'],g['email'],g['idHousehold'],g['date_choice'],people)
        sqlq = """ SELECT idMeta, CollectionDate, Quality
                    FROM Meta
                    WHERE DataType = 'E'
                    AND Household_idHousehold = {}
                """.format(g['idHousehold'])
        eMeterList = mdb.getSQL(sqlq)

        for e in eMeterList:
            hhString+="{} ({} quality: {})\n        ".format(e['idMeta'],e['CollectionDate'],e['Quality'])
        hhString+="\n---------------------\n\n"

        if (g['st'] == 'de'):
            DE.write(hhString)
            anyDE = True
        else:
            UK.write(hhString)
            anyUK = True

    DE.close()
    UK.close()
    if (anyDE):
        subjectLine = getSubjectline("DE")
        cmd = 'mutt -e "set content_type=text/plain" -s "'+subjectLine+'" Marvin.Gleue@wiwi.uni-muenster.de -c meter@energy.ox.ac.uk < ' + emailFilePathDE
        call(cmd, shell=True)
    if (anyUK):
        subjectLine = getSubjectline("UK")
        cmd = 'mutt -e "set content_type=text/plain" -s "'+subjectLine+'" meter@energy.ox.ac.uk < ' + emailFilePathUK
        call(cmd, shell=True)

if __name__ == "__main__":
    emailConfirmed()
