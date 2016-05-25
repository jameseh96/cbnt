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
                subprocess.check_call(self.command, cwd=os.getcwd(), shell=True)
            except subprocess.CalledProcessError:
                print "failed to run command: '{}'".format(self.command)
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
        test_results = self._run_tests(config, parsed_args.iterations)
        name = name.split()[-1]
        report = self._generate_report(name, parsed_args.type, test_results)
        parsed_args.report_path = parsed_args.report_path or 'report.json'
        lnt_report_file = open(parsed_args.report_path, 'w')
        print >> lnt_report_file, report.render()
        lnt_report_file.close()
        self.submit_helper(parsed_args)
        exit(0)

    def _generate_report(self, tag, type, test_results):
        machine = lnt.testing.Machine('test-machine', {})
        run_info = self._generate_run_info(tag, type)
        run = lnt.testing.Run(self.start, self.end, info=run_info)
        test_outputs = []
        for test_result in test_results:
            test_outputs.extend(test_result.generate_report(tag))

        report = lnt.testing.Report(machine, run, test_outputs)
        return report

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Couchbase-based test suite')
        parser.add_argument('config', help='location of the config.yaml file '
                            'for this test run')
        parser.add_argument('type', choices=['master', 'cv'], help='type of result entry')
        parser.add_argument('--run_order', help='run order of this test run')
        parser.add_argument('-v', '--verbose', action='store_true', help='show verbose test results')
        parser.add_argument('--report_path', help='path to save report file to')
        parser.add_argument('--submit_url', help='url to submit report to', nargs='*')
        parser.add_argument('--commit', default=True, type=int,
                            help='commit result to db')
        parser.add_argument('-i', '--iterations', default=1, type=int,
                            help='number of iterations to run')
        parsed_args = parser.parse_args(args)
        return parsed_args

    def _parse_config(self, config_location):
        config = yaml.load(open(config_location, 'r').read())
        return config

    def _run_tests(self, config, iterations):
        self.start = datetime.datetime.utcnow()
        test_results = [CouchbaseTestResult(test['test'], test['command'],
                                            test['output'], iterations)
                        for test in config]
        self.end = datetime.datetime.utcnow()
        return test_results

    def _generate_run_info(self, tag, type):
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

        if type == 'cv':
            run_info.update({'parent_commit': self._get_parent_commit()})

        return run_info

    def _get_parent_commit(self):
        required_variables = {'project': os.environ.get('GERRIT_PROJECT', None),
                              'branch': os.environ.get('GERRIT_BRANCH', None),
                              'change_id': os.environ.get('GERRIT_CHANGE_ID', None),
                              'commit': os.environ.get('GERRIT_PATCHSET_REVISION', None)}

        if all(required_variables.values()):
            url = ('http://review.couchbase.org/changes/{project}~{branch}~'
                   '{change_id}/revisions/{commit}/commit'
                   .format(**required_variables))
            print 'Getting parent commit from', url
            response = urllib2.urlopen(url).read()
            start_index = response.index('{')
            json_response = json.loads(response[start_index:])
            parent_commit = json_response['parents'][0]['commit']
            return parent_commit

        else:
            print ('Unable to find required gerrit environment variables, '
                   'exiting')
            exit(1)

    def submit_helper(self, parsed_args):
        """Submit the report to the server.  If no server
        was specified, use a local mock server.
        """

        result = None
        if parsed_args.submit_url:
            from lnt.util import ServerUtil, ImportData
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
            exit(1)
        return result


def create_instance():
    return CouchbaseTest()