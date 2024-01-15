###
# _runner.py
# detect new file from OE now in SFTP drop point
# grab new file
# call react app to process through scoring algo
# get new html file
# move html file to location to serve
###

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import element_to_be_clickable

import requests
from time import sleep
import os
from shutil import copy2

SOURCE_DIR = "C:\\Users\\eric\\OneDrive\\Orienteering\\epunchCoord\\losttime2_testing\\_reference\\xml\\"

LOSTTIME_URL='http://localhost:3000'

LOSTTIME_OUT_DIR = "C:\\Users\\eric\\OneDrive\\Orienteering\\epunchCoord\\losttime2_testing\\_downloads\\"

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "web-public\\")
PUBLIC_FILENAME = "results.html"

def GetLatestFileInFolder(dir):
    wd = os.getcwd()
    os.chdir(dir)
    files = sorted(filter(os.path.isfile, os.listdir('.')), key=os.path.getmtime, reverse=True)
    fn = files[0]
    os.chdir(wd)
    return os.path.join(dir, fn)

def GetLatestResultsXml(dir=SOURCE_DIR):
    return GetLatestFileInFolder(dir)

#### Section: Check LostTime

def LiveConnectionToLostTime():
    try:
        resp = requests.get(
            url=LOSTTIME_URL,
            timeout=5
            )
        resp.raise_for_status()
    except:
        print("Unable to reach LostTime - is it running at {}?".format(LOSTTIME_URL))
        return False
    return True

#### Section: Check the file

# From: https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python
def LastLineOfXmlIsPresent(file):
    with open(file, 'rb') as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    if last_line == "</ResultList>\r\n":
        return True
    return False

#### Section: Call LostTime with File

def addFileToDropzone(driver, css_id, file):
    upload_file = driver.find_element(By.ID, css_id)
    upload_file.send_keys(file)
    return

def clickViaJS(driver, selector):
    script = 'document.querySelector(\"{}\").click();'.format(selector)
    driver.execute_script(script)
    return

def CreateNewHtmlFromSplits(xmlresults_fn):
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.dhowWhenStarting", False)
    options.set_preference("browser.download.dir", LOSTTIME_OUT_DIR )
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/html")

    driver = webdriver.Firefox(options=options)
    try:
        driver.get(LOSTTIME_URL)

        errors = [NoSuchElementException, ElementNotInteractableException]
        wait = WebDriverWait(driver, timeout=5, ignored_exceptions=errors)
        wait.until(lambda x: driver.find_element(By.CLASS_NAME, 'dropzone').is_displayed())
        addFileToDropzone(driver, 'dz-file-input', xmlresults_fn)

        errors = [NoSuchElementException, ElementNotInteractableException]
        wait = WebDriverWait(driver, timeout=5, ignored_exceptions=errors)
        wait.until(element_to_be_clickable((By.ID, "scoring-preset-COC-WL2324")))
        clickViaJS(driver, "#scoring-preset-COC-WL2324")

        errors = [NoSuchElementException, ElementNotInteractableException]
        wait = WebDriverWait(driver, timeout=5, poll_frequency=.5, ignored_exceptions=errors)
        wait.until(element_to_be_clickable((By.ID, "dl-COC-html")))
        clickViaJS(driver, "#dl-COC-html")

    except:
        print("Issue with generating file in LostTime")
        return False

    finally:
        sleep(2) ## this is here to make sure the the file downloads and firefox doesn't block on pending download.
        driver.quit()
    return True


#### Section: Move files to server location

def GetLostTimeOutputFile(dir=LOSTTIME_OUT_DIR):
    return GetLatestFileInFolder(dir)

def CopyOutputToPublicFolder():
    try:
        src = GetLostTimeOutputFile()
        dest = os.path.join(PUBLIC_DIR, PUBLIC_FILENAME)
        print("from here: " + src)
        print("to here: " + dest)
        copy2(src, dest)
    except:
        print("issue copying file to public folder")
        return False
    return True


def main():
    processed_file=''

    while True:
        # always sleep
        print('Sleeping')
        sleep(2)

        # detect new file from OE now in SFTP drop point
        # grab new file
        XmlResults_fn = GetLatestResultsXml()
        print('Found file: ' + XmlResults_fn)

        if XmlResults_fn != processed_file:
            print('This is new! processing')
            
            if not LastLineOfXmlIsPresent(XmlResults_fn):
                continue

            # make sure react app is running locally
            if not LiveConnectionToLostTime():
                continue
            
            # call react app to process through scoring algo
            if not CreateNewHtmlFromSplits(XmlResults_fn):
                continue

            # get new html file
            # move html file to location to serve
            if not CopyOutputToPublicFolder():
                continue

            # set this file as processed
            processed_file = XmlResults_fn
        else:
            print('Already processed that file')

main()
