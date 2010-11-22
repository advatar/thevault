from flask import Flask, url_for
from flaskext.testing import TestCase
from settings import create_app

class FrontpageTest(TestCase):

    def create_app(self):
        app = create_app()
        app.config['TESTING']
        return app

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_frontpage(self):
        response = self.client.get(url_for('base.index'))

        self.assert200(response)

