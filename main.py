from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import re
import time
import threading
import playsound

UPDATE_TIME = 30  # seconds. time between printing current points
TIMEOUT = 240  # seconds. time to wait for the total points element to appear
REFRESH_WAIT_TIME = 3  # seconds. time to wait after a refresh click
POINTS_CLASSNAME = "dKLPfQ"
REFRESH_BUTTON_CLASSNAME = "GDkNk"
USERNAME_CLASSNAME = "ldMMkD"
SEPARATOR = "|".center(7, ' ')
THIRD_COLUMN = "Difference"


class FantasyScraper:
    # invisible webdriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=3")

    def __init__(self, url, name):
        self.url = url
        self.name = name

    def connect(self):
        print(self.name + ": Connecting...")

        # run browser and open link
        self.browser = webdriver.Chrome(options=self.options)

        self.browser.get(self.url)
        print(self.name + ": Waiting for page to load...")

        # wait for points element to appear
        self.points_webelement = WebDriverWait(self.browser, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, POINTS_CLASSNAME)))

        # regex for integers and minus sign
        self.points = re.search(r"[0-9-]+", self.points_webelement.text)[0]

        # set username to his fantasy name
        self.username = self.browser.find_elements_by_class_name(USERNAME_CLASSNAME)[0].text

        print(self.name + ": Successfully connected.")

    def updatePoints(self):
        self.browser.find_elements_by_class_name(REFRESH_BUTTON_CLASSNAME)[0].click()
        time.sleep(REFRESH_WAIT_TIME)  # wait for a refresh to happen
        self.points_webelement = self.browser.find_elements_by_class_name(POINTS_CLASSNAME)[0]

        # regex for integers and minus sign
        self.points = re.search(r"[0-9-]+", self.points_webelement.text)[0]


# creates a new current results row and computes difference
def createCurrentResult(scraperA, scraperB):
    difference = str(int(scraperA.points) - int(scraperB.points))

    current_result = scraperA.points.center(len(scraperA.username), ' ')
    current_result += ' ' * len(SEPARATOR) + scraperB.points.center(len(scraperB.username), ' ')
    current_result += ' ' * len(SEPARATOR) + difference.center(len(THIRD_COLUMN))

    return current_result


def main():
    while True:
        message = input("Do you want to compare the previous teams in the same gameweek?(y/n): ")
        if message.lower() == 'y' or message.lower() == 'n':
            break
        else:
            print("Please answer with y or n.")

    if message == 'y':
        file = open("last_used.txt", 'r')
        teamA_url = file.readline()
        teamB_url = file.readline()
        file.close()
    else:
        teamA_url = input("Enter the Fantasy PL team URL for the current gameweek(team A): ")
        teamB_url = input("Enter the Fantasy PL team URL for the current gameweek(team B): ")

        # store in last used file
        file = open("last_used.txt", 'w')
        file.write(teamA_url)
        file.write('\n')
        file.write(teamB_url)
        file.close()

    scraperA = FantasyScraper(teamA_url, "Team A")
    scraperB = FantasyScraper(teamB_url, "Team B")

    # set the threads to connect
    threadA = threading.Thread(target=scraperA.connect)
    threadB = threading.Thread(target=scraperB.connect)

    threadA.start()
    threadB.start()

    # wait for threads to finish
    threadA.join()
    threadB.join()


    top_row = scraperA.username + SEPARATOR + scraperB.username
    print("\n\n" + "<---CURRENT-POINTS--->".center(len(top_row), ' '))

    # append this later to make current points centered on first two rows only
    top_row += SEPARATOR + THIRD_COLUMN
    print(top_row)

    current_result = createCurrentResult(scraperA, scraperB)
    print(current_result)

    previous_result = current_result

    try:
        while True:

            # set the threads to update
            threadA = threading.Thread(target=scraperA.updatePoints)
            threadB = threading.Thread(target=scraperB.updatePoints)
            threadA.start()
            threadB.start()
            threadA.join()
            threadB.join()

            current_result = createCurrentResult(scraperA, scraperB)

            # print a result only if it changed from the previous
            if previous_result != current_result:
                print(current_result)
                previous_result = current_result

                playsound.playsound("alert.wav")

            time.sleep(UPDATE_TIME - REFRESH_WAIT_TIME)

    except:
        # to avoid exceptions and errors when closing
        # or driver stays open
        pass


main()
