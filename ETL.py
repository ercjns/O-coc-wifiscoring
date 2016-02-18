# ETL.py

import json
from bs4 import BeautifulSoup as BS

#############################################     
####### XML Soup Helper Methods #############
#############################################

def getNameFromSoup(PR, iofV):
    if iofV == 2:
        try:
            gn = PR.Person.PersonName.Given.string
        except:
            gn = None
        try:
            fn = PR.Person.PersonName.Family.string
        except:
            fn = None
    elif iofV == 3:
        try:
            gn = PR.Person.Name.Given.string
        except:
            gn = None
        try:
            fn = PR.Person.Name.Family.string
        except:
            fn = None
    else:
        raise ValueError

    if (gn != None) and (fn != None):
        name = gn + ' ' + fn
    elif (gn != None):
        name = gn
    elif (fn != None):
        name = fn
    else:
        name = None
    return name

def getClassFromSoup(PE, iofV):
    if iofV == 3:
        try:
            cclass = PE.Class.Name.string
        except:
            raise ValueError
    else:
        raise ValueError
    return cclass
    
def getClubFromSoup(PR, iofV):
    if iofV == 2:
        try:
            club = PR.Person.CountryId.string
        except:
            club = None
    elif iofV == 3:
        try:
            club = PR.Organisation.ShortName.string
        except:
            club = None
    else:
        raise ValueError
    return club

def getSIcardFromSoup(PE, iofV):
    if iofV == 3:
        try:
            sicard = PE.ControlCard.string
        except:
            sicard = None
    else:
        raise ValueError("Invalid iofVersion")
    return sicard    
    
    
    
#############################################     
#######       ETL Methods       #############
#############################################



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
    
def entriesXML3(file):
    """ returns array of entry dicts """
    entries = []
    with open(file, 'r') as f:
        soup = BS(f, 'xml')
        person_entries = soup.EntryList.find_all('PersonEntry')
        
        for p in person_entries:
            entry = {}
            entry['name'] = getNameFromSoup(p, 3)
            entry['cclass'] = getClassFromSoup(p, 3)
            entry['club'] = getClubFromSoup(p, 3)
            entry['sicard'] = getSIcardFromSoup(p, 3)
            entries.append(entry)
    return entries
