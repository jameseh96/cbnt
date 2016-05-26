import argparse
import builtintest
import calendar
import datetime
import json
import subprocess
import os
import sys
import time
import urllib2
import yaml
import xmltodict

import lnt
from lnt.testing.util.commands import note, warning, fatal
from lnt.util import ImportData


class CouchbaseTestResult(object):
    def __init__(self, name, command, output, iterations):
        self.name = name
        self.command = command
        self.iterations = iterations
        self.output_files = output if isinstance(output, list) else [output]
        self.output = []
        self._run_test()
        # The tests may involve some tear down time
        # Sleep the thread to eliminate this being a factor
        # for deviations between tests
        time.sleep(5)

    def _run_test(self):
        for iteration in xrange(self.iterations):
            for output_file in self.output_files:
                try:
                    os.remove(output_file)
                except (IOError, OSError):
                    pass
            try:
                subprocess.check_call(self.command, cwd=os.getcwd(),
                                      shell=True)
            except subprocess.CalledProcessError:
                warning("failed to run command: '{}'".format(self.command))
            else:
                self.output.extend([xmltodict.parse(open(output_file, 'r'))
                                    for output_file in self.output_files])

    def generate_report(self, tag):
        test_results = []
        for output in self.output:
            self._normalise_xml(output)
            for test_suite in output['testsuites']['testsuite']:
                for test in test_suite['testcase']:
                    full_test_name = '{}.'.format(tag) + '/'.join(
                        [test['@classname'], test['@name']]) + '.exec'
                    data_list = [str(test['@time'])]
                    test_output = lnt.testing.TestSamples(full_test_name,
                                                          data_list)
                    test_results.append(test_output)

        return test_results

    @staticmethod
    def _normalise_xml(output):
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
        test_results = self._run_tests(config, parsed_args.iterations)
        name = name.split()[-1]
        report = self._generate_report(name, parsed_args.result_type,
                                       parsed_args.run_order, test_results)
        parsed_args.report_path = parsed_args.report_path or 'report.json'
        lnt_report_file = open(parsed_args.report_path, 'w')
        print >> lnt_report_file, report.render()
        lnt_report_file.close()
        server_report = self.submit_helper(parsed_args)
        ImportData.print_report_result(
            server_report, sys.stdout, sys.stderr, parsed_args.verbose)
        return server_report

    def _generate_report(self, tag, result_type, run_order, test_results):
        machine = self._generate_machine()
        run_info = self._generate_run_info(tag, result_type, run_order)
        run = lnt.testing.Run(self.start, self.end, info=run_info)
        test_outputs = []
        for test_result in test_results:
            test_outputs.extend(test_result.generate_report(tag))

        report = lnt.testing.Report(machine, run, test_outputs)
        return report

    @staticmethod
    def _parse_args(args):
        parser = argparse.ArgumentParser(
            description='Couchbase-based test suite')
        parser.add_argument('config', help='location of the config.yaml file '
                            'for this test run')
        parser.add_argument('result_type', choices=['master', 'cv'],
                            help='type of result entry')
        parser.add_argument('--run_order', help='run order of this test run')
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='show verbose test results')
        parser.add_argument('--report_path',
                            help='path to save report file to')
        parser.add_argument('--submit_url', help='url to submit report to',
                            nargs='*')
        parser.add_argument('--commit', default=True, type=int,
                            help='commit result to db')
        parser.add_argument('-i', '--iterations', default=1, type=int,
                            help='number of iterations to run')
        parsed_args = parser.parse_args(args)
        return parsed_args

    @staticmethod
    def _parse_config(config_location):
        config = yaml.load(open(config_location, 'r').read())
        return config

    def _run_tests(self, config, iterations):
        self.start = datetime.datetime.utcnow()
        test_results = [CouchbaseTestResult(test['test'], test['command'],
                                            test['output'], iterations)
                        for test in config]
        self.end = datetime.datetime.utcnow()
        return test_results

    def _generate_machine(self):
        #TODO: Make machine generation smarter
        return lnt.testing.Machine('test-machine', {})

    def _generate_run_info(self, tag, result_type, run_order):
        env_vars = ['BUILD_NUMBER',
                    'GERRIT_CHANGE_COMMIT_MESSAGE',
                    'GERRIT_CHANGE_OWNER_NAME',
                    'GERRIT_CHANGE_URL',
                    'BUILD_URL']

        run_info = {env_var: os.getenv(env_var) for env_var in env_vars
                    if os.getenv(env_var)}

        git_sha = os.getenv('GERRIT_PATCHSET_REVISION')
        if not git_sha:
            fatal("unable to determine git SHA for result, exiting.")

        run_info.update({'git_sha': git_sha,
                         'run_order': str(run_order),
                         't': str(calendar.timegm(time.gmtime())),
                         'tag': tag})

        if result_type == 'cv':
            run_info.update({'parent_commit': self._get_parent_commit()})

        return run_info

    def _get_parent_commit(self):
        required_variables = {
            'project': os.environ.get('GERRIT_PROJECT'),
            'branch': os.environ.get('GERRIT_BRANCH'),
            'change_id': os.environ.get('GERRIT_CHANGE_ID'),
            'commit': os.environ.get('GERRIT_PATCHSET_REVISION')}

        if all(required_variables.values()):
            url = ('http://review.couchbase.org/changes/{project}~{branch}~'
                   '{change_id}/revisions/{commit}/commit'
                   .format(**required_variables))
            note('getting parent commit from {}'.format(url))
            try:
                response = urllib2.urlopen(url).read()
            except Exception:
                fatal('failed to get parent commit from {}')
                raise

            # For some reason Gerrit returns a malformed json response
            # with extra characters before the actual json begins
            # Skip ahead to avoid this causing json deserialisation to fail
            start_index = response.index('{')
            response = response[start_index:]

            try:
                json_response = json.loads(response)
            except Exception:
                fatal('failed to decode Gerrit json response: {}'
                      .format(response))
                raise

            parent_commit = json_response['parents'][0]['commit']
            return parent_commit

        else:
            fatal('unable to find required Gerrit environment variables, '
                  'exiting')

    def submit_helper(self, parsed_args):
        """Submit the report to the server.  If no server
        was specified, use a local mock server.
        """

        result = None
        if parsed_args.submit_url:
            from lnt.util import ServerUtil
            for server in parsed_args.submit_url:
                self.log("submitting result to %r" % (server,))
                try:
                    result = ServerUtil.submitFile(
                        server, parsed_args.report_path, parsed_args.commit,
                        parsed_args.verbose)
                except (urllib2.HTTPError, urllib2.URLError) as e:
                    warning("submitting to {} failed with {}".format(server,
                                                                     e))
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
            fatal("results were not obtained from submission.")

        return result


def create_instance():
    return CouchbaseTest()
