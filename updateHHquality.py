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
    if (hh['people'] is None): q -= 1
    if (ageGroupSum == 0): q -= 1
    if (hh['p6pm'] is None): q -= 1
    if (hh['house_type'] is None): q -= 1
    if (hh['rooms'] is None): q -= 1
    if (hh['own'] is None): q -= 1
    if (hh['provider'] is None): q -= 1
    if (hh['tariff'] is None): q -= 1
    if (hh['income'] is None): q -= 1
    if (hh['bill_affordable'] is None): q -= 1
    sqlq = """
            SELECT quality FROM Household WHERE idHousehold = {}
           """.format(hhID)
    r = mdb.getSQL(sqlq)[0]
    if (r['quality'] != q):
        sqlUpdate = """ 
                    UPDATE Household 
                        SET quality = '{}' 
                        WHERE idHousehold = '{}'
                    """.format(q,hhID)
        mdb.executeSQL(sqlUpdate)
        print "Set HH {} quality to {}".format(hhID,q)

mdb.commit()
