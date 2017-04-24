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
    """ number of rows in a `table` matching the `condition` """
    sqlq = SQLquery['Count'].format(table,condition)
    cursor.execute(sqlq)
    results = cursor.fetchall()
    return results[0]['result']


def getCols(table):
    """ get list of all Column names in `table` """
    colNames = []
    sqlq = "SHOW Columns FROM {}".format(table)
    cursor.execute(sqlq)
    results = cursor.fetchall()
    for result in results:
        colNames.append(result['Field'])
    return colNames

def getColPDF(col,table,condition):
    """ list all values and percentage of occurances as string """
    cursor.execute(SQLquery['PDF'].format(col,table,condition))
    results = cursor.fetchall()
    q = '# Undefined \n\n'
    # Formatting for markdown table: 
    # 1. Header Row
    # 2. Formatting row: `:--` align left, `--:` align right
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
    """
cockpit.py 

        options: 


[-h,--help]

    this help 


[-l,--localhost] 

    override default host to use localhost

    Default: energy-use.org

    Example: python cockpit.py -l


[-c,--condition] 

    add sql criteria

    Default: None

    Example: python cockpit.py -c 'quality = 1 AND people > 3'


[-t,--table] 

    specify table.

    Default: `Household`

    Example: `python cockpit.py -t 'Individual'`


    """

    # Default values
    output = False
    table = "Household"
    # table = "Individual"
    condition = "True"

    # Optional arguments
    options = "hlt:c:o:"
    optionsLong = ["help","localhost","condition","table","output"]

    # Help
    helpStr =  "\
cockpit.py \n\
        options: \n\
\n\
[-h,--help]\n\
    this help \n\
\n\
[-l,--localhost] \n\
    override default host to use localhost\n\
    Default: energy-use.org\n\
    Example: python cockpit.py -l\n\
\n\
[-c,--condition] \n\
    add sql criteria\n\
    Default: None\n\
    Example: python cockpit.py -c 'quality = 1 AND people > 3'\n\
\n\
[-t,--table] \n\
    specify table.\n\
    Default: `Household`\n\
    Example: `python cockpit.py -t 'Individual'`\n\
"
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

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    # cursor = connectDB()
    main(sys.argv[1:])

