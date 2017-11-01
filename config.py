from os.path import abspath, dirname, join
from os import environ

_cwd = dirname(abspath(__file__))

# config.py

DEBUG = False
TESTING = False
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
