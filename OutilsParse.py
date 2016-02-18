"""
O-Utils-Parse.py.

Imports an IOF xml result snapshot into python data structures

written for python 2.7
(c) 2015 Eric Jones COC Tech Team
"""

from bs4 import BeautifulSoup as BS
import csv


class Runner(object):
    """
    Represents a single-day meet entry/result.
    Handles results as well as tracking starts.
    """
    def __init__(self, estick=None, start=None, info=None, result=None):
        """init."""
        self.estick = estick
        self.start = start
        if (info):
            self.name = info['name']
            self.club = info['club']
            self.cclass = info['cclass']
            self.course = info['course']
            self.bib = info['bib']
        if (result):
            self.finish = result['finish']
            self.mmmss = result['mmmss']
            self.time = result['time']
            self.status = result['status']
        self.position = None
        self.score = None
        self.teamscorer = False
        
class WIOLTeam(object):
    """
    Represents a team of individuals in a WIOL team class at a single meet
    """
    def __init__(self, club, clubfull, cclass, runners, finishers, scorers, score):
        """init."""
        self.club = club
        self.clubfull = clubfull
        self.cclass = cclass
        self.runners = runners # list of Runner objects
        self.finishers = finishers # list, subset of runners
        self.scorers = scorers # list, subset of finishers
        self.score = score
        self.position = None
        return

class SeasonResult(object):
    """
    Represents a result for an individual over the season.
    """
    def __init__(self, name, bib, club, clubfull):
        self.name = name
        self.bib = bib
        self.club = club
        self.clubfull = clubfull
        self.scores = {}
        self.score = 0
        self.position = None
        return
        
    def _calcSeasonScore(self):
        seasonscore = 0
        scorelist = self.scores.values()
        scorelist.sort(key=lambda x: -x)
        for i in range(4):
            try:
                seasonscore += scorelist[i]
            except:
                break
        self.score = seasonscore
        return
    
    # verb: insert
    def insertResult(self, meet, score):
        self.scores[meet] = score
        self._calcSeasonScore()
        return
        
class TeamSeasonResult(object):
    """
    Represents a result for team over the season.
    """
    def __init__(self, club, clubfull):
        self.club = club
        self.clubfull = clubfull
        self.scores = {}
        self.score = 0
        self.position = None
        return
        
    def _calcSeasonScore(self):
        seasonscore = 0
        scorelist = self.scores.values()
        scorelist.sort(key=lambda x: -x)
        for i in range(4):
            try:
                seasonscore += scorelist[i]
            except:
                break
        self.score = seasonscore
        return

    def insertResult(self, meet, score):
        self.scores[meet] = score
        self._calcSeasonScore()
        return


def getURLs(file):
    """return dict of urls to meet specific pages"""
    urls = {}
    with open(file) as f:
        reader = list(csv.DictReader(f))
        for meet in reader:
            urls[meet['meet']] = meet
    return urls


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

def getClassFromSoup(CR, iofV):
    if iofV == 2:
        try:
            cclass = CR.ClassShortName.string
        except:
            raise ValueError
    elif iofV == 3:
        try:
            cclass = CR.Class.ShortName.string
        except:
            raise ValueError
    else:
        raise ValueError
    return cclass
    
def getCourseFromSoup(CR, iofV):
    if iofV == 2:
        course = None
    elif iofV == 3:
        try:
            course = CR.Course.Name.string
        except:
            raise ValueError
    else:
        raise ValueError
    return course

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


def getFinishFromSoup(PR, iofV):
    if iofV == 2:
        try:
            finish = PR.Result.FinishTime.string
        except:
            finish = None
    elif iofV == 3:
        try:
            finish = PR.Result.FinishTime.string
        except:
            finish = None
    else:
        raise ValueError
    return finish


def getMMMSSFromSoup(PR, iofV):
    if iofV == 2:
        try:
            mmmss = PR.Result.Time.string
        except:
            mmmss = None
    else:
        raise ValueError
    return mmmss


def getTimeFromSoup(PR, iofV):
    if iofV == 3:
        try:
            time = int(PR.Result.Time.string)
        except:
            time = None
    else:
        raise ValueError
    return time


