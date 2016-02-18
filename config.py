from os.path import abspath, dirname, join
from os import environ

_cwd = dirname(abspath(__file__))

DEBUG = True

PORT = 80 if environ.get('PORT') is None else environ['PORT']

SECRET_KEY = 'this-is-a-poor-place-to-store-my-secret-key'
if environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'wifiscoring.db')
else:
    SQLALCHEMY_DATABASE_URI = environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = True
#SQLALCHEMY_ECHO = True