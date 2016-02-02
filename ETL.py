# ETL.py

import json

def clubcodejson(file):
	""" returns array of {'abbr':u'COC'; 'name':u'Cascade'} """
	f = json.load(file)
	return f['clubs']
    
def cclassjson(file):
	""" returns array of {'abbr':   u'8M'
                          'name':   u'Long Advanced Men'
                          'course': 8
                          'public': True
                          'scored': True }
    """
	f = json.load(file)
	return f['classes']