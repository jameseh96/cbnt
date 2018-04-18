#!/usr/bin/env python2.7

import optparse
import sys
import os
import json
import subprocess
from shutil import copyfile
import sqlite3

FILE_NAME_PATTERN = "{}_{}.py"
CLASS_NAME_PATTERN = "{}{}Test"

TABLES_TO_COPY = ["CV_Gerrit", "CV_Order", "CV_Run", "CV_Sample",
                  "ChangeIgnore", "FieldChange", "FieldChangeV2", "Gerrit",
                  "Machine", "Order", "Profile", "Regression",
                  "RegressionIndicator", "Run", "Sample", "Test"]


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def main():
    parser = optparse.OptionParser()
    required_args = optparse.OptionGroup(parser, 'Required Arguments')
    required_args.add_option('-p', '--project', action='store', type='string',
                             dest='project', help='The name of the project to '
                                                  'create a new branch for.')
    required_args.add_option('-n', '--name', action='store', type='string',
                             dest='name', help='The short name of the new '
                                               'test-suite, for example '
                                               '"spock" or "vulcan"')
    required_args.add_option('-a', '--ancestor', action='store', type='string',
                             dest='parent', help='The full name of the parent '
                                                 'test-suite to create the '
                                                 'new test-stuite from. '
                                                 'Note this should be the '
                                                 'server-name specified in the'
                                                 ' config file. '
                                                 'For example: "kv-engine"')
    required_args.add_option('-d', '--database', action='store', type='string',
                             dest='database_path', help='The fully qualified '
                                                        'path to the database '
                                                        'file used by CBNT')
    required_args.add_option('-k', '--db-key', action='store', type='string',
                             dest='database_key',
                             help='Unique name for the database key '
                                  'for the new test suite. '
                                  'For example: "KV_spock"')

    optional_args = optparse.OptionGroup(parser, 'Optional Arguments')
    optional_args.add_option('-g', '--git', action='store', type='choice',
                             choices=['True', 'False'], default='True',
                             dest='use_git',
                             help="Enable/Disable interaction with Git. "
                                  "Options are: [True, False]")

    parser.add_option_group(required_args)
    parser.add_option_group(optional_args)

    (options, args) = parser.parse_args()

    for option in options.__dict__:
        if (options.__dict__[option] is None and
                option in required_args.defaults):
            print('Some required arguments were not set')
            parser.print_help()
            sys.exit(-2)

    if not os.path.isfile(options.database_path):
        print("Database file does not exist or is not a valid file")
        sys.exit(-2)

    config_file = open(
        "{}/../lnt/tests/kv_engine_testsuites.conf".format(get_script_path()),
        'r')
    global_config = json.load(config_file)
    config_file.close()

    parent_db_key = ""
    for item in global_config:
        if item['server-name'] == options.parent:
            parent_db_key = item['server-db-key']
    if not parent_db_key:
        print("Could not find the specified parent")
        sys.exit(-2)

    # Step 1: Kill and Remove the docker containers if they are running
    print("Killing and Removing existing server docker container")
    process = subprocess.Popen("docker stop cbnt_server".split(),
                               stdout=subprocess.PIPE)
    output, error = process.communicate()
    process = subprocess.Popen("docker rm cbnt_server".split(),
                               stdout=subprocess.PIPE)
    output, error = process.communicate()

    # Step 2: Checkout master branch
    # TODO: We might not want to do this... In theory the server should
    # always be running the up-to-date master branch though

    # print("Checking out master branch")
    # process = subprocess.Popen('git checkout master'.split(),
    # stdout=subprocess.PIPE)
    # output, error = process.communicate()

    # Step 3: Append the new testsuite name to the end of the config file
    print("Adding new testsuite to the config file")
    test_suite_config = {}
    test_suite_config['client-name'] = '{}_{}'.format(options.project,
                                                      options.name)
    test_suite_config['server-name'] = '{}_{}'.format(
        options.project.replace("_", "-"), options.name)
    test_suite_config['server-db-key'] = options.database_key
    global_config.append(test_suite_config)
    config_file = open(
        "{}/../lnt/tests/kv_engine_testsuites.conf".format(get_script_path()),
        'w')
    json.dump(global_config, config_file, indent=3)
    config_file.close()

    # Step 4: Create the necessary files within the tests folder
    print("Creating the new testsuite files")
    class_name = CLASS_NAME_PATTERN.format(
        "".join([a.capitalize() for a in options.project.split("_")]),
        options.name.capitalize())
    file_name = FILE_NAME_PATTERN.format(options.project.lower(),
                                         options.name.lower())
    with open("{}/../lnt/tests/".format(get_script_path()) + file_name,
              'w') as test_suite:
        test_suite.write("from couchbase import CouchbaseTest\n\n")
        test_suite.write(class_name + "(CouchbaseTest):\n")
        test_suite.write("    pass\n\n")
        test_suite.write("def create_instance():\n")
        test_suite.write("    return {}()\n".format(class_name))

    # Step 5: Stage a commit to push to git
    # (note, this needs a human to manually push)
    if options.use_git == "True":
        print("Staging changes for commit")
        process = subprocess.Popen(
            "git add {}/../lnt/tests/kv_engine_testsuites.conf".format(
                get_script_path()).split(),
            stdout=subprocess.PIPE)
        output, error = process.communicate()

        process = subprocess.Popen(("git add {}/../lnt/tests/".format(
            get_script_path()) + file_name).split(),
                                   stdout=subprocess.PIPE)
        output, error = process.communicate()

        commit_message = "[Automatic] Create {} test suite".format(
            file_name.rstrip(".py"))
        process_list = 'git commit -m {}'.split()
        process_list[-1] = process_list[-1].format(commit_message)
        process = subprocess.Popen(process_list, stdout=subprocess.PIPE)
        output, error = process.communicate()
    else:
        print("Not staging the database changes for Git")

    # Step 6: Rebuild and re-run the docker containers
    print("Rebuilding the docker container")
    process = subprocess.Popen(
        '{}/rebuild-server.sh'.format(get_script_path()).split(),
        stdout=subprocess.PIPE)
    output, error = process.communicate()

    # Step 7: Docker exec to do a lnt update
    print("Updating lnt")
    process = subprocess.Popen(
        "docker exec -it cbnt_server lnt update /lnt/db/db/data/lnt.db".split())
    output, error = process.communicate()

    # Step 8: Stop the docker container
    print("Stopping the docker container")
    process = subprocess.Popen("docker stop cbnt_server".split())
    output, error = process.communicate()

    # Step 9: Update the database to contain the new tables from the old ones
    print("Creating a temporary copy of the database")
    temp_file = "{}.tmp".format(options.database_path)
    copyfile(options.database_path, temp_file)

    print("Copying data to new test suite")
    conn = sqlite3.connect(temp_file)
    c = conn.cursor()
    for table in TABLES_TO_COPY:
        print("Copying from {}_{} to {}_{}".format(parent_db_key,
                                                   table,
                                                   options.database_key,
                                                   table))
        values = ("{}_{}".format(options.database_key, table),
                  "{}_{}".format(parent_db_key, table),)
        c.execute("INSERT INTO {} SELECT * FROM {}".
                  format(values[0], values[1]))
    conn.commit()
    conn.close()

    print("Removing the old database")
    os.remove(options.database_path)
    print("Promoting the new database")
    os.rename(temp_file, temp_file.rstrip(".tmp"))

    # Step 10: Restart the docker container :)
    print("Starting the docker container")
    process = subprocess.Popen("docker start cbnt_server".split())
    output, error = process.communicate()

    print("Finished adding new Test Suite.")


if __name__ == '__main__':
    main()
