import glob
import yaml
import sys

try:
    import threading
except Exception:
    import dummy_threading as threading

import sqlalchemy

import lnt.testing

import lnt.server.db.testsuitedb
import lnt.server.db.migrate

from lnt.util import logger
from lnt.server.db import testsuite
from sqlalchemy.orm import joinedload, subqueryload
import lnt.server.db.util


class V4DB(object):
    """
    Wrapper object for LNT v0.4+ databases.
    """
    def _load_schema_file(self, schema_file):
        session = self.make_session()
        with open(schema_file) as schema_fd:
            data = yaml.load(schema_fd)
        suite = testsuite.TestSuite.from_json(data)
        testsuite.check_testsuite_schema_changes(session, suite)
        suite = testsuite.sync_testsuite_with_metatables(session, suite)
        session.commit()

        # Create tables if necessary
        tsdb = lnt.server.db.testsuitedb.TestSuiteDB(self, suite.name, suite)
        session.close()
        tsdb.create_tables(self.engine)

    def _load_schemas(self):
        # Load schema files (preferred)
        schemasDir = self.config.schemasDir
        for schema_file in glob.glob('%s/*.yaml' % schemasDir):
            self._load_schema_file(schema_file)

        # Load schemas from database.
        session = self.make_session()
        ts_list = session.query(testsuite.TestSuite).all()
        session.expunge_all()
        session.close()
        for suite in ts_list:
            name = suite.name
            ts = lnt.server.db.testsuitedb.TestSuiteDB(self, name, suite)
            self.testsuite[name] = ts

    def __init__(self, path, config, baseline_revision=0):
        # If the path includes no database type, assume sqlite.
        if lnt.server.db.util.path_has_no_database_type(path):
            path = 'sqlite:///' + path

        self.path = path
        self.config = config
        self.baseline_revision = baseline_revision
        connect_args = {}
        if path.startswith("sqlite://"):
            # Some of the background tasks keep database transactions
            # open for a long time. Make it less likely to hit
            # "(OperationalError) database is locked" because of that.
            connect_args['timeout'] = 30
        self.engine = sqlalchemy.create_engine(path,
                                               connect_args=connect_args)

        # Update the database to the current version, if necessary. Only check
        # this once per path.
        lnt.server.db.migrate.update(self.engine)

        self.sessionmaker = sqlalchemy.orm.sessionmaker(self.engine)

        self.testsuite = dict()
        self._load_schemas()

    def close(self):
        self.engine.dispose()

    def make_session(self):
        return self.sessionmaker()

    def settings(self):
        """All the setting needed to recreate this instnace elsewhere."""
        return {
            'path': self.path,
            'config': self.config,
            'baseline_revision': self.baseline_revision,
        }
    
    @property
    def testsuite(self):
        # This is the start of "magic" part of V4DB, which allows us to get
        # fully bound SA instances for databases which are effectively
        # described by the TestSuites table.

        # The magic starts by returning a object which will allow us to use
        # dictionary like access to get the per-test suite database wrapper.
        if self._testsuite_proxy is None:
            self._testsuite_proxy = V4DB.TestSuiteAccessor(self)
        return self._testsuite_proxy


    def importDataFromDict(self, data, commit, testsuite_schema, config=None, cv=False):
        print("v4db: importDataFromDict")
        # Select the database to import into.
        data_schema = data.get('schema')
        if data_schema is not None and data_schema != testsuite_schema:
            raise ValueError, "Tried to import '%s' data into schema '%s'" % \
                              (data_schema, testsuite_schema)

        db = self.testsuite.get(testsuite_schema)
        if db is None:
            raise ValueError, "test suite %r not present in this database!" % (
                testsuite_schema)

        print("v4db: Calling db.importDataFromDict")
        return db.importDataFromDict(data, commit, config, cv=cv)


