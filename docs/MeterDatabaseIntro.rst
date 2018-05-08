The Meter Database
==================

This section explains

-  the types of data collected as part of the Meter project;
-  how these data are structured, stored and retrieved; and
-  the tools used to manage the data.

This is a live document. For the latest version, please visit
`Meter/docs <https://github.com/PhilGrunewald/Meter/tree/master/docs>`__.

What data are collected?
------------------------

Meter collects three types of data:

#. Household and individual survey information
#. Individual activity information
#. Electricity readings at household level

Each of these data are explained in more detail here.

.. figure:: MeterSchema.png
   :alt: Database schema for Meter Data

   Database schema for Meter Data

Household and individual survey information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Survey information is grouped into three tables:

**Contact**: This is personal information with restricted access (all
other data will become public). It is provided by participants when
registering via `energy-use.org/hhq.php <http://www.energy-use.org/hhq.php>`_.

**Household**: Socio-demographic information about household composition
(number of people, ages, housetype, appliances, electricity bills
income). This table also keeps the 'date\_choice' - the preferred date
for the study, and 'status' (see Section 'Status progression').

**Individual**: Collected on the study day via the booklet or app.
Covers individual information, such as age, occupation, working hours,
use of appliances...

Individual activity information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Recorded via booklet or app. Each entry contains:

**Time** (dt\_activity): Freely chosen by participant (unlike in
conventional Time-use research, where 10 minute windows are prescribed).
Certain times of particular interest will be suggested in the app (e.g.
5:30pm, 6pm, 8am). 'dt' stands for DateTime in the format '2012-11-13
23:59:59'.

**Time recorded** (dt\_recorded): The time when the entry was made. In
case of the app, entries can be back-dated (what did you do 20 minutes
ago?). Booklets may be coded up days later. Entries made via the
web-interface later still. This time stamp helps to identify 'how
devoiced' the entry is from the actual event.

**Time use code** (tuc): Numeric code based on an extended version of
the Harmonised European Time-Use Survey codes (@eurostat14). See field
'ID' in
`activities.json <https://github.com/PhilGrunewald/MeterApp/blob/master/www/js/activities.json>`__.

**Activity**: Plain text description of the activity. See field 'title'
in
`activities.json <https://github.com/PhilGrunewald/MeterApp/blob/master/www/js/activities.json>`__.

**Location**: Numeric code for location:

1. home
2. travelling
3. work
4. public place
5. outdoors
6. other
7. not specified

**Enjoyment**: Numeric code for enjoyment:

1. not at all
2. not very much
3. neutral
4. somewhat
5. very much
6. not specified

Electricity readings
^^^^^^^^^^^^^^^^^^^^

Collected via current clamp connected to an Android phone using `DMon
software <https://github.com/PhilGrunewald/DMon>`__. Recordings are
taken every second and stored in a csv file with two columns: a DateTime
stamp '2012-11-13 23:59:59') and the reading in Watt. The file name
refers to the Meta table 'idMeta' value followed by underscore and a
sequential number for each time readings were started for this device
with this 'idMeta'. Often the xxxx\_2.csv file contains the 'real'
readings, because the phone was started up for testing before shipment.
A xxxx\_03.csv file is created when starting up the phone to process the
data.

When uploading to the database this file is copied to the server first
to speed up the database processing. Each reading is a row with an ID
(idElectricity) the reference to the Meta entry (Meta\_idMeta), the
DateTime stamp and the reading value in Watt.

Database structure
------------------

The Meta table is central to the data structure as shown in Figure 1.
The name is perhaps an unfortunate left over from early trials with data
structure. It could equally be called the 'devices', 'instruments' or
'study events'.

Each row in this table has a unique ID (idMeta) and represents either a
booklet or a phone that has been sent out. The entry is created as part
of the equipment set up. Each household gets one entry for the
electricity recorder (eMeter) they receive and one for each booklet or
activity app. DataType for an eMeter is 'E', whereas a booklet or device
with the activity app is labelled 'A'.

When devices are returned the CollectionDate, which is 'NULL' until now
is updated.

Individual and Activity data share the same idMeta value, because they
come from the same instrument and can thus be linked.
Individual/Activity data and Electricity readings can be linked to their
Household via the Household\_idHousehold reference in their Meta entry
and vice versa: To find all Activities for a given Household with the ID
1234 one could use the following SQL statement:

.. code:: sql

    SELECT idMeta
        FROM Meta
        WHERE Household_idHousehold = 1234 AND DataType = 'A';

This will return one idMeta for each individual which has completed a
study day. The activities can then be retrieved for each of these
returned values. If 6789 was returned, the activity record can be
accessed with:

.. code:: sql

    SELECT dt_activity,activity 
        FROM Activities 
        WHERE Meta_idMeta = 6789;

This will produce a list of DateTime values and the description of the
activity.

Further information
-------------------

The data handing is principally conducted with the `Meter
Interface <https://github.com/PhilGrunewald/Meter>`__. This repository
includes a dummy database file in
`/dbDummy <https://github.com/PhilGrunewald/Meter/tree/master/dbDummy>`__
which can be used for experimenting. To set this up you require a
working MySQL version on your machine. Create a user and grant
privileges to the data.

To gain access to the live Meter database on
`www.energy-use.org <http://www.energy-use.org>`__ you will need to be
granted access.