def getStartFromSoup(PR, iofV):
    if iofV == 2:
        try:
            start = PR.Result.StartTime.string
        except:
            start = None
    elif iofV == 3:
        try:
            start = PR.Result.StartTime.string
        except:
            start = None
    else:
        raise ValueError
    return start


def getStatusFromSoup(PR, iofV):
    if iofV == 2:
        try:
            status = PR.Result.CompetitorStatus['value']
        except:
            raise NameError
    elif iofV == 3:
        try:
            status = PR.Result.Status.string
        except:
            raise NameError
    else:
        raise ValueError
    return status


def getSIIDFromSoup(PR, iofV):
    if iofV == 2:
        estick = None
    elif iofV == 3:
        try:
            estick = PR.Result.ControlCard.string
        except:
            estick = None
    else:
        raise ValueError("Invalid iofVersion")
    return estick
    
def getBibFromSoup(PR, iofV):
    if iofV == 2:
        bib = None
    elif iofV == 3:
        try:
            bib = PR.Result.BibNumber.string
        except:
            bib = None
    else:
        raise ValueError("Invalid iofVersion")
    return bib


def getRunners(file):
    """
    Import XML of runners and info into python structures.

    Input: file path to xml
    Return: List of Runner objects.
    Caller will need to handle any merging of runner objects as needed.
    """
    runners = []
    with open(file, 'r') as fn:
        soup = BS(fn, 'xml')
    
    v = soup.ResultList.find_all('IOFVersion')
    if len(v) > 0:
        iofV = 2
    else:
        iofV = 3

    cclasses = soup.ResultList.find_all('ClassResult')
    for c in cclasses:
        cclass = getClassFromSoup(c, iofV)
        course = getCourseFromSoup(c, iofV)
        for PR in c.find_all("PersonResult"):
            estick = getSIIDFromSoup(PR, iofV)
            start = getStartFromSoup(PR, iofV)
            club = getClubFromSoup(PR, iofV)
            bib = getBibFromSoup(PR, iofV) if cclass[0] == 'W' else None
            info = {"name": getNameFromSoup(PR, iofV),
                    "club": club,
                    "cclass": cclass,
                    "course": course, 
                    "bib": bib
                    }
            if iofV == 2:
                mmmss = getMMMSSFromSoup(PR, iofV)
                time = timeToInt(mmmss)
            elif iofV == 3:
                time = getTimeFromSoup(PR, iofV)
                mmmss = timeToMMMSS(time)
            result = {"finish": getFinishFromSoup(PR, iofV),
                      "mmmss": mmmss,
                      "time": time,
                      "status": getStatusFromSoup(PR, iofV),
                      }
            runners.append(Runner(estick, start, info, result))
    
    return runners


def assignPositions(runners):
    """
    Assign places (1st, 2nd, 3rd) to a set of Runners based on time.

    Input: List of Runner objects
    Return: List of Runner objects with place assigned.
    """
    # make sure we only have runners from a single cclass
    if len(set([r.cclass for r in runners])) > 1:
        raise ValueError("Runner list should only contain a single class.")

    finished = [r for r in runners if r.status == 'OK']
    finished.sort(key=lambda r: r.time)
    nextposition = 1
    for i in range(len(finished)):
        if i == 0:
            finished[i].position = nextposition
        elif finished[i].time == finished[i-1].time:
            finished[i].position = finished[i-1].position
        else:
            finished[i].position = nextposition
        nextposition += 1
    
    return runners


def assignScore(runners, algo):
    """
    Assign score (100, 95, 92 or similar) based on the given algorithm.

    Parameters: List of Runner objects (places should be assigned)
           String algorithm name
    Return: List of Runner objects with score assigned.
    """
    if len(set([r.cclass for r in runners])) > 1:
        raise ValueError("Runner list should only contain a single class.")

    if algo == "COC":  # Cascade OC WIOL points
        for r in runners:
            if r.cclass in ['1', '3', '7', '8G']:
                r.score = None
            if r.position is None:
                if r.status in ['DidNotFinish', 'MissingPunch', 'Disqualified']:
                    r.score = 0
                else:
                    r.score = None
            elif r.position == 1:
                r.score = 100
            elif r.position == 2:
                r.score = 95
            elif r.position == 3:
                r.score = 92
            else:
                r.score = 100 - 6 - int(r.position)

        return runners

    elif algo == "ISOC":  # Interscholatics, see USOF rule A.36.5
        awt = sum([r.time for r in runners if r.position <= 3]) / 3.0

        for r in runners:
            if r.status == "OK":
                r.score = 60*r.time / awt
            else:
                r.score = 10 + 60*(3*60*60) / awt

        return runners

    else:
        raise ValueError("Algorithm not recognized - try 'COC' or 'ISOC'")


