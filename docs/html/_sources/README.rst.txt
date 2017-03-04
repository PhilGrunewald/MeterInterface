Meter study
===========

.. image:: _static/meter_logo.png
    :width: 300
    :align: right

The `Meter study <http://www.energy-use.org>`_ is a research project at the `University of Oxford's <http://ox.ac.uk>`_ Environmental Change Institute (`ECI <http://www.eci.ox.ac.uk/>`_) collecting data on household demographics, activities and electricity use. The aim is to better understand the timing of electricity use in households and identify potential routes towards flexibility in electricity use, which could support the emergence of more sustainable energy systems.


Activity recorder
=================

.. image:: _static/handheld.png
    :height: 200

The app to record activities is kept in the `Meter App <https://github.com/PhilGrunewald/MeterApp>`_ repository. This has it's own `documentation <https://github.com/PhilGrunewald/MeterApp/tree/master/docs>`_.

User data visualisation
=======================

.. image:: _static/user_profile.png
    :height: 200

A D3 based visualisation of activity and electricity data for a single household. See `Your data <https://github.com/PhilGrunewald/yourdata>`_ repository.


Admin interface
===============

.. image:: _static/MeterInterface.png

The Meter interface is a terminal based app to configure the research tools of the `Meter study <http://www.energy-use.org>`_ and support data handling with the MySQL database.
The forms support Mutt-style navigation and key bindings. Build on the `npyScreen <http://npyscreen.readthedocs.io/>`_ package.

.. automodule:: interface
    :members:

Meter Module
============

This module provides SQL functionality to connect, query and upload to the database.

.. automodule:: meter
    :members:

See `GitHub Documentation <https://rawgit.com/PhilGrunewald/AdminInterface/master/_build/html/>`__ for more information.
