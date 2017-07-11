"""
Define facilities for automatically applying rules to data.
"""

import os
import re
from lnt.util import logger
from lnt.testing.util.commands import timed


def load_rules():
    """
    Load available rules scripts from a directory.

    Rules are organized as:

    <current dir>/rules/
    <current dir>/rules/rule_.*.py
    ...
    """

    rule_script_rex = re.compile(
        r'^rule_(.*)\.py$')
    rule_scripts = {}

    rules_path = os.path.join(os.path.dirname(__file__),
                                              'rules')
    for item in os.listdir(rules_path):
        # Ignore certain known non-scripts.
        if item in ('README.txt', '__init__.py') or item.endswith('.pyc'):
            continue

        # Ignore non-matching files.
        m = rule_script_rex.match(item)
        if m is None:
            logger.warning("ignoring item {} in rule  directory: {}"
                           .format(item, rules_path))
            continue

        name = m.groups()[0]
        # Allow rules to be disabled by name
        if name.endswith("disabled"):
            continue
            
        rule_scripts[name] = os.path.join(rules_path, item)

    return rule_scripts

# Places our rules can hook to.
HOOKS = {'post_test_hook':[],
         'post_submission_hook':[],
         'post_regression_create_hook':[],
         'is_useful_change': []}
DESCRIPTIONS = {}


def register_hooks():
    """Exec all the rules files.  Gather the hooks from them
    and load them into the hook dict for later use.
    """
    for name, path in load_rules().items():
        globals = {}
        execfile(path, globals)
        DESCRIPTIONS[name] = globals['__doc__']
        for hook_name in HOOKS.keys():
            if hook_name in globals:
                HOOKS[hook_name].append(globals[hook_name])
    return HOOKS


def post_submission_hooks(ts, run_id):
    """Run all the post submission hooks on the submitted run."""
    for func in HOOKS['post_submission_hook']:
        try:
            func(ts, run_id)
        except Exception:
            continue


def is_useful_change(ts, field_change):
    """Run all the change filters. If any are false, drop this change."""
    all_filters = []
    for func in HOOKS['is_useful_change']:
        decision = func(ts, field_change)
        all_filters.append(decision)
    if len(all_filters) == 0:
        return True
    else:
        #  If any filter ignores, we ignore.
        return all(all_filters)

