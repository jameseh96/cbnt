import json
import calendar
import sys
import subprocess
import time
import xmltodict


def convert_xml(project, run_order, *file_names):
    output = dict()
    test_dict = xmltodict.parse(open(file_names[0], 'r').read())
    machine_dict = {'Info': {},
                    'Name': 'Test Machine'}
    start_time = test_dict['testsuites']['@timestamp'].replace('T', ' ')
    output['Machine'] = machine_dict

    end_time = test_dict['testsuites']['@timestamp'].replace('T', ' ')
    info = {'run_order': run_order,
            't': str(calendar.timegm(time.gmtime())),
            'tag': project,
            '__report_version__': '1'}
    run_dict = {'End Time': end_time,
                'Start Time': start_time,
                'Info': info}
    output['Run'] = run_dict

    output['Tests'] = list()

    for file_name in file_names:
        test_dict = xmltodict.parse(open(file_name, 'r').read())
        if isinstance(test_dict['testsuites']['testsuite']['testcase'], list):
            for test in test_dict['testsuites']['testsuite']['testcase']:
                full_test_name = '{}.'.format(project) + '/'.join([test['@classname'], test['@name']]) + '.exec'
                data_list = [str(test['@time'])]
                test_output = {'Data': data_list,
                               'Info': {},
                               'Name': full_test_name}
                output['Tests'].append(test_output)
        else:
            test = test_dict['testsuites']['testsuite']['testcase']
            full_test_name = '{}.'.format(project) + '/'.join([test['@classname'], test['@name']]) + '.exec'
            data_list = [str(test['@time'])]
            test_output = {'Data': data_list,
                           'Info': {},
                           'Name': full_test_name}
            output['Tests'].append(test_output)

    print json.dumps(output)


if __name__ == '__main__':
    convert_xml(*sys.argv[1:])