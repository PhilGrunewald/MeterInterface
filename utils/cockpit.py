#!/usr/bin/env python
import getopt
import sys
import json
import MySQLdb.cursors
import db_ini as db     # reads the database and file path information
# override host to local
# db.Host='localhost'

# ========= #
#  GLOBALS  #
# ========= #


SQLquery ={
"PDF": "\
Select value,meaning,percent FROM \
(SELECT {0} AS col,ROUND \
    ( \
     COUNT(*)/ \
         ( \
         SELECT COUNT(*) as count  \
         FROM {1} \
         WHERE {2} \
         ) \
     *100 \
     ,1) as percent  \
    FROM {1}  \
    WHERE {2} \
    GROUP BY col) as ColPercent \
JOIN Legend \
    ON col = Legend.`value` \
    WHERE Legend.`column` = '{0}' \
    AND Legend.`table` = '{1}' \
    ORDER BY value;",

"PDF_noLegend": "\
    Select value, percent  \
	FROM (SELECT {0} AS value,ROUND     (       \
    COUNT(*)/          (          SELECT COUNT(*) as count            \
    FROM {1}          WHERE {2}          )      *100      ,1) as percent       \
    FROM {1}      WHERE {2}      \
    GROUP BY value) as ColPercent \
    ORDER BY value;",

"Count": "\
    SELECT Count(*) as result\
    FROM {0}\
    WHERE {1};"
}


# ========= #
# FUNCTIONS #
# ========= #

def connectDB():
    """ use db credentials for MySQLdb """
    dbConnection = MySQLdb.connect(
        host=db.Host,
        user=db.User,
        passwd=db.Pass,
        db=db.Name,
        cursorclass=MySQLdb.cursors.DictCursor)
    return dbConnection.cursor()

def getCount(table,condition):
    sqlq = SQLquery['Count'].format(table,condition)
    cursor.execute(sqlq)
    results = cursor.fetchall()
    return results[0]['result']


def getCols(table):
    """ get list of Column names  """
    colNames = []
    sqlq = "SHOW Columns FROM {}".format(table)
    cursor.execute(sqlq)
    results = cursor.fetchall()
    for result in results:
        colNames.append(result['Field'])
    return colNames

def getColPDF(col,table,condition):
    """ list all values and percentage of occurances """
    cursor.execute(SQLquery['PDF'].format(col,table,condition))
    results = cursor.fetchall()
    q = '# Undefined \n\n'
    row = "{}\t|{}\n:--- |---:\n".format(col,'Percent')
    for result in results:
        if (result['value'] == 'q'):
            q = "# {}\n\n".format(result['meaning'])
        else:
            row += "{}\t|{}\n".format(result['meaning'],result['percent'])
    if (len(results) < 2):
        cursor.execute(SQLquery['PDF_noLegend'].format(col,table,condition))
        results2 = cursor.fetchall()
        for result in results2:
            row += "{}\t|{}\n".format(result['value'],result['percent'])
    return "\n{}\n{}".format(q,row)

def getTablePDFs(table,condition):
    """ go through all cols and return PDF """
    PDF_Str = ""
    for col in getCols(table):
        PDF =  getColPDF(col,table,condition)
        if (PDF.count('\n') < 18):
            # Formatting for markdown table: 2 col - align right
            # inserted after header (i.e after first \n)
            # PDF_table = PDF.replace("\n","\n---: |---:\n",1)
            PDF_Str += PDF
    return PDF_Str

def createCockpit(table,condition,output):
    """ produce summary for table stats """
    if output:
        with open(output,'w') as f:
           f.write("% Table: {}\n".format(table))
           f.write("% Count: {}\n".format(getCount(table,condition)))
           f.write(getTablePDFs(table,condition))

def main(argv):
    """ Check for arguments """

    # Default values
    global width
    output = False
    table = "Household"
    condition = "True"
    # table = "Individual"

    # Optional arguments
    options = "hlt:c:o:"
    optionsLong = ["help","file"]

    # Help
    helpStr =  "sql.py {} \n\
                options \n\
                [-h,--help]\t\tthis help \n\
                ".format(options)
    result = helpStr

    # Evaluate arguments
    try:
        opts, args = getopt.getopt(argv,options,optionsLong)
    except getopt.GetoptError:
        print helpStr
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print helpStr
            sys.exit()
        elif opt in ("-l", "--localhost"):
            db.Host = 'localhost'
        elif opt in ("-c", "--condition"):
            condition = arg
        elif opt in ("-t", "--table"):
            table = arg
        elif opt in ("-o", "--output"):
            output = arg

    global cursor
    cursor = connectDB()
    createCockpit(table,condition,output)
    print "Entry complete\n\n"

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    cursor = connectDB()
    main(sys.argv[1:])

