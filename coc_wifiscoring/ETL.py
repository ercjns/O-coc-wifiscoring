# ETL.py

import timeit
import json
from defusedxml.ElementTree import parse as defusedETparse

#############################################     
####### XML Soup Helper Methods #############
#############################################

# def getNameFromSoup(S, iofV):
#     if S.name == 'PersonResult' or S.name == 'PersonEntry':
#         if iofV == 2:
#             try:
#                 gn = S.Person.PersonName.Given.string
#             except:
#                 gn = None
#             try:
#                 fn = S.Person.PersonName.Family.string
#             except:
#                 fn = None
#         elif iofV == 3:
#             try:
#                 gn = S.Person.Name.Given.string
#             except:
#                 gn = None
#             try:
#                 fn = S.Person.Name.Family.string
#             except:
#                 fn = None
#         else:
#             raise ValueError
#     else: raise ValueError

#     if (gn != None) and (fn != None):
#         name = gn + ' ' + fn
#     elif (gn != None):
#         name = gn
#     elif (fn != None):
#         name = fn
#     else:
#         name = None
#     return name

# def getClassFromSoup(S, iofV):
#     if S.name == 'ClassResult':    
#         if iofV == 2:
#             try:
#                 cclass = S.ClassShortName.string
#             except:
#                 raise ValueError
#         elif iofV == 3:
#             try:
#                 cclass = S.Class.ShortName.string
#             except:
#                 raise ValueError
#         else:
#             raise ValueError
#     elif S.name == 'PersonEntry':
#         if iofV == 3:
#             try:
#                 cclass = S.Class.Name.string
#             except:
#                 raise ValueError
#         else:
#             raise ValueError
#     else: raise ValueError
#     return cclass

# def getCourseFromSoup(S, iofV):
#     if S.name == 'ClassResult':
#         if iofV == 2:
#             course = None
#         elif iofV == 3:
#             try:
#                 course = S.Course.Name.string
#             except:
#                 raise ValueError
#         else:
#             raise ValueError
#     else: raise ValueError
#     return course
    
# def getClubFromSoup(S, iofV):
#     if S.name == 'PersonResult' or S.name == 'PersonEntry':
#         if iofV == 2:
#             try:
#                 club = S.Person.CountryId.string
#             except:
#                 club = None
#         elif iofV == 3:
#             try:
#                 club = S.Organisation.ShortName.string
#             except:
#                 club = None
#     else: raise ValueError
#     return club

# def getSIcardFromSoup(S, iofV):
#     if S.name == 'PersonEntry':
#         if iofV == 3:
#             try:
#                 sicard = S.ControlCard.string
#             except:
#                 sicard = None
#         else:
#             raise ValueError
#     elif S.name == 'PersonResult':
#         if iofV == 2:
#             sicard = None
#         elif iofV == 3:
#             try:
#                 sicard = S.Result.ControlCard.string
#             except:
#                 sicard = None
#         else:
#             raise ValueError
#     else: raise ValueError
#     return sicard    

# def getSIIDFromSoup(PR, iofV):
#     if iofV == 2:
#         estick = None
#     elif iofV == 3:
#         try:
#             estick = PR.Result.ControlCard.string
#         except:
#             estick = None
#     else:
#         raise ValueError
#     return estick

# def getStartFromSoup(S, iofV):
#     if S.name == 'PersonResult':
#         if iofV == 2:
#             try:
#                 start = S.Result.StartTime.string
#             except:
#                 start = None
#         elif iofV == 3:
#             try:
#                 start = S.Result.StartTime.string
#             except:
#                 start = None
#         else:
#             raise ValueError
#     else: raise ValueError
#     return start

# def getBibFromSoup(S, iofV):
#     if S.name == 'PersonResult':
#         if iofV == 2:
#             bib = None
#         elif iofV == 3:
#             try:
#                 bib = S.Result.BibNumber.string
#             except:
#                 bib = None
#         else:
#             raise ValueError
#     else: raise ValueError
#     return bib

# def getMMMSSFromSoup(S, iofV):
#     if S.name == 'PersonResult':
#         if iofV == 2:
#             try:
#                 mmmss = S.Result.Time.string
#             except:
#                 mmmss = None
#         else:
#             raise ValueError
#     else: raise ValueError
#     return mmmss

