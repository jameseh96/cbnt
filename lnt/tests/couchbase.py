import argparse
import builtintest
import calendar
import datetime
import subprocess
import os
import sys
import time
import yaml
import xmltodict

import lnt

class CouchbaseTestResult(object):
    def __init__(self, name, command, output):
        self.name = name
        self.command = command
        self.output = output if isinstance(output, list) else [output]
        self._run_test()
        # The tests may involve some tear down time
        # Sleep the thread to eliminate this being a factor
        # for deviations between tests
        time.sleep(5)

    def _run_test(self):
        for output in self.output:
            try:
                os.remove(output)
            except (IOError, OSError):
                pass
        try:
            subprocess.check_call(self.command, cwd=os.getcwd(), shell=True)
        except subprocess.CalledProcessError:
            print 'failed to run'
        else:
            self.output = [xmltodict.parse(open(output, 'r'))
                           for output in self.output]

    def generate_report(self, tag):
        test_results = []
        for output in self.output:
            self._normalise_xml(output)
            for test_suite in output['testsuites']['testsuite']:
                for test in test_suite['testcase']:
                    full_test_name = '{}.'.format(tag) + '/'.join(
                        [test['@classname'], test['@name']]) + '.exec'
                    data_list = [str(test['@time'])]
                    test_output = lnt.testing.TestSamples(full_test_name, data_list)
                    test_results.append(test_output)

        return test_results

    def _normalise_xml(self, output):
        if not isinstance(output['testsuites']['testsuite'], list):
            output['testsuites']['testsuite'] = [
                output['testsuites']['testsuite']]

        for test_suite in output['testsuites']['testsuite']:
            if not isinstance(test_suite['testcase'], list):
                test_suite['testcase'] = [test_suite['testcase']]

class CouchbaseTest(builtintest.BuiltinTest):
    def describe(self):
        return 'Couchbase performance test suite'

    def run_test(self, name, args):
        parsed_args = self._parse_args(args)
        config = self._parse_config(parsed_args.config)
        self.run_order = parsed_args.run_order
        test_results = self._run_tests(config)
        name = name.split()[-1]
        report = self._generate_report(name, test_results)
        parsed_args.report_path = parsed_args.report_path or 'report.json'
        lnt_report_file = open(parsed_args.report_path, 'w')
        print >> lnt_report_file, report.render()
        lnt_report_file.close()
        self.submit_helper(parsed_args)
        exit(0)

    def _generate_report(self, tag, test_results):
        machine = lnt.testing.Machine('test-machine', {})
        run_info = self._generate_run_info(tag)
        run = lnt.testing.Run(self.start, self.end, info=run_info)
        test_outputs = []
        for test_result in test_results:
            test_outputs.extend(test_result.generate_report(tag))

        report = lnt.testing.Report(machine, run, test_outputs)
        return report

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='lol')
        parser.add_argument('config', help='location of the config.yaml file '
                            'for this test run')
        parser.add_argument('--run_order', help='run order of this test run')
        parser.add_argument('-v', '--verbose', action='store_true', help='show verbose test results')
        parser.add_argument('--report_path', help='path to save report file to')
        parser.add_argument('--submit_url', help='url to submit report to', nargs='*')
        parser.add_argument('--commit', default=True, type=int,
                            help='commit result to db')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def _parse_config(self, config_location):
        config = yaml.load(open(config_location, 'r').read())
        return config

    def _run_tests(self, config):
        self.start = datetime.datetime.utcnow()
        test_results = [CouchbaseTestResult(test['test'], test['command'],
                                            test['output'])
                        for test in config]
        self.end = datetime.datetime.utcnow()
        return test_results

    def _generate_run_info(self, tag):
        env_vars = ['BUILD_NUMBER',
                    'GERRIT_CHANGE_COMMIT_MESSAGE',
                    'GERRIT_CHANGE_OWNER_NAME',
                    'GERRIT_CHANGE_URL',
                    'BUILD_URL']

        run_info = {env_var: os.getenv(env_var, '') for env_var in env_vars
                    if os.getenv(env_var, '')}

        run_info.update({'git_sha': os.getenv('GERRIT_PATCHSET_REVISION', 'test'),
                         'run_order': str(self.run_order),
                         't': str(calendar.timegm(time.gmtime())),
                         'tag': tag})

        return run_info

    def submit_helper(self, parsed_args):
        """Submit the report to the server.  If no server
        was specified, use a local mock server.
        """

        result = None
        if parsed_args.submit_url:
            from lnt.util import ServerUtil, ImportData
            import urllib2
            for server in parsed_args.submit_url:
                self.log("submitting result to %r" % (server,))
                try:
                    result = ServerUtil.submitFile(server, parsed_args.report_path,
                                                   parsed_args.commit, parsed_args.verbose)
                except (urllib2.HTTPError, urllib2.URLError) as e:
                    print ("submitting to {} failed with {}".format(server,
                                                                     e))
                else:
                    ImportData.print_report_result(
                        result, sys.stdout, sys.stderr, parsed_args.verbose)
        else:
            # Simulate a submission to retrieve the results report.
            # Construct a temporary database and import the result.
            self.log("submitting result to dummy instance")

            import lnt.server.db.v4db
            import lnt.server.config
            db = lnt.server.db.v4db.V4DB("sqlite:///:memory:",
                                         lnt.server.config.Config.dummyInstance())
            result = lnt.util.ImportData.import_and_report(
                None, None, db, parsed_args.report_path, 'json', True)

        if result is None:
            print ("Results were not obtained from submission.")

        return result


def create_instance():
    return CouchbaseTest()