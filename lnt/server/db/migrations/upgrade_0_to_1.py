# Version 0 is an empty database.
#
# Version 1 is the schema state at the time when we started doing DB
# versioning.

import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


###
# Core Schema


class SampleType(Base):
    __tablename__ = 'SampleType'
    id = Column("ID", Integer, primary_key=True)
    name = Column("Name", String(256), unique=True)


class StatusKind(Base):
    __tablename__ = 'StatusKind'
    id = Column("ID", Integer, primary_key=True, autoincrement=False)
    name = Column("Name", String(256), unique=True)


class TestSuite(Base):
    __tablename__ = 'TestSuite'
    id = Column("ID", Integer, primary_key=True)
    name = Column("Name", String(256), unique=True)
    db_key_name = Column("DBKeyName", String(256))
    version = Column("Version", String(16))
    machine_fields = relation('MachineField', backref='test_suite')
    order_fields = relation('OrderField', backref='test_suite')
    run_fields = relation('RunField', backref='test_suite')
    sample_fields = relation('SampleField', backref='test_suite')
    cv_order_fields = relation('CVOrderField', backref='test_suite')
    cv_run_fields = relation('CVRunField', backref='test_suite')
    cv_sample_fields = relation('CVSampleField', backref='test_suite')


class MachineField(Base):
    __tablename__ = 'TestSuiteMachineFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    info_key = Column("InfoKey", String(256))


class OrderField(Base):
    __tablename__ = 'TestSuiteOrderFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    info_key = Column("InfoKey", String(256))
    ordinal = Column("Ordinal", Integer)


class RunField(Base):
    __tablename__ = 'TestSuiteRunFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    info_key = Column("InfoKey", String(256))


class CVOrderField(Base):
    __tablename__ = 'TestSuiteCVOrderFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    info_key = Column("InfoKey", String(256))
    ordinal = Column("Ordinal", Integer)


class CVRunField(Base):
    __tablename__ = 'TestSuiteCVRunFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    info_key = Column("InfoKey", String(256))


class SampleField(Base):
    __tablename__ = 'TestSuiteSampleFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    type_id = Column("Type", Integer, ForeignKey('SampleType.ID'))
    type = relation(SampleType)
    info_key = Column("InfoKey", String(256))
    status_field_id = Column("status_field", Integer, ForeignKey(
        'TestSuiteSampleFields.ID'))
    status_field = relation('SampleField', remote_side=id)


class CVSampleField(Base):
    __tablename__ = 'TestSuiteCVSampleFields'
    id = Column("ID", Integer, primary_key=True)
    test_suite_id = Column("TestSuiteID", Integer, ForeignKey('TestSuite.ID'),
                           index=True)
    name = Column("Name", String(256))
    type_id = Column("Type", Integer, ForeignKey('SampleType.ID'))
    type = relation(SampleType)
    info_key = Column("InfoKey", String(256))
    status_field_id = Column("status_field", Integer, ForeignKey(
        'TestSuiteCVSampleFields.ID'))
    status_field = relation('CVSampleField', remote_side=id)


def initialize_core(lnt_engine, session):
    # Create the tables.
    Base.metadata.create_all(lnt_engine)

    # Create the fixed sample kinds.
    #
    # NOTE: The IDs here are proscribed and should match those from
    # 'lnt.testing'.
    session.add(StatusKind(id=0, name="PASS"))
    session.add(StatusKind(id=1, name="FAIL"))
    session.add(StatusKind(id=2, name="XFAIL"))

    # Create the fixed status kinds.
    session.add(SampleType(name="Real"))
    session.add(SampleType(name="Status"))

    session.commit()


def initialize_couchbase_definition(engine, session, name, key_name):
    real_sample_type = session.query(SampleType). \
        filter_by(name="Real").first()
    status_sample_type = session.query(SampleType). \
        filter_by(name="Status").first()

    # Create a test suite compile with "lnt runtest nt".
    ts = TestSuite(name=name, db_key_name=key_name)

    # Promote the natural information produced by 'runtest nt' to fields.
    ts.machine_fields.append(MachineField(name="hardware",
                                          info_key="hardware"))

    ts.machine_fields.append(MachineField(name="os", info_key="os"))

    # The only reliable order currently is the "run_order" field. We will want
    # to revise this over time.
    ts.order_fields.append(OrderField(name="llvm_project_revision",
                                      info_key="run_order", ordinal=0))
    ts.order_fields.append(
        OrderField(name="git_sha", info_key="git_sha", ordinal=1))

    ts.cv_order_fields.append(CVOrderField(name="llvm_project_revision",
                                           info_key="run_order", ordinal=0))
    ts.cv_order_fields.append(
        CVOrderField(name="git_sha", info_key="git_sha", ordinal=1))
    ts.cv_order_fields.append(
        CVOrderField(name="parent_commit", info_key="parent_commit",
                     ordinal=2))

    # We are only interested in simple runs, so we expect exactly four fields
    # per test.
    exec_status = SampleField(name="execution_status", type=status_sample_type,
                              info_key=".exec.status")
    cv_exec_status = CVSampleField(name="execution_status",
                                   type=status_sample_type,
                                   info_key=".exec.status")

    ts.sample_fields.append(exec_status)

    ts.sample_fields.append(
        SampleField(name="execution_time", type=real_sample_type,
                    info_key=".exec", status_field=exec_status))
    ts.cv_sample_fields.append(cv_exec_status)
    ts.cv_sample_fields.append(
        CVSampleField(name="execution_time", type=real_sample_type,
                      info_key=".exec", status_field=cv_exec_status))
    session.add(ts)


