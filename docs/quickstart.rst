.. _quickstart:

Quickstart Guide
================

This quickstart guide is designed for developers who are primarily
interested in using CBNT to test performance.

Installation
------------

Building Locally
----------------
The first thing to do is to checkout install the CBNT software itself. The
following steps should suffice on any modern Unix variant:

#. Install ``virtualenv``, if necessary::

           sudo easy_install virtualenv

   ``virtualenv`` is a standard Python tool for allowing the installation of
   Python applications into their own sandboxes, or virtual environments.

#. Create a new virtual environment for the CBNT application::

            virtualenv ~/mysandbox

   This will create a new virtual environment at ``~/mysandbox``.

#. Checkout the CBNT sources::

            git clone https://github.com/couchbaselabs/cbnt.git

#. Install CBNT into the virtual environment::

           ~/mysandbox/bin/python ~/cbnt/setup.py develop

   We recommend using ``develop`` instead of install for local use, so that any
   changes to the CBNT sources are immediately propagated to your
   installation. If you are running a production install or care a lot about
   stability, you can use ``install`` which will copy in the sources and you
   will need to explicitly re-install when you wish to update the CBNT
   application.

Docker Installation
-------------------
If you do not wish to setup the environment locally, then Docker deployment is
also supported, all files are located in ``deployment/docker``.

The following instructions assume that you have a familiarity with Docker, if
not then please check out the `Docker quickstart guide
<https://docs.docker.com/engine/getstarted/>`_. For the Dockerfile to work
correctly, you will need to run build from the root of your CBNT checkout.

There is a pre-canned version of the server container at
https://hub.docker.com/r/mattcarabine/cbnt_server and the client container
(which also includes everything required to build Couchbase) at
https://hub.docker.com/r/mattcarabine/cbnt_client

You can download these images with the following commands::

          docker pull mattcarabine/cbnt_server

          docker pull mattcarabine/cbnt_client

These can then run these using the commands::

          docker run -p 0.0.0.0:80:8000 -v <host_dir>:/lnt/db --name=cbnt_server -d mattcarabine/cbnt_server

          docker run -p 0.0.0.0:<host_port>:22 --name=cbnt_client -d mattcarabine/cbnt_client

The ``-v`` is recommended to create a persistent volume on your host machine,
so that data is not lost if you have to rebuild your container.

These are very handy for quick deployment but do not allow you to easily make
changes to the code that is being run, instead you may wish to consider using
the local build instructions detailed above.

Alternatively, you could rebuild the docker containers yourself using the
supplied Dockerfiles.
The command to do so (run from the individual docker directories) would be::

       docker build -f Dockerfile -t mattcarabine/cbnt_server ../../../

       docker build -f Dockerfile -t mattcarabine/cbnt_client ../../../

Although this method may be quite heavy weight if you expect to make code
changes often, so you want to just build natively instead!

That's it!


Running Tests
-------------

To execute testsuites using CBNT you use the ``lnt runtest``
command. The information below should be enough to get you started, but see the
:ref:`tests` section for more complete documentation.

#. Checkout a Couchbase build, if you haven't already::

      mkdir source
      cd source
      repo init -u git://github.com/couchbase/manifest -m branch-master.xml
      repo sync
      make

_
#. Execute the ``lnt runtest {ep-engine|memcached}`` test producer, point it at
the config file you wish to test::

     lnt runtest ep-engine <config_file> master --run_order=<run_order> --submit_url=<submit_url>/submitRun -v --commit=1

An important thing to note here though is that CBNT is designed to be powered
from Jenkins, so there are a few environment variables that need to be set to
allow the CBNT test harness to work correctly:

* 'GERRIT_PATCHSET_REVISION' - This is the git commit at the ``HEAD`` of the current project
* If running a commit validation test a few more are also required:
    - 'GERRIT_PROJECT' - Name of the project (e.g ep-engine or memcached)
    - 'GERRIT_BRANCH' - The branch the gerrit change is on (e.g master)
    - 'GERRIT_CHANGE_ID' - The gerrit changeid of the commit
    - Alternatively if the commit is not yet on gerrit but you wish to submit the
      result for testing purposes then you can do so using the flag
      ``--parent_commit`` which specifies the SHA1 of the parent of your commit

When running the client in a docker container you will have to run any commands
that you wish to within your container by using the ``docker exec`` command on
the host machine. More information about this can be found
`here <https://docs.docker.com/engine/reference/commandline/exec/>`_.

Viewing Results
---------------

By default, ``lnt runtest nt`` will show the passes and failures after doing a
run, but if you are interested in viewing the result data in more detail you
should install a local CBNT instance to submit the results to.

You can create a local CBNT instance with, e.g.::

    lnt create ~/myperfdb

This will create an CBNT instance at ``~/myperfdb`` which includes the
configuration of the CBNT application and a SQLite database for storing the
results.

Once you have a local instance, you can either submit results directly with::

     lnt import --commit=1 ~/myperfdb SANDBOX/test-<stamp>/report.json

or as part of a run with::

     lnt runtest --submit ~/myperfdb memcached ... arguments ...

Once you have submitted results into a database, you can run the CBNT web UI
with::

     lnt runserver ~/myperfdb

which runs the server on ``http://localhost:8000`` by default.
