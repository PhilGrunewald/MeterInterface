#!/usr/bin/python
"""

el_downsample
-------------

.. note:: the original of this file is in Analysis repo. For consistency all these scripts may want to live in the Interface repo. Used on the server with live db (push with care)

MeterInterface uploads 1s electricity reading

This script identifies recordings which do not yet exist as 1min or 10min and uploads them

execute remotely with:

`ssh -t meter@energy-use.org "cd Analysis/scripts/ && python el_downsample.py"`

"""

"""
> _functions
use pandas to downsample


"""


# import sys
# sys.path.append('../res/')
import meter_db as mdb      # for sql queries
# import meter_tools as mt    # for generic function

import pandas as pd #data analysis
from pandas import Series, DataFrame #the book suggests this is done explicitly



#-----------------------------------------------------------------------------#
#                                _functions                                   #
#-----------------------------------------------------------------------------#

def downsample(idRecording, time_inc='1min'):
    """ 
    gets 1s electricity readings for idRecordings (idMeta)
    downsample and upload to relevant table
    """
    e = mdb.getElectricity(idRecording)             # get 1s electricity readings (as dataframe)
    e.index = pd.to_datetime(e.dt)                  # index by time
    e = e.resample(time_inc, label='left').mean()   # downsample, label left such that time refers to the next minute 
    del e['idElectricity']                          # remove index, so that a new one is auto-incremented
    engine = mdb.connectPandasDatabase()            # pandas is brutal, if not append it rewrites the table!!
    e.to_sql(con=engine, name="Electricity_{}".format(time_inc), if_exists='append', index=True)


def getMissingRecordings(time_inc='1min'):
    """ Find recodings missing in the downsample table """
    # eAll = mdb.getElectricityIDs()  
    eAll  = mdb.getElectricityRecording()
    eDS  = mdb.getElectricityRecording("_{}".format(time_inc))
    missing = eAll[~eAll['Meta_idMeta'].isin(eDS['Meta_idMeta'])]  # = is not in set
    return missing


def processMissing(time_inc):
    """ cycle through all missing records and call `downsample`"""
    missing = getMissingRecordings(time_inc)
    for recording in missing['Meta_idMeta']:
        try:
            downsample(recording,time_inc)
            print "<p>Processed {} for {}</p>".format(recording,time_inc)
        except:
            print "<p>failed for {} {}</p>".format(recording,time_inc)

#-----------------------------------------------------------------------------#
#                   _execution                                                #
#-----------------------------------------------------------------------------#

if __name__ == "__main__":
    # needs venv meter when run on server
    try:
        activate_this_file = "/home/meter/.venvs/meter/bin/activate_this.py"
        execfile(activate_this_file, dict(__file__=activate_this_file))
    except:
        print "venv is assumed"
    processMissing('1min')
    processMissing('10min')
