.. _concepts:

Concepts
========

CBNT's data model is pretty simple, and just following the :ref:`quickstart` can
get you going with performance testing. Moving beyond that, it is useful to have
an understanding of some of the core concepts in CBNT. This can help you get the
most out of CBNT.

Orders Machines and Tests
-------------------------

CBNT's data model was designed to track the performance of a system in many configurations
over its evolution.  In CBNT, and Order is the x-axis of your performance graphs.  It is
the thing that is changing.  Examples of common orders are software versions, 
Subversion revisions, and time stamps. Orders can also be used to represent
treatments, such as a/b.  You can put anything you want into CBNT as an order,
as long as it can be sorted by Python's sort function.
The idea being that an order represents a state of the source tree at a given
time, as such it has certain information in it, such as the ``git_commit`` of the
commit at the HEAD of the branch. Additionally CV orders have ``parent_commits``
to identify which order is the parent of the commit validation job.

A Machine in CBNT is the logical bucket which results are categorized by.
Comparing results from the same machine is easy, across machines is harder.
Sometimes machine can literally be a machine, but more abstractly, it can be any
configuration you are interested in tracking. For example, to store results
from an Arm test machine, you could have a machine call "ArmMachine".

Tests are benchmarks, the things you are actually testing.

Runs and Samples
----------------

Samples are the actual data points CBNT collects. Samples have a value, and
belong to a metric, for example a 4.00 second (value) compile time (metric).  
Runs are the unit in which data is submitted.  A Run represents one run through
a set of tests.  A run has a Order which it was run
on, a Machine it ran on, and a set of Tests that were run, and for each Test
one or more samples.  For example, a run on ArmMachine at
Order r1234 might have two Tests, test-a which had 4.0 compile time and 3.5
and 3.6 execution times and test-b which just has a 5.0 execution time. As new
runs are submitted with later orders (r1235, r1236), CBNT will start tracking
the per-machine, per-test, per-metric performance of each order.  This is how
CBNT tracks performance over the evolution of your code.

Test Suites
-----------

CBNT uses the idea of a Test Suite to control what metrics are collected.  Simply,
the test suite acts as a definition of the data that should be stored about
the tests that are being run.  CBNT currently comes with two default test suites.
The Nightly Test Suite (NTS) (which is run far more often than nightly now), 
collects 6 metrics per test: compile time, compile status, execution time, execution
status, score and size.  The Compile (compile) Test Suite, is focused on metrics
for compile quality: wall, system and user compile time, compile memory usage
and code size.  Other test suites can be added to CBNT if these sets of metrics
don't mactch your needs.

Any program can submit results data to CBNT, and specify any test suite.  The
data format is a simple JSON file, and that file needs to be HTTP POSTed to the
submitRun URL.

The most common program to submit data to CBNT is the CBNT client application
itself.  The ``lnt runtest nt`` command can run the LLVM test suite, and submit
data under the NTS test suite. Likewise the ``lnt runtest compile`` command
can run a set of compile time benchmarks and submit to the Compile test suite.

Given how simple it is to make your own results and send them to CBNT,
it is common to not use the CBNT client application at all, and just have a
custom script run your tests and submit the data to the CBNT server. Details
on how to do this are in :mod:`lnt.testing`
