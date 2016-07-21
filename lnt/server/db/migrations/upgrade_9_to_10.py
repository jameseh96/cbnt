# Version 10 adds Gerrit Change IDs

import sqlalchemy
from sqlalchemy import *
from sqlalchemy.schema import Index
from sqlalchemy.orm import relation

import lnt.server.db.migrations.upgrade_0_to_1 as upgrade_0_to_1
import lnt.server.db.migrations.upgrade_2_to_3 as upgrade_2_to_3


def add_gerrit_ids(test_suite):
    # Grab the Base for the previous schemga so that we have all
    # the definitions we need.
    Base = upgrade_2_to_3.get_base(test_suite)
    # Grab our db_key_name for our test suite so we can properly
    # prefix our fields/table names.
    db_key_name = test_suite.db_key_name

    class Gerrit(Base):
        __tablename__ = db_key_name + '_Gerrit'
        id = Column("ID", Integer, primary_key=True)
        order_id = Column("OrderID", Integer,
                          ForeignKey(upgrade_0_to_1.OrderField.id),
                          index=True)
        gerrit_change_id = Column("gerrit_change_id", String(256),
                                  index=True)

    class CVGerrit(Base):
        __tablename__ = db_key_name + '_CV_Gerrit'
        id = Column("ID", Integer, primary_key=True)
        order_id = Column("OrderID", Integer,
                          ForeignKey(upgrade_0_to_1.CVOrderField.id),
                          index=True)
        gerrit_change_id = Column("gerrit_change_id", String(256),
                                  index=True)
        gerrit_change_id_parent = Column("gerrit_change_id_parent",
                                         String(256), index=True)

    return Base


def upgrade_testsuite(engine, session, name):
    # Grab Test Suite.
    test_suite = session.query(upgrade_0_to_1.TestSuite).filter_by(
        name=name).first()
    assert (test_suite is not None)

    # Add FieldChange to the test suite.
    Base = add_gerrit_ids(test_suite)

    # Create tables. We commit now since databases like Postgres run
    # into deadlocking issues due to previous queries that we have run
    # during the upgrade process. The commit closes all of the
    # relevant transactions allowing us to then perform our upgrade.
    session.commit()
    Base.metadata.create_all(engine)
    # Commit changes (also closing all relevant transactions with
    # respect to Postgres like databases).
    session.commit()


def upgrade(engine, cb_testsuites):
    # Create a session.
    session = sqlalchemy.orm.sessionmaker(engine)()

    for testsuite in cb_testsuites:
        try:
            upgrade_testsuite(engine, session, testsuite['name'])
        except Exception as e:
            print(e)
            pass

