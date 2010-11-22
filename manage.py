"""
MyCube Vault 1.0.0
Copyright(c) 2010 DLMM Pte Ltd.
licensing@mycube.com
http://mycube.com/vault/license
"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

import unittest2
from flaskext.script import Manager
from settings import create_app
from myvault.database import db
from werkzeug import import_string

SQLALCHEMY_ECHO = True
DEBUG = True

app = create_app(__name__)
manager = Manager(app)

@manager.command
def createall():
    """Create all tables"""
    db.create_all()

@manager.command
def test(target=None, verbosity=0):
    """Run the testsuite"""
    suite = unittest2.TestSuite()
    if target:
        test_mod = import_string(target)
        suite.addTest(unittest2.defaultTestLoader.loadTestsFromModule(test_mod))
    else:
        suite.addTest(unittest2.defaultTestLoader.discover('tests'))

    unittest2.TextTestRunner(verbosity=verbosity).run(suite)


@manager.shell
def make_shell_context():
    db.create_all()
    return dict(app=app, db=db)

if __name__ == "__main__":
    manager.run()
