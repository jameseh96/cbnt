.. _tests:

Test Producers
==============

On the client-side, CBNT comes with a number of built-in test data producers.

CBNT also makes it easy to add new test data producers and includes examples of
custom data importers (e.g., to import buildbot build information into) and
dynamic test data generators (e.g., abusing the infrastructure to plot graphs,
for example).

Running a Local Server
----------------------

It is useful to set up a local CBNT server to view the results of tests, either
for personal use or to preview results before submitting them to a public
server. To set up a one-off server for testing::

  # Create a new installation in /tmp/FOO.
  $ lnt create /tmp/FOO
  created LNT configuration in '/tmp/FOO'
  ...

  # Run a local CBNT server.
  $ lnt runserver /tmp/FOO &> /tmp/FOO/runserver.log &
  [2] 69694

  # Watch the server log.
  $ tail -f /tmp/FOO/runserver.log
  * Running on http://localhost:8000/
  ...

Running Tests
-------------

The built-in tests are designed to be run via the ``lnt`` tool. The
following tools for working with built-in tests are available:

  ``lnt showtests``
    List the available tests.  Tests are defined with an extensible
    architecture. FIXME: Point at docs on how to add a new test.

  ``lnt runtest [<run options>] <test name> ... test arguments ...``
    Run the named test. The run tool itself accepts a number of options which
    are common to all tests. The most common option is ``--submit=<url>`` which
    specifies the server to submit the results to after testing is complete. See
    ``lnt runtest --help`` for more information on the available options.

    The remainder of the options are passed to the test tool itself. The options
    are specific to the test, but well behaved tests should respond to ``lnt
    runtest <test name> --help``. The following section provides specific
    documentation on the built-in tests.

Built-in Tests
--------------
All built-in tests are based off of the ``couchbase`` test harness.

The ``couchbase`` based test harnesses require a yaml config file to know which
tests to run.
The config file follows the following format::

       - test: test1
         command: "command to run this test"
         output:
           - "output1.xml"
           - "output2.xml"
       - test: test2
         command: "command to run this test"
         output: "output.xml"

One really important thing to note about this config file is that all commands
should be relative to the root of the couchbase build directory (i.e the
directory which contains all of the projects) so that it can appropriately find
all of the required files. e.g ``

The harness will run the command provided and then consume the input xml files
generated. These xml files follow the format of the gtest xml output, as it is
already commonly used within Couchbase tests.
A brief overview of this format can be found _here: http://help.catchsoftware.com/display/ET/JUnit+Format

Below is also an example of such an xml report (from a real run!)::

    <testsuites timestamp="2016-02-29T15:44:08">
      <testsuite name="ep-perfsuite">
        <testcase name="1_bucket_1_thread_baseline.Add.median" time="7.09" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Add.pct95" time="9.263" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Add.pct99" time="10.709" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Get.median" time="4.115" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Get.pct95" time="4.278" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Get.pct99" time="4.374" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Replace.median" time="6.937" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Replace.pct95" time="7.309" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Replace.pct99" time="10.095" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Append.median" time="72.567" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Append.pct95" time="204.058" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Append.pct99" time="269.502" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Delete.median" time="4.54" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Delete.pct95" time="5.12" classname="ep-perfsuite"/>
        <testcase name="1_bucket_1_thread_baseline.Delete.pct99" time="11.374" classname="ep-perfsuite"/>
      </testsuite>
    </testsuites>

The test harness then uses this input to generate an overall run report to
submit to the server, this is usually submitted as part of the run, but can also
be saved and submitted separately.

An example report is as follows::

    {
        "Machine": {
            "Info": {
                "cores": "16",
                "hardware": "x86_64",
                "os": "#47-Ubuntu SMP Fri May 2 23:30:00 UTC 2014"
            },
            "Name": "KV-Engine-Perf-1"
        },
        "Run": {
            "End Time": "2016-06-21 16:08:18",
            "Info": {
                "Build Number": "6",
                "Commit Message": "This is a commit",
                "Gerrit URL": "http://review.couchbase.org/65082",
                "Jenkins URL": "http://factory.couchbase.com/job/ep-engine-master-perf/6/",
                "Owner": "Commit Owner",
                "__report_version__": "1",
                "git_sha": "55c4d1b58e667dad5492692171fcb2f887e1da20",
                "run_order": "6",
                "t": "1466525298",
                "tag": "ep-engine"
            },
            "Start Time": "2016-06-21 16:05:26"
        },
        "Tests": [
            {
                "Data": [
                    7.073
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Add.median.exec"
            },
            {
                "Data": [
                    9.27
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Add.pct95.exec"
            },
            {
                "Data": [
                    10.598
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Add.pct99.exec"
            },
            {
                "Data": [
                    4.111
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Get.median.exec"
            },
            {
                "Data": [
                    4.273
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Get.pct95.exec"
            },
            {
                "Data": [
                    4.398
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Get.pct99.exec"
            },
            {
                "Data": [
                    7.023
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Replace.median.exec"
            },
            {
                "Data": [
                    7.394
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Replace.pct95.exec"
            },
            {
                "Data": [
                    10.13
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Replace.pct99.exec"
            },
            {
                "Data": [
                    72.614
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Append.median.exec"
            },
            {
                "Data": [
                    203.883
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Append.pct95.exec"
            },
            {
                "Data": [
                    212.15
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Append.pct99.exec"
            },
            {
                "Data": [
                    4.501
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Delete.median.exec"
            },
            {
                "Data": [
                    5.184
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Delete.pct95.exec"
            },
            {
                "Data": [
                    11.43
                ],
                "Info": {},
                "Name": "ep-engine.ep-perfsuite/1_bucket_1_thread_baseline.Delete.pct99.exec"
            }
        ]
    }

You can submit any report to the server which adheres to this format!

Adding Testsuites
-----------------
By default there are two ``Couchbase`` based testsuites, ``ep-engine`` and
``memcached`` but it is very easy to add new testsuites.

To add a new test to the test harness you can simply add the testsuite name to
the ``known_tests`` set in ``lnt/tests/__init__.py`` and then create a new file
``your_test_name.py`` in ``lnt/tests/`` which follows the format::

   from couchbase import CouchbaseTest


    class YourTestClass(CouchbaseTest):
        pass

    def create_instance():
        return YourTestClass()

Your new testsuite should now be accessible in the test harness!

Adding a new testsuite to the database is just as simple, you simply add your
new testsuite to the list of ``CB_TESTSUITES`` in ``lnt/server/db/migrate.py``,
specifying the name of the testsuite and its db key.
Once this is done you just run the command ``lnt update /path/to/db`` to
update an exist database or ``lnt create`` to create a new database and
your new testsuite will be created!