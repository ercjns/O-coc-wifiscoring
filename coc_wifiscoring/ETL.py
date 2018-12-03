# ETL.py

import timeit
import json
from defusedxml.ElementTree import parse as defusedETparse

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
    # return f['clubs']
    return f
    
def cclassjson(file):
	""" returns array of {'abbr':   u'8M'
                          'name':   u'Long Advanced Men'
                          'course': 8
                          'public': True
                          'scored': True }
    """
	f = json.load(file)
	return f['classes']

def classCSV(filehandle):
    ''' returns array of classinfo dictionaries '''
    classes = []
    # with open(file, 'r') as f:
    #     for line in file:
    for line in filehandle:
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
    
def eventsTSV(file):
    ''' returns array of eventinfo dictionaries '''
    events = []
    with open(file, 'r') as f:
        for line in f:
            props = line.split('\t')
            if props[0] == 'event_code':
                continue # skip header row
            if len(props) != 5:
                raise ValueError
            eventinfo = {}
            eventinfo['event_code'] = props[0]
            eventinfo['event_name'] = props[1]
            eventinfo['date'] = props[2]
            eventinfo['venue'] = props[3]
            eventinfo['description'] = props[4]
            events.append(eventinfo)
    return events
    
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

#############################################
####### XML eTree Helper Methods ############
#############################################

def getCreateTimeEtree(RL):
    date, hmstz = RL.get('createTime').split('T')
    hms = hmstz.split('.')[0]
    timestamp = '{} {}'.format(date, hms)
    return timestamp

def getClassShortEtree(CR, nstag):
    try:
        classShortName = CR[0].find(nstag)
        return classShortName.text
    except:
        return None

def getClassCourseEtree(CR, nstag):
    try:
        course = CR[1].find(nstag)
        return course.text
    except:
        return None

def getNameEtree(PR, nstags):
    try:
        first = PR.find(nstags['Person']).find(nstags['Name']).find(nstags['Given']).text
    except:
        first = None
    try:
        last = PR.find(nstags['Person']).find(nstags['Name']).find(nstags['Family']).text
    except:
        last = None
    return u'{} {}'.format(first, last).strip()

def getClubShortEtree(PR, nstags):
    try:
        clubcode = PR.find(nstags['Org']).find(nstags['ShortName'])
        return clubcode.text
    except:
        return None

def getTimeEtree(PR_R, nstag):
    try:
        status = PR_R.find(nstag)
        return int(status.text)
    except:
        return None

def getResultStrEtree(PR_R, nstag):
    try: 
        card = PR_R.find(nstag)
        return card.text
    except:
        return None

def getRunners(file):
    """
    Input: file path to XMLv3 *now only supports v3!*
    Return: List of runner dictionaries, along with the file's timestamp
    """
    iof3tags = {
        'CR':'{http://www.orienteering.org/datastandard/3.0}ClassResult',
        'ShortName':'{http://www.orienteering.org/datastandard/3.0}ShortName',
        'Name':'{http://www.orienteering.org/datastandard/3.0}Name',
        'PR':'{http://www.orienteering.org/datastandard/3.0}PersonResult',
        'Person':'{http://www.orienteering.org/datastandard/3.0}Person',
        'Given':'{http://www.orienteering.org/datastandard/3.0}Given',
        'Family':'{http://www.orienteering.org/datastandard/3.0}Family',
        'Org':'{http://www.orienteering.org/datastandard/3.0}Organisation',
        'Result':'{http://www.orienteering.org/datastandard/3.0}Result',
        'ControlCard':'{http://www.orienteering.org/datastandard/3.0}ControlCard',
        'StartTime':'{http://www.orienteering.org/datastandard/3.0}StartTime',
        'FinishTime':'{http://www.orienteering.org/datastandard/3.0}FinishTime',
        'Time':'{http://www.orienteering.org/datastandard/3.0}Time',
        'BibNumber':'{http://www.orienteering.org/datastandard/3.0}BibNumber',
        'Status':'{http://www.orienteering.org/datastandard/3.0}Status',
        
    }

    runners = []
    with open(file, 'r') as fn:
        tree = defusedETparse(fn)
        root = tree.getroot()

        timestamp = getCreateTimeEtree(root)

        for CR in root.iter(iof3tags['CR']):
            CR_ShortName = getClassShortEtree(CR, iof3tags['ShortName'])
            CR_Course = getClassCourseEtree(CR, iof3tags['Name'])

            for PR in CR.iter(iof3tags['PR']):
                try:
                    PR_R = PR.find(iof3tags['Result'])
                except:
                    continue
                runner = {}
                runner['estick'] = getResultStrEtree(PR_R, iof3tags['ControlCard'])
                runner['start'] = getResultStrEtree(PR_R, iof3tags['StartTime'])
                runner['club'] = getClubShortEtree(PR, iof3tags)
                runner['bib'] = getResultStrEtree(PR_R, iof3tags['BibNumber'])
                runner['name'] = getNameEtree(PR, iof3tags)
                runner['class_code'] = CR_ShortName
                runner['course'] = CR_Course
                runner['finish'] = getResultStrEtree(PR_R, iof3tags['FinishTime'])
                runner['status'] = getResultStrEtree(PR_R, iof3tags['Status'])
                runner['time'] = getTimeEtree(PR_R, iof3tags['Time'])
                runner['mmmss'] = timeToMMMSS(runner['time'])

                runners.append(runner)

    return runners, timestamp
