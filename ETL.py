# ETL.py

import json
from bs4 import BeautifulSoup as BS

#############################################     
####### XML Soup Helper Methods #############
#############################################

def getNameFromSoup(S, iofV):
    if S.name == 'PersonResult' or S.name == 'PersonEntry':
        if iofV == 2:
            try:
                gn = S.Person.PersonName.Given.string
            except:
                gn = None
            try:
                fn = S.Person.PersonName.Family.string
            except:
                fn = None
        elif iofV == 3:
            try:
                gn = S.Person.Name.Given.string
            except:
                gn = None
            try:
                fn = S.Person.Name.Family.string
            except:
                fn = None
        else:
            raise ValueError
    else: raise ValueError

    if (gn != None) and (fn != None):
        name = gn + ' ' + fn
    elif (gn != None):
        name = gn
    elif (fn != None):
        name = fn
    else:
        name = None
    return name

def getClassFromSoup(S, iofV):
    if S.name == 'ClassResult':    
        if iofV == 2:
            try:
                cclass = S.ClassShortName.string
            except:
                raise ValueError
        elif iofV == 3:
            try:
                cclass = S.Class.ShortName.string
            except:
                raise ValueError
        else:
            raise ValueError
    elif S.name == 'PersonEntry':
        if iofV == 3:
            try:
                cclass = S.Class.Name.string
            except:
                raise ValueError
        else:
            raise ValueError
    else: raise ValueError
    return cclass

def getCourseFromSoup(S, iofV):
    if S.name == 'ClassResult':
        if iofV == 2:
            course = None
        elif iofV == 3:
            try:
                course = S.Course.Name.string
            except:
                raise ValueError
        else:
            raise ValueError
    else: raise ValueError
    return course
    
def getClubFromSoup(S, iofV):
    if S.name == 'PersonResult' or S.name == 'PersonEntry':
        if iofV == 2:
            try:
                club = S.Person.CountryId.string
            except:
                club = None
        elif iofV == 3:
            try:
                club = S.Organisation.ShortName.string
            except:
                club = None
    else: raise ValueError
    return club

def getSIcardFromSoup(S, iofV):
    if S.name == 'PersonEntry':
        if iofV == 3:
            try:
                sicard = S.ControlCard.string
            except:
                sicard = None
        else:
            raise ValueError
    elif S.name == 'PersonResult':
        if iofV == 2:
            sicard = None
        elif iofV == 3:
            try:
                sicard = S.Result.ControlCard.string
            except:
                sicard = None
        else:
            raise ValueError
    else: raise ValueError
    return sicard    

def getSIIDFromSoup(PR, iofV):
    if iofV == 2:
        estick = None
    elif iofV == 3:
        try:
            estick = PR.Result.ControlCard.string
        except:
            estick = None
    else:
        raise ValueError
    return estick

def getStartFromSoup(S, iofV):
    if S.name == 'PersonResult':
        if iofV == 2:
            try:
                start = S.Result.StartTime.string
            except:
                start = None
        elif iofV == 3:
            try:
                start = S.Result.StartTime.string
            except:
                start = None
        else:
            raise ValueError
    else: raise ValueError
    return start

def getBibFromSoup(S, iofV):
    if S.name == 'PersonResult':
        if iofV == 2:
            bib = None
        elif iofV == 3:
            try:
                bib = S.Result.BibNumber.string
            except:
                bib = None
        else:
            raise ValueError
    else: raise ValueError
    return bib
    
def getMMMSSFromSoup(S, iofV):
    if S.name == 'PersonResult':
        if iofV == 2:
            try:
                mmmss = S.Result.Time.string
            except:
                mmmss = None
        else:
            raise ValueError
    else: raise ValueError
    return mmmss


def getTimeFromSoup(S, iofV):
    if S.name == 'PersonResult':
        if iofV == 3:
            try:
                time = int(S.Result.Time.string)
            except:
                time = None
        else:
            raise ValueError
    else: raise ValueError
    return time
    
