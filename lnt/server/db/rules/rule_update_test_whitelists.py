"""
Post submission hook to update the whitelists of all tests featured in a run after the run
has been submitted.
"""
from lnt.testing.util.commands import note, timed


def get_all_tests_for_run(ts, run_id):
    return ts.query(ts.Test).join(ts.Sample).filter(ts.Sample.run_id == run_id).all()


def get_all_field_changes_for_run(ts, run_id):
    return ts.query(ts.FieldChange).filter(ts.FieldChange.run_id == run_id).all()


@timed
def update_whitelist(ts, run_id):
    """Update the test whitelists
    Find all regressions in the current run
    If a test has regressed, reset its counter to 0 otherwise increment it
    """
    note("Running whitelist updater")
    changed = 0
    tests = get_all_tests_for_run(ts, run_id)
    field_changes = get_all_field_changes_for_run(ts, run_id)
    regressions = []

    for field_change in field_changes:
        regressions.append(field_change.test_id)

    for test in tests:
        if test.id in regressions:
            test.whitelist = 0
            changed += 1
            note("Resetting whitelist value for {}".format(test.name))
            regressions.remove(test.id)
        else:
            test.whitelist += 1

    ts.commit()
    note("Reset the whitelist of {} tests".format(changed))

post_submission_hook = update_whitelist