def initialize_epengine_definition(engine, session):
    initialize_couchbase_definition(engine, session, 'ep-engine', 'EP')


def initialize_memcached_definition(engine, session):
    initialize_couchbase_definition(engine, session, 'memcached', 'Memcached')


###
# Compile Testsuite Definition


def initialize_compile_definition(session):
    # Fetch the sample types.
    real_sample_type = session.query(SampleType) \
        .filter_by(name="Real").first()
    status_sample_type = session.query(SampleType) \
        .filter_by(name="Status").first()

    # Create a test suite compile with "lnt runtest compile".
    ts = TestSuite(name="compile", db_key_name="Compile")

    # Promote some natural information to fields.
    ts.machine_fields.append(MachineField(name="hardware",
                                          info_key="hw.model"))
    ts.machine_fields.append(MachineField(name="os_version",
                                          info_key="kern.version"))

    # The only reliable order currently is the "run_order" field. We will want
    # to revise this over time.
    ts.order_fields.append(OrderField(name="llvm_project_revision",
                                      info_key="run_order", ordinal=0))

    # We expect up to five fields per test, each with a status field.
    for name, type_name in (('user', 'time'),
                            ('sys', 'time'),
                            ('wall', 'time'),
                            ('size', 'bytes'),
                            ('mem', 'bytes')):
        status = SampleField(
            name="%s_status" % (name,), type=status_sample_type,
            info_key=".%s.status" % (name,))
        ts.sample_fields.append(status)
        value = SampleField(
            name="%s_%s" % (name, type_name), type=real_sample_type,
            info_key=".%s" % (name,), status_field=status)
        ts.sample_fields.append(value)

    session.add(ts)


###
# Per-Testsuite Table Schema