def getFinishFromSoup(S, iofV):
    if S.name == 'PersonResult':
        if iofV == 2:
            try:
                finish = S.Result.FinishTime.string
            except:
                finish = None
        elif iofV == 3:
            try:
                finish = S.Result.FinishTime.string
            except:
                finish = None
        else:
            raise ValueError
    else: raise ValueError
    return finish
    
def getStatusFromSoup(S, iofV):
    if S.name == 'PersonResult':
        if iofV == 2:
            try:
                status = S.Result.CompetitorStatus['value']
            except:
                raise NameError
        elif iofV == 3:
            try:
                status = S.Result.Status.string
            except:
                raise NameError
        else:
            raise ValueError
    else: raise ValueError
    return status

def timeToInt(timestring):
    """convert HH:MM:SS or MMM:SS to integer seconds."""
    if timestring == None or timestring == '--:--':
        return None
    minutes, seconds = timestring.rsplit(':', 1)
    try:
        hours, minutes = minutes.rsplit(':', 1)
    except:
        hours = 0
    time = int(hours)*60*60 + int(minutes)*60 + int(seconds)
    return time

def timeToMMMSS(timeint):
    """Convert int seconds to MMM:SS string."""
    if timeint == None:
        return '--:--'
    minutes, seconds = divmod(timeint, 60)
    m, s = str(minutes), str(seconds)
    if len(s) < 2:
        s = "0" + s
    return m + ":" + s

    
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

def classCSV(file):
    ''' returns array of classinfo dictionaries '''
    classes = []
    with open(file, 'r') as f:
        for line in f:
            props = line.split(',')
            if props[0] == 'class_code':
                continue # skip header row
            if len(props) != 8:
                raise ValueError
            classinfo = {}
            classinfo['class_code'] = props[0]
            classinfo['class_name'] = props[1]
            classinfo['is_scored'] = True if props[2] == 'TRUE' else False
            classinfo['score_method'] = props[3]
            classinfo['is_multi_scored'] = True if props[4] == 'TRUE' else False
            classinfo['multi_score_method'] = props[5]
            classinfo['is_team_class'] = True if props[6] == 'TRUE' else False
            classinfo['team_classes'] = props[7]
            classes.append(classinfo)
    return classes
    
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
    
def getRunners(file):
    """
    Import XML of runners and info into python structures.

    Input: file path to xml
    Return: List of dictionaries representing runners
    Caller will need to handle any merging of runner objects as needed.
    """
    runners = []
    with open(file, 'r') as fn:
        soup = BS(fn, 'xml')
    
    v = soup.ResultList.find_all('IOFVersion')
    if len(v) > 0:
        # TODO: Fix this conditional to be readable. This makes no sense.
        iofV = 2
    else:
        iofV = 3

    cclasses = soup.ResultList.find_all('ClassResult')
    for c in cclasses:
        class_code = getClassFromSoup(c, iofV)
        course = getCourseFromSoup(c, iofV)
        for PR in c.find_all("PersonResult"):
            runner = {}
            runner['estick'] = getSIcardFromSoup(PR, iofV)
            runner['start'] = getStartFromSoup(PR, iofV)
            runner['club'] = getClubFromSoup(PR, iofV)
            runner['bib'] = getBibFromSoup(PR, iofV)
            runner['name'] = getNameFromSoup(PR, iofV)
            runner['class_code'] = class_code
            runner['course'] = course
            runner['finish'] = getFinishFromSoup(PR, iofV)
            runner['status'] = getStatusFromSoup(PR, iofV)
            if iofV == 2:
                runner['mmmss'] = getMMMSSFromSoup(PR, iofV)
                runner['time'] = timeToInt(runner['mmmss'])
            elif iofV == 3:
                runner['time'] = getTimeFromSoup(PR, iofV)
                runner['mmmss'] = timeToMMMSS(runner['time'])
            runners.append(runner)
    
    return runners
