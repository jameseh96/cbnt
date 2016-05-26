"""
Access to built-in tests.
"""

import yaml
import lnt.tests.couchbase

def get_test_names():
    """get_test_names() -> list

    Return the list of known built-in test names.
    """

    return known_tests


def get_test_instance(name):
    """get_test_instance(name) -> lnt.test.BuiltinTest

    Return an instance of the named test.
    """
    # Allow hyphens instead of underscores when specifying the test on the command
    # line. (test-suite instead of test_suite).
    name = name.replace('-', '_')
    
    if name in known_tests:
        module = getattr(__import__('lnt.tests.%s' % name, level=0).tests,
                         name)
    else:
        if name in couchbase_tests:
            module = lnt.tests.couchbase
        else:
            raise KeyError, name

    return module.create_instance()


def _find_couchbase_tests():
    # Load all couchbase tests from the relevant config file
    tests = yaml.load(open('/Users/matt/lnt/lnt/cb_config/tests.yml',
                           'r').read())
    return {test['name'].replace('-', '_') for test in tests}


def get_test_description(name):
    """get_test_description(name) -> str

    Return the description of the given test.
    """

    return get_test_instance(name).describe()

__all__ = ['get_test_names', 'get_test_instance', 'get_test_description']

# FIXME: There are better ways to do this, no doubt. We also would like this to
# be extensible outside of the installation. Lookup how 'nose' handles this.

known_tests = {'compile', 'nt', 'test_suite'}
couchbase_tests = _find_couchbase_tests()
