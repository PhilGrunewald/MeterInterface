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
seperator = '\t'
outputFile = 'sql_result.txt'

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
    cursor = connectDB()
    cursor.execute(_query)
    results = cursor.fetchall()
    ks = results[0].keys()
    if width:
        resultStr =  seperator.join("{0: >{1}.{1}}".format(str(e),width) for e in ks)
    else:
        resultStr =  seperator.join("{}".format(str(e)) for e in ks)
        
    for result in results:
        vs = result.values()
        resultStr += '\n'
        if width:
            resultStr += seperator.join("{0: >{1}.{1}}".format(str(e),width) for e in vs)
        else:
            resultStr += seperator.join("{}".format(str(e)) for e in vs)

    return resultStr

def main(argv):
    """\
A tool to develop and test SQL statements.\n\n\
Example:\n\
python sql.py -q 'SELECT * FROM table' \n\n\
[-h,--help]\n\
    this help \n\n\
[-l,--localhost]\n\
    use localhost [default: 109.74.196.205]\n\n\
[-s,--seperator]\n\
    specify column seperator [default: tab]\n\n\
[-w,--width]\n\
    column width [default: 10]\n\n\
[-q,--query | -f,--file]\n\
    SQL query as argument or read from a file\n\n\
[-o,--output]\n\
    sepcify output file name [default: sql_result.txt]\
    """
    global width
    options = "hlw:q:f:o:s:"
    optionsLong = ["help","file","query","output"]
    helpStr =  "sql.py {} \n\
Example:\n\
python sql.py -q 'SELECT * FROM table' \n\n\
[-h,--help]\n\
    this help \n\n\
[-l,--localhost]\n\
    use localhost [default: 109.74.196.205]\n\n\
[-s,--seperator]\n\
    specify column seperator [default: tab]\n\n\
[-w,--width]\n\
    column width [default: 10]\n\n\
[-q,--query | -f,--file]\n\
    SQL query as argument or read from a file\n\n\
[-o,--output]\n\
    sepcify output file name [default: sql_result.txt]\
".format(options)
    result = helpStr
    query = 'SHOW tables;'
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
        elif opt in ("-s", "--seperator"):
            global seperator
            seperator = arg
        elif opt in ("-w", "--width"):
            width = arg
            print width
        elif opt in ("-q", "--query"):
            query = arg
        elif opt in ("-f", "--file"):
            with open(arg,'r') as f:
                query = f.read()
        elif opt in ("-o", "--output"):
            global outputFile
            outputFile = arg

    result = getResults(query)
    print "{}".format(result)
    with open(outputFile,'w') as f:
       f.write(result)

# ========= #
#  EXECUTE  #
# ========= #
if __name__ == "__main__":
    main(sys.argv[1:])
