import time
import re
import os
from PyQt5 import QtCore
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait


class StormFufuTest(QtCore.QThread):
    msgSignal = QtCore.pyqtSignal(str, str, str, int)

    def __init__(self, parent) -> None:
        super().__init__()
        self.currParent = parent
        self.driver = webdriver.Ie(executable_path=r"Drivers/IEDriverServer.exe")
        self.driver.implicitly_wait(3)

        self.reName = re.compile(r"&nbsp;[\w+]</TD>")
        self.reButton = re.compile(r"'([\w\d=&?.]+)'")
        self.mainPage = "http://192.168.1.253/"

    def run(self):
        self.driver.get(self.mainPage)
        elem = self.driver.find_element_by_id('user')
        elem.clear()
        elem.send_keys("deko")
        elem = self.driver.find_element_by_id('pass')
        elem.clear()
        elem.send_keys("deko10")
        elem.send_keys(Keys.RETURN)
        pages = ('Alarms', 'Control&Params', 'Band Info', 'SW Upgrade', 'License')
        for i in pages:
            elem = self.driver.find_element_by_xpath("//a[text()='" + i + "']")
            print(elem.get_attribute("href"))
            self.driver.get(elem.get_attribute("href"))
            time.sleep(2)
            # if i == pages[0]:
            #     self.pageAlarms()
            if i == pages[1]:
                self.pageControl()
        self.driver.close()
        os.system("taskkill /f /im IEDriverServer.exe")

    def pageAlarms(self):
        for elem in self.driver.find_elements_by_xpath(".//tr/td[@class='NeAlarmTbl']"):
            print(elem.get_attribute('innerHTML'))
            for alarm in elem.find_elements_by_xpath("../td/div"):
                print(alarm.get_attribute('innerHTML'))
            print("------------------------------------------------------------------------")

    def pageControl(self):
        for elem in self.driver.find_elements_by_xpath("//button"):
            print(elem.get_attribute('innerHTML'))
            onclick = elem.get_attribute('onclick')
            print(self.reButton.search(onclick).group(0))





