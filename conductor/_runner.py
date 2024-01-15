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

SOURCE_DIR = "C:\\Users\\eric\\OneDrive\\Orienteering\\epunchCoord\\losttime2_testing\\_reference\\"
SOURCE_FILE = "2023WL01_Splits_v2.xml"
INTERMEDIATE_DIR = "C:\\Users\\eric\\OneDrive\\Orienteering\\epunchCoord\\losttime2_testing\\_downloads\\"
# FINAL_DIR = 

def CreateNewHtmlFromSplits():
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.dhowWhenStarting", False)
    options.set_preference("browser.download.dir", INTERMEDIATE_DIR )
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/html")

    driver = webdriver.Firefox(options=options)
    driver.get('localhost:3000')

    errors = [NoSuchElementException, ElementNotInteractableException]
    wait = WebDriverWait(driver, timeout=10, ignored_exceptions=errors)
    wait.until(lambda x: driver.find_element(By.CLASS_NAME, 'dropzone').is_displayed())
    addFileToDropzone(driver, 'dz-file-input', 'Fakeresults.xml')

    errors = [NoSuchElementException, ElementNotInteractableException]
    wait = WebDriverWait(driver, timeout=10, ignored_exceptions=errors)
    wait.until(element_to_be_clickable((By.ID, "scoring-preset-COC-WL2324")))
    clickViaJS(driver, "#scoring-preset-COC-WL2324")

    errors = [NoSuchElementException, ElementNotInteractableException]
    wait = WebDriverWait(driver, timeout=10, poll_frequency=.5, ignored_exceptions=errors)
    wait.until(element_to_be_clickable((By.ID, "dl-COC-html")))
    clickViaJS(driver, "#dl-COC-html")

    # check the file has finished downloading
    # while retries > 0
    # with open the file reading
    # confirm last line of file is "</ResultList>" (then empty line)
    # if not, wait 1 second and try again.
    # max wait 30 seconds is probably too generous but not sure what load is going to be like.
    
    # and in the meantime...
    wait = WebDriverWait(driver, timeout=5)

    driver.quit()

def addFileToDropzone(driver, css_id, file):
    upload_file = driver.find_element(By.ID, css_id)
    upload_file.send_keys(SOURCE_DIR + SOURCE_FILE)
    return

def clickViaJS(driver, selector):
    script = 'document.querySelector(\"{}\").click();'.format(selector)
    driver.execute_script(script)
    return

# detect new file from OE now in SFTP drop point
# grab new file
# make sure react app is running locally, start it if not?
# call react app to process through scoring algo
CreateNewHtmlFromSplits()
# get new html file
# move html file to location to serve
