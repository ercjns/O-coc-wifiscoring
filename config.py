from os.path import abspath, dirname, join

_cwd = dirname(abspath(__file__))

DEBUG = True

SECRET_KEY = 'this-is-a-poor-place-to-store-my-secret-key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'wifiscoring.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True
#SQLALCHEMY_ECHO = True