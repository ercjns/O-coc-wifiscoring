# ETL.py

import json

def clubcodejson(file):
	""" returns array of {'abbr':u'COC'; 'name':u'Cascade'} """
	f = json.load(file)
	return f['clubs']