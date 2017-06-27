# Version 4 of the database adds the bigger_is_better column to StatusField.

import os
import sys

import sqlalchemy


###
# Upgrade TestSuite


def upgrade(engine, _):
    # Add our new column. SQLAlchemy doesn't really support adding a new
    # column to an existing table, so instead of requiring SQLAlchemy-Migrate,
    # just execute the raw SQL.
    try:
        with engine.begin() as trans:
            trans.execute("""
    ALTER TABLE "TestSuiteSampleFields"
    ADD COLUMN "bigger_is_better" INTEGER DEFAULT 0
    """)
            trans.execute("""
            ALTER TABLE "TestSuiteCVSampleFields"
            ADD COLUMN "bigger_is_better" INTEGER DEFAULT 0
            """)
    except:
        pass