def get_base_for_testsuite(test_suite):
    UpdatedBase = declarative_base()
    db_key_name = test_suite.db_key_name

    class Machine(UpdatedBase):
        __tablename__ = db_key_name + '_Machine'
        __table_args__ = {'mysql_collate': 'utf8_bin'}  # For case sensitive compare.
        id = Column("ID", Integer, primary_key=True)
        name = Column("Name", String(256), index=True)

        parameters_data = Column("Parameters", Binary, index=False, unique=False)

        class_dict = locals()
        for item in test_suite.machine_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key %r" %
                                 (name,))

            class_dict[item.name] = item.column = Column(
                item.name, String(256))

    class Order(UpdatedBase):
        __tablename__ = db_key_name + '_Order'

        id = Column("ID", Integer, primary_key=True)

        next_order_id = Column("NextOrder", Integer, ForeignKey(
            "%s.ID" % __tablename__))
        previous_order_id = Column("PreviousOrder", Integer, ForeignKey(
            "%s.ID" % __tablename__))

        class_dict = locals()
        for item in test_suite.order_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key %r" % (
                    item.name,))

            class_dict[item.name] = item.column = Column(
                item.name, String(256))

    class Run(UpdatedBase):
        __tablename__ = db_key_name + '_Run'

        id = Column("ID", Integer, primary_key=True)
        machine_id = Column("MachineID", Integer, ForeignKey(Machine.id),
                            index=True)
        order_id = Column("OrderID", Integer, ForeignKey(Order.id),
                          index=True)
        imported_from = Column("ImportedFrom", String(512))
        start_time = Column("StartTime", DateTime)
        end_time = Column("EndTime", DateTime)
        simple_run_id = Column("SimpleRunID", Integer)

        parameters_data = Column("Parameters", Binary, index=False, unique=False)

        machine = sqlalchemy.orm.relation(Machine)
        order = sqlalchemy.orm.relation(Order)

        class_dict = locals()
        for item in test_suite.run_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key %r" % (item.name))

            class_dict[item.name] = item.column = Column(
                item.name, String(256))

    class CVOrder(UpdatedBase):
        __tablename__ = db_key_name + '_CV_Order'

        id = Column("ID", Integer, primary_key=True)

        class_dict = locals()
        for item in test_suite.cv_order_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key %r" % (item.name))

            class_dict[item.name] = item.column = Column(
                item.name, String(256))

    class CVRun(UpdatedBase):
        __tablename__ = db_key_name + '_CV_Run'

        id = Column("ID", Integer, primary_key=True)
        machine_id = Column("MachineID", Integer, ForeignKey(Machine.id),
                            index=True)
        order_id = Column("OrderID", Integer, ForeignKey(Order.id),
                          index=True)
        imported_from = Column("ImportedFrom", String(512))
        start_time = Column("StartTime", DateTime)
        end_time = Column("EndTime", DateTime)
        simple_run_id = Column("SimpleRunID", Integer)

        parameters_data = Column("Parameters", Binary)

        machine = sqlalchemy.orm.relation(Machine)
        order = sqlalchemy.orm.relation(Order)

        class_dict = locals()
        for item in test_suite.cv_run_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key %r" % (
                    item.name))

            class_dict[item.name] = item.column = Column(
                item.name, String(256))

    class Test(UpdatedBase):
        __tablename__ = db_key_name + '_Test'
        __table_args__ = {'mysql_collate': 'utf8_bin'}
        id = Column("ID", Integer, primary_key=True)
        name = Column("Name", String(256), unique=True, index=True)

    class Sample(UpdatedBase):
        __tablename__ = db_key_name + '_Sample'

        id = Column("ID", Integer, primary_key=True)

        run_id = Column("RunID", Integer, ForeignKey(Run.id))
        test_id = Column("TestID", Integer, ForeignKey(Test.id), index=True)

        run = sqlalchemy.orm.relation(Run)
        test = sqlalchemy.orm.relation(Test)

        class_dict = locals()
        for item in test_suite.sample_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key {}"
                                 .format(item.name))

            if item.type.name == 'Real':
                item.column = Column(item.name, Float)
            elif item.type.name == 'Status':
                item.column = Column(item.name, Integer, ForeignKey(
                    StatusKind.id))
            elif item.type.name == 'Hash':
                continue
            else:
                raise ValueError("test suite defines unknown sample type {}"
                                 .format(item.type.name))

            class_dict[item.name] = item.column

    class CVSample(UpdatedBase):
        __tablename__ = db_key_name + '_CV_Sample'

        id = Column("ID", Integer, primary_key=True)

        run_id = Column("RunID", Integer, ForeignKey(CVRun.id))
        test_id = Column("TestID", Integer, ForeignKey(Test.id), index=True)

        run = sqlalchemy.orm.relation(CVRun)
        test = sqlalchemy.orm.relation(Test)

        class_dict = locals()
        for item in test_suite.cv_sample_fields:
            if item.name in class_dict:
                raise ValueError("test suite defines reserved key {}"
                                 .format(item.name))
            if item.type.name == 'Real':
                item.column = Column(item.name, Float)
            elif item.type.name == 'Status':
                item.column = Column(item.name, Integer, ForeignKey(
                    StatusKind.id))
            elif item.type.name == 'Hash':
                continue
            else:
                raise ValueError("test suite defines unknown sample type {}"
                                 .format(item.type.name))

            class_dict[item.name] = item.column

    sqlalchemy.schema.Index("ix_%s_CVSample_CVRunID_TestID" % db_key_name,
                            CVSample.run_id, CVSample.test_id)

    sqlalchemy.schema.Index("ix_%s_Sample_RunID_TestID" % db_key_name,
                            Sample.run_id, Sample.test_id)

    return UpdatedBase


def initialize_testsuite(lnt_engine, session, name):
    defn = session.query(TestSuite).filter_by(name=name).first()
    assert defn is not None

    # Create all the testsuite database tables. We don't need to worry about
    # checking if they already exist, SA will handle that for us.
    get_base_for_testsuite(defn).metadata.create_all(lnt_engine)


def upgrade(lnt_engine, cb_testsuites):
    # This upgrade script is special in that it needs to handle databases "in
    # the wild" which have contents but existed before versioning.

    # Create a session.
    session = sqlalchemy.orm.sessionmaker(lnt_engine)()

    # If the TestSuite table exists, assume the database is pre-versioning but
    # already has the core initialized.
    if not TestSuite.__table__.exists(lnt_engine):
        initialize_core(lnt_engine, session)

    # Initialise the Couchbase testsuites
    for testsuite in cb_testsuites:
        if (session.query(TestSuite)
                .filter_by(name=testsuite['name']).first() is None):
            initialize_couchbase_definition(
                engine, session, name=testsuite['name'],
                key_name=testsuite['db_key'])

    # Commit the results.
    session.commit()

    # Materialize the test suite tables.
    for testsuite in cb_testsuites:
        try:
            initialize_testsuite(engine, session, testsuite['name'])
        except:
            pass

    session.close()
