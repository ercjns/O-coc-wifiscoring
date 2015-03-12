'''
TicketDataToXML.py

Intended to translate data from an OORG split ticket into IOF compliant XML

written for python 2.7
(c) 2014 Eric Jones COC Tech Team
'''

from lxml import etree
from lxml.builder import E
from datetime import datetime
import os
import re
import sys
import requests



class OORGdownload(object):
    def __init__(self, file):
        '''
        class for processing a printout created from a download event in OORG
        INPUT
            <string> file - file location of the OORG printout using format splits-ticket_XML.spf
        '''
        self.file = file
        self.d = self.readTicket(self.file)
        self.d['iofFinish'] = next(r[1] for r in self.d['SplitTimes'] if r[0]=="Finish")
        self.d['iofRunResult'] = self._expandRunResult(self.d['RunResult'])
        self.xml = self._toXML()

    def _toXML(self):
        '''
        define an XML document to the iof 3.0 datastandard. This is a delta type ResultList message
        '''

        doc = (
        E.ResultList(
            E.Event(E.Name("HARD CODE")),
            E.ClassResult(
                E.Class(E.Name(self.d['RunClass'])),
                E.Course(E.Id(self.d['RunCourse']), E.Name("MISSING")),
                E.PersonResult(
                    E.Person(
                        E.Id(self.d['CompId']),
                        E.Name(
                            E.Family("SKIP"),
                            E.Given(self.d['CompName'])),
                            ),
                    E.Organisation(
                        E.Name(self.d['ClubName']),
                        E.ShortName(self.d['ClubShort'])),
                    E.Result(
                        E.BibNumber(self.d['RunStartNo']),
                        E.StartTime("%s WRONGFORMAT" % self.d['RunStartTime']),
                        E.Time(self.d['iofFinish']),
                        E.Status(self.d['iofRunResult']),
                        #SplitTime elements added in this position via code below....
                        #Course here should be used if there are individual courses for each competitor.
                        E.ControlCard(self.d['RunECard']),
                    type="PersonRaceResult"
                    )
                )
            ),
            xmlns="http://www.orienteering.org/datastandard/3.0",
            iofVersion="3.0",
            createTime=datetime.now().isoformat(),
            creator="COC Tech Team",
            status="delta"
        ))

        #add the SplitTime elements to the doc
        for p in self.d['SplitTimes']:
            if p[2] in ["OK", "ADDITIONAL"]:
                #if p[0] in ["Finish"]: continue
                splitdoc = E.SplitTime(E.ControlCode(p[0]), E.Time(p[1]), E.Status(p[2]))

            elif p[2] == "MISSING":
                splitdoc = E.SplitTime(E.ControlCode(p[0]), E.Status(p[2]))
            else:
                raise(TypeError, "Unrecognised Split Time")

            el = doc.find(".//ControlCard")
            if el.text == self.d['RunECard']: #probably not needed...
                el.addprevious(splitdoc)

        return doc

    def readTicket(self, filename):
        '''
        return a dictionary of key value pairs for all data supplied in the OORG intermediate ticket
        INPUT:
            <string> filename - path to "printed" ticket
        OUTPUT:
            <dict> d - dictionary of oorg values
        '''
        d = {}
        with open(filename, 'r') as f:
            #Read the OORG key value pairs
            for line in f:
                if line.startswith("SplitTimes"): break

                line = line.partition(' ')
                k = line[0]
                if k.endswith('\n'): k = k[:-1]
                v = line[2].strip()

                if (k != ''):
                    d[k] = v

            #Read the SplitTimes, Missing punches
            splits = self._readSplitTimes(f)
            d["SplitTimes"] = splits

        return(d)

    def _readSplitTimes(self, openfileobject):
        '''
        return a list of 3-tuples (code, time, status) for all punches and missing punches
        '''
        #OK:         [order,     code,   time, split, [+], behind]
        #Finish:     ["Finish:", time,   split]
        #Additional: [code,      time,   split]
        #Missing:    ["Missing", order, "code", code]
        #OK in MSP   [order*,    code,   time, split]

        file = openfileobject
        splits = []

        for line in file:
            l = line.split()
            if len(l) < 2: continue

            if l[0] == "Finish:":
                punch = ("Finish", self.timeToSeconds(l[1]), "OK")
                splits.append(punch)

            elif l[0] == "Missing:":
                punch = (l[3], '', "MISSING")
                splits.append(punch)

            elif (len(l) == 3) and (l[0].isdigit()) and (self.isTime(l[1])):
                punch = (l[0], self.timeToSeconds(l[1]), "ADDITIONAL")
                splits.append(punch)

            elif (len(l) >= 5) and (l[0].isdigit()) and (l[1].isdigit) and (self.isTime(l[2])):
                punch = (l[1], self.timeToSeconds(l[2]), "OK")
                splits.append(punch)

            elif (len(l) == 4) and (l[1].isdigit()) and (self.isTime(l[2])) and (self.isTime(l[3])):
                punch = (l[1], self.timeToSeconds(l[2]), "OK")
                splits.append(punch)

            elif ('smallest' in l) or ('Average' in l) or ('biggest' in l) or ('place' in l):
                continue

            else:
                print("Can't process line: %s" % line)

        return(splits)

    def _expandRunResult(self, s):
        '''
        expand the OORG Run Result abbreviation to the proper value for IOF xml
        '''
        resultTypes = {"OK":  "OK",
                       "MSP": "Misspunch",
                       "DSQ": "Disqualified",
                       "DNF": "Did not finish",
                       "OVT": "Overtime",
                       "NC":  "Non-Compete"}

        s = s.split()[0] #handles the case: "NC  15.45"

        if self.isTime(s):
            return "OK"

        elif s in resultTypes.keys():
            return resultTypes[s]
        else:
            return "Finished"

    def isTime(self, s):
        '''
        returns True if string matches \d+.\d\d, (OORG output for minutes.seconds), otherwise false
        '''
        time = re.compile(r"\d+.\d\d")
        if time.match(s) is not None:
            return(True)
        return(False)

    def timeToSeconds(self, t):
        '''
        translates OORG "minutes.seconds" string to "seconds" string.
        '''
        if self.isTime(t):
            t = t.split(".")
            m = int(t[0])
            s = int(t[1])
            v = m*60 + s
            return str(v)
        else:
            raise(TypeError, "Can't process timestring: %s" % t)

        

if __name__ == '__main__':
    #create the object
    foo = OORGdownload(sys.argv[1])

    #save the XML file
    filename = "download2XML_" + foo.d['RunECard'] + ".xml"
    with open(filename, 'w') as w:
        w.write(etree.tostring(foo.xml, pretty_print=True))

    #POST the XML file
    url = sys.argv[2]+'/api/downloads'
    f = {'file': open(filename, 'r')}
    r = requests.post(url, files=f)
    #print(r.text)

    #delete the XML file
    os.unlink(filename)