# def getTimeFromSoup(S, iofV):
#     if S.name == 'PersonResult':
#         if iofV == 3:
#             try:
#                 time = int(S.Result.Time.string)
#             except:
#                 time = None
#         else:
#             raise ValueError
#     else: raise ValueError
#     return time

# def getFinishFromSoup(S, iofV):
#     if S.name == 'PersonResult':
#         if iofV == 2:
#             try:
#                 finish = S.Result.FinishTime.string
#             except:
#                 finish = None
#         elif iofV == 3:
#             try:
#                 finish = S.Result.FinishTime.string
#             except:
#                 finish = None
#         else:
#             raise ValueError
#     else: raise ValueError
#     return finish

# def getStatusFromSoup(S, iofV):
#     if S.name == 'PersonResult':
#         if iofV == 2:
#             try:
#                 status = S.Result.CompetitorStatus['value']
#             except:
#                 raise NameError
#         elif iofV == 3:
#             try:
#                 status = S.Result.Status.string
#             except:
#                 raise NameError
#         else:
#             raise ValueError
#     else: raise ValueError
#     return status

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

def getNameEtree(PR, nstag_f, nstag_l):
    try:
        first = PR[0][0].find(nstag_f).text
    except:
        first = None
    try:
        last = PR[0][0].find(nstag_l).text
    except:
        last = None
    return '{} {}'.format(first, last).strip()

def getClubShortEtree(PR, nstag):
    try:
        clubcode = PR[1].find(nstag)
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
        'Given':'{http://www.orienteering.org/datastandard/3.0}Given',
        'Family':'{http://www.orienteering.org/datastandard/3.0}Family',
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
                PR_R = PR[2] # <Result> node contains most of the data
                runner = {}
                runner['estick'] = getResultStrEtree(PR_R, iof3tags['ControlCard'])
                runner['start'] = getResultStrEtree(PR_R, iof3tags['StartTime'])
                runner['club'] = getClubShortEtree(PR, iof3tags['ShortName'])
                runner['bib'] = getResultStrEtree(PR_R, iof3tags['BibNumber'])
                runner['name'] = getNameEtree(PR, iof3tags['Given'], iof3tags['Family'])
                runner['class_code'] = CR_ShortName
                runner['course'] = CR_Course
                runner['finish'] = getResultStrEtree(PR_R, iof3tags['FinishTime'])
                runner['status'] = getResultStrEtree(PR_R, iof3tags['Status'])
                runner['time'] = getTimeEtree(PR_R, iof3tags['Time'])
                runner['mmmss'] = timeToMMMSS(runner['time'])

                runners.append(runner)

    return runners, timestamp



# def timewrapper(func, *args, **kwargs):
#     def wrapped():
#         return func(*args, **kwargs)
#     return wrapped


# if __name__ == '__main__':
    

#     smlfile = ''
#     midfile = ''
#     bigfile = '../setupdata/2015_WIOL5.xml'

#     runnersET, timestampET = getRunners(bigfile)
#     runnersBS, timestampBS = getRunners_BS(bigfile)

#     print('eTree: {} \t bSoup: {}'.format(len(runnersET), len(runnersBS)))
#     print('eTree == bSoup? {} (runners)'.format(runnersET == runnersBS))
#     print('eTree == bSoup? {} (timestamp)'.format(timestampET == timestampBS))

#     differences = 0
#     for i in range(len(runnersBS)):
#         if runnersBS[i] == runnersET[i]:
#             continue
#         else:
#             for k in runnersBS[i].keys():
#                 if runnersBS[i][k] == runnersET[i][k]:
#                     continue
#                 else:
#                     print('{} not equal to {}'.format(runnersBS[i][k], runnersET[i][k]))
#             differences += 1
#             print()

#     print('Differences: {} of {}'.format(differences, len(runnersBS)))
    
#     # for r in runnersET[0:10]:
#     #     print r

#     bs2 = timewrapper(getRunners_BS, bigfile)

#     bstime2 = timeit.timeit(bs2, number=10)

#     eT2 = timewrapper(getRunners, bigfile)
    
#     eTtime2 = timeit.timeit(eT2, number=10)

#     print('Beautiful Soup vs ETree')
#     print('lg: {:1.6f} \t {:1.6f}'.format(bstime2, eTtime2))