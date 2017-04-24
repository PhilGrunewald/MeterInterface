===========
Meter study
===========

.. image:: docs/MeterSchema.png
    :width: 300

.. image:: docs/meter_logo.png
    :width: 300
    :align: right

The Meter_ Study is a research project at the `University of Oxford's <http://ox.ac.uk>`_ Environmental Change Institute (`ECI <http://www.eci.ox.ac.uk/>`_) collecting data on household demographics, activities and electricity use. The aim is to better understand the timing of electricity use in households and identify potential routes towards flexibility in electricity use, which could support the emergence of more sustainable energy systems.

.. toctree::
    :maxdepth: 3
    :caption: Content:

    README.rst



Modules in this Repository
==========================


Meter
-----

This module provides SQL functionality to connect, query and upload to the database.

// .. automodule:: meter
//    :members:


Meter interface
---------------

.. image:: docs/MeterInterface.png

The Meter interface is a terminal based app to configure the research tools of the `Meter study <http://www.energy-use.org>`_ and support data handling with the MySQL database.
The forms support Mutt-style navigation and key bindings, based on the `npyScreen <http://npyscreen.readthedocs.io/>`_ package.

.. automodule:: interface
    :members:

Meter mailer
------------

A utility to send emails to mailing lists and contacts in the Meter Database. Built on a similar framework as the Meter interface.


See full Documentation_ for more detail.

.. include:: utils/README.rst


.. include:: docs/MeterDatabaseIntro.rst

.. include:: docs/Configure_aMeter.rst

.. include:: json/README.rst

Other Meter Repositories
========================


Activity recorder
-----------------

.. image:: docs/handheld.png
    :height: 200

The app to record activities is kept in the `Meter App`__ repository (see `MeterApp documentation <https://github.com/PhilGrunewald/MeterApp/tree/master/docs>`_).


User data visualisation
-----------------------

.. image:: docs/user_profile.png
    :height: 200

A D3 based visualisation of activity and electricity data for a single household. See `Your data <https://github.com/PhilGrunewald/yourdata>`_ repository.



.. _Meter: http://www.energy-use.org

.. _`Meter App`: https://github.com/PhilGrunewald/MeterApp

.. _Documentation: https://rawgit.com/PhilGrunewald/MeterInterface/master/docs/html/_

.. _activities: ../json/activities.json 

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
