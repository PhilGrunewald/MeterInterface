Utils
=====

This folder contains an number of useful utilities for common tasks.

json2sql
--------

Used to transfer json data to the database. Originally these files were created in json.

The activities_ json file was developed for and is principally used by `Meter App`__. This python script makes the `title` in json available in the database as the `meaning` for each `tuc` (`ID` in json). 

.. autofunction:: json2sql.main
   :noindex:

cockpit
-------

Creates a table summary in markdown table format.

.. autofunction:: cockpit.main
   :noindex:

app_tree
--------

Interactive command line interface to step through the screen options of the `Meter App`__

.. autofunction:: app_tree.main
   :noindex:

sql
---

.. autofunction:: sql.main
   :noindex:
