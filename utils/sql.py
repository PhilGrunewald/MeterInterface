#!/usr/bin/env python
import getopt
import sys
import json
import MySQLdb.cursors
import db_ini as db     # reads the database and file path information
# override host to local

# ========= #
#  GLOBALS  #
# ========= #

width = 0

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

def getResults(_query):
    """ send sql query and return result as list """
    cursor.execute(_query)
    results = cursor.fetchall()
    ks = results[0].keys()
    if width:
        resultStr =  '\t'.join("{0: >{1}.{1}}".format(str(e),width) for e in ks)
    else:
        resultStr =  '\t'.join("{}".format(str(e)) for e in ks)
        
    for result in results:
        vs = result.values()
        resultStr += '\n'
        if width:
            resultStr += '\t'.join("{0: >{1}.{1}}".format(str(e),width) for e in vs)
        else:
            resultStr += '\t'.join("{}".format(str(e)) for e in vs)

    return resultStr

def main(argv):
    """ Check for arguments """
    global width
    options = "hw:q:f:o:O"
    optionsLong = ["help","file"]
    helpStr =  "sql.py {} \n\
                options \n\
                [-h,--help]\t\tthis help \n\
                [-l,--localhost]\t\tuse localhost\n\
                [-w,--width]\t\tcolumn width [10]\n\
                [-q,--query]\t\tSQL query\n\
                [-f,--file]\t\tfile with SQL query\n\
                [-o,--output]\t\toutput file\n\
                [-O,--Output]\t\twrite to sql_result.txt\n\
                ".format(options)
    result = helpStr
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
        elif opt in ("-w", "--width"):
            width = arg
            print width
        elif opt in ("-q", "--query"):
            result = getResults(arg)
        elif opt in ("-f", "--file"):
            with open(arg,'r') as f:
                query = f.read()
            result = getResults(query)
        elif opt in ("-o", "--output"):
            print "x{}y".format(arg)
            if (arg == ''):
               arg = 'sql_result.txt'
            with open(arg,'w') as f:
               f.write(result)

    print "{}".format(result)
    print "Entry complete\n\n"

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    cursor = connectDB()
    main(sys.argv[1:])
