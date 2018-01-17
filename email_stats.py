#!/usr/bin/python

import sys
sys.path.append('../Analysis/res/')
from subprocess import call
import meter_db as mdb      # for sql queries
import meter_tools as mt    # for generic function

def getCount(status, condition):
    sqlq = """
            SELECT COUNT(*) AS c
            FROM Household
            WHERE status = '{}'
            AND {}
            ;
            """.format(status, condition)
    return mdb.getSQL(sqlq)[0]['c']

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
    sendEmail()
