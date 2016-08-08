.. _intro:

Introduction
============

CBNT is an infrastructure for performance testing. The software itself consists
of two main parts, a web application for accessing and visualizing performance
data, and command line utilities to allow users to generate and submit test
results to the server.

The package was originally written for use in testing LLVM compiler
technologies, but is designed to be usable for the performance testing of any
software, in this case Couchbase software.

If you are a developer who is mostly interested in just using CBNT for the
test harness, then you should fast forward to the
:ref:`quickstart` or to the information on :ref:`tests`.

CBNT uses a simple and extensible format for interchanging data between the test
producers and the server; this allows the CBNT server to receive and store data
for a wide variety of applications.

Both the CBNT client and server are written in Python, however the test data
itself can be passed in one of several formats, including property lists and
JSON. This makes it easy to produce test results from almost any language.


Installation
------------

If you are only interested in using CBNT to run tests locally, see the
:ref:`quickstart`.

If you want to run an CBNT server, you will need to perform the following
additional steps:

 1. Create a new CBNT installation::

      lnt create path/to/install-dir

    This will create the CBNT configuration file, the default database, and a
    .wsgi wrapper to create the application. You can execute the generated app
    directly to run with the builtin web server, or use::

      lnt runserver path/to/install-dir

    which provides additional command line options. Neither of these servers is
    recommended for production use.

For production servers, you should consider using a full DBMS like PostgreSQL.
To create an CBNT instance with PostgreSQL backend, you need to do this instead:

 1. Create an CBNT database in PostgreSQL, also make sure the user has
    write permission to the database::

      CREATE DATABASE "lnt.db"

 2. Then create CBNT installation::

      lnt create path/to/install-dir --db-dir postgresql://user@host

 3. Run server normally::

      lnt runserver path/to/install-dir


Architecture
------------

The CBNT web app is currently implemented as a Flask WSGI web app, with Jinja2
for the templating engine. My hope is to eventually move to a more AJAXy web
interface.

The database layer uses SQLAlchemy for its ORM, and is typically backed by
SQLite.