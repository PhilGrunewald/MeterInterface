#!/usr/bin/python
"""
automated script run by cron job
check Household table for entries with quality NULL
calculate number of missing values (up to 10)
update quality
"""

import meter_db as mdb      # for sql queries

sql = """
      SELECT * FROM Household
      """
hhTable = mdb.getSQL(sql)
for hh in hhTable:
    hhID = hh['idHousehold']
    q = 10
    ageGroupSum = hh['age_group1'] + hh['age_group2'] + hh['age_group3'] + hh['age_group4'] + hh['age_group5'] + hh['age_group6']
    if (hh['people'] == 0): q -= 1
    if (ageGroupSum == 0): q -= 1
    if (hh['p6pm'] == -1): q -= 1
    if (hh['house_type'] == 0): q -= 1
    if (hh['rooms'] == 0): q -= 1
    if (hh['own'] == 0): q -= 1
    if (hh['provider'] == 'not given'): q -= 1
    if (hh['tariff'] == 0): q -= 1
    if (hh['income'] == 0): q -= 1
    if (hh['bill_affordable'] == 0): q -= 1
    sqlUpdate = """ 
                UPDATE Household 
                    SET quality = '{}' 
                    WHERE idHousehold = '{}'
                """.format(q,hhID)
    mdb.executeSQL(sqlUpdate)
    print "Set HH {} quality to {}".format(hhID,q)
mdb.commit()