def calcTeams(runners, algo):
    """
    Create teams and assign team score. Does NOT assign places to teams.
    
    Algos are "COC" or "ISOC". Input should be a list of ALL runners.
    This is not limited to a single class, as COC/WIOL requires team to be
    calculated across classes (boys and girls together) for Middle School.
    """
    if algo == "COC":
        WIOLcclasses = ['W2', 'W3F', 'W4M', 'W5M', 'W6F', 'W6M']
        clubdict = OCC.ClubCodes('ClubCodes.csv')
        teams = []
        for c in WIOLcclasses:
            if c == "W2":
                classRunners = [r for r in runners if (r.cclass == 'W2F' or r.cclass == 'W2M')]
            else:
                classRunners = [r for r in runners if (r.cclass == c)]
                
            classTeams = set([r.club for r in classRunners])
            for club in classTeams:
                teamRunners = [r for r in classRunners if (r.club == club) and (r.status not in ['NotCompeting', 'DidNotStart'])]
                if len(teamRunners) == 0:
                    continue
                teamFinishers = [r for r in teamRunners if (r.status == "OK")]
                teamFinishers.sort(key=lambda x: -x.score) # also sort by time(?)
                teamScorers = []
                for i in range(3):
                    try:
                        teamFinishers[i].teamscorer = True
                        teamScorers.append(teamFinishers[i])
                    except:
                        break
                teamScore = sum([r.score for r in teamScorers])
                teams.append(WIOLTeam(club,
                                      clubdict.getClubFull(club),
                                      c,
                                      teamRunners,
                                      teamFinishers,
                                      teamScorers,
                                      teamScore))
        return teams

    elif algo == "ISOC":
        print("Sorry, ISOC scoring not yet implemented")
        return

    else:
        raise ValueError("Sorry, didn't recognize that algorithm")
        return

def assignTeamPositions(teams, algo):
    """
    assign Position to a team in a team class. Team-tie breaks happen here
    """
    if algo == "COC":
        WIOLcclasses = ['W2', 'W3F', 'W4M', 'W5M', 'W6F', 'W6M']
        for c in WIOLcclasses:
            classTeams = [t for t in teams if t.cclass == c]
            classTeams.sort(key=lambda x: -x.score)
            
            nextposition = 1
            for i in range(len(classTeams)):
                if i == 0:
                    # first place
                    classTeams[i].position = nextposition
                    
                elif classTeams[i].score == classTeams[i-1].score:
                    # team tie-breaks
                    a = classTeams[i-1]
                    b = classTeams[i]
                    # make sure they're in order...
                    a.scorers.sort(key=lambda x: -x.score)
                    b.scorers.sort(key=lambda x: -x.score)
                    for i in range(3):
                        try:
                            tiebreakerA = a.scorers[i].score
                        except IndexError:
                            tiebreakerA = 0
                        try:
                            tiebreakerB = b.scorers[i].score
                        except IndexError:
                            tiebreakerB = 0

                        if tiebreakerA > tiebreakerB:
                            # a wins, so assign the next position to b
                            b.position = nextposition
                            break
                        elif tiebreakerB > tiebreakerA:
                            # b wins, so take a's position and assign a the next position
                            b.position = a.position
                            a.position = nextposition
                            break
                        else:
                            continue
                            
                    if b.position == None:
                        # actually a tie
                        b.position = a.position
                else:
                    classTeams[i].position = nextposition
                nextposition += 1
        return
                
    elif algo == "ISOC":
        print("Sorry, ISOC scoring not yet implemented")
        return

    else:
        raise ValueError("Sorry, didn't recognize that algorithm")
        return            
    
def createSeasonResults(meetdata):
    """
    Create season result objects for individuals and teams
    
    Input value is {'WIOL1':{'indiv':[runners],'teams':[teams]}, ... }
    """
    seasonindvs = {}
    seasonteams = {}
    
    for meet, results in meetdata.items():
        # season individuals:
        for runner in results['indv']:
            recorded = False
            if runner.cclass in ['1','3','7','8G']:
                continue # skip public classes
            if runner.status in ['NotCompeting']:
                continue # skip NC, but MSP, DSQ and DNF get 0s so they stay.
                
            seasonclass = seasonindvs.setdefault(runner.cclass, [])
            # TODO refactor - ALWAYS inserting a new result
            sp = None
            for seasonperson in seasonclass:
                if runner.bib: #for WIOL match on bib
                    if seasonperson.bib == runner.bib:
                        sp = seasonperson
                        break
                else: #for public match on name, bibs exist but are not consistent.
                    if seasonperson.name == runner.name:
                        sp = seasonperson
                        break
            if not sp:
                # no match, create a new SeasonResult
                sp = SeasonResult(runner.name, runner.bib, runner.club, runner.clubfull)
                seasonclass.append(sp)
            
            sp.insertResult(meet, runner.score)
                        
            # for seasonperson in seasonclass:
                # if (seasonperson.name == runner.name) and (seasonperson.club == runner.club):
                    # # match, add to results
                    # seasonperson.addResult(meet, runner.score)
                    # recorded = True
                    # break
            # if not recorded:
                # # no match found, add a new season result in the class for this runner.
                # sp = SeasonResult(runner.name, runner.bib, runner.club, runner.clubfull)
                # sp.addResult(meet, runner.score)
                # seasonclass.append(sp)
                # recorded = True # this is not needed?
        
        # season teams
        for team in results['teams']:
            # recorded = False
            seasonteamresults = seasonteams.setdefault(team.cclass, []) #this is a table in the results output
            
            st = None
            for seasonteam in seasonteamresults:
                # TODO can we grab it with an index rather than loopin through the list?
                # Find the right team if it exists already in season results
                if (seasonteam.club == team.club):
                    st = seasonteam
                    break
            if not st:
                # no match found, create new TeamSeasonResult:
                st = TeamSeasonResult(team.club, team.clubfull)
                seasonteamresults.append(st)
                
            st.insertResult(meet, team.score)
        
    return seasonindvs, seasonteams
    
    
def assignSeasonPositions(seasonResults):
    """
    assign obj.position for SeasonResult or TeamSeasonResult
    input is {"cclass":[SeasonResults], "cclass":[SeasonResults], ...}
    """
    for cclass, entries in seasonResults.items():
        entries.sort(key=lambda x: -x.score)

        entries[0].position = 1
        nextposition = 1
        
        for i in range(len(entries)):
            if i == 0:
                # First place!
                entries[i].position = nextposition
            elif entries[i].score == entries[i-1].score:
                # break the tie
                a = entries[i-1]
                b = entries[i]
                aScores = sorted(a.scores.values(), key=lambda x: -x)
                bScores = sorted(b.scores.values(), key=lambda x: -x)
                races = max(len(aScores), len(bScores))
                for i in range(races):
                    try:
                        tiebreakerA = aScores[i]
                    except IndexError:
                        tiebreakerA = 0
                    try:
                        tiebreakerB = bScores[i]
                    except IndexError:
                        tiebreakerB = 0

                    if tiebreakerA > tiebreakerB:
                        # a wins, so assign the next position to b
                        b.position = nextposition
                        break
                    elif tiebreakerB > tiebreakerA:
                        # b wins, so take a's position and assign a the next position
                        b.position = a.position
                        a.position = nextposition
                        break
                    else:
                        continue     
                if b.position == None:
                    # actually a tie
                    b.position = a.position   
            else:
                # assign the next position...
                entries[i].position = nextposition
                
            nextposition += 1 # always increment so ties skip the next place.

    return seasonResults
    
    