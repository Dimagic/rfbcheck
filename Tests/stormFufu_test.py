import time
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

    def run(self):
        # self.msgSignal.emit('i', 'RFBChech', 'FUFU', 1)
        # try:
        #     driver = webdriver.Chrome(executable_path=r"Drivers/chromedriver.exe")
        # except Exception as e:
        #     print(str(e))
        # else:


        self.driver.get("http://192.168.1.253")
        # assert "Python" in driver.title
        elem = self.driver.find_element_by_id('user')
        elem.clear()
        elem.send_keys("deko")
        elem = self.driver.find_element_by_id('pass')
        elem.clear()
        elem.send_keys("deko10")
        elem.send_keys(Keys.RETURN)
        # WebDriverWait(driver, timeout).until(elem)

        # for i in ('Alarms', 'Control&amp;Params'):
        #     try:
        #         driver.find_element_by_link_text(i).click()
        #     except Exception:
        #         print('Element: ' + i + ' not found')

        # links = driver.find_elements_by_partial_link_text('##')
        # for link in links:
        #     print(link.get_attribute("href"))

        pages = ('Alarms', 'Control&Params', 'Band Info', 'SW Upgrade', 'License')
        for i in pages:
            elem = self.driver.find_element_by_xpath("//a[text()='" + i + "']")
            print(elem.get_attribute("href"))
            self.driver.get(elem.get_attribute("href"))
            time.sleep(2)
            if i == pages[0]:
                self.pageAlarms()
        # ActionChains(driver).move_to_element(elem).click()
        # elem.click()

            # WebDriverWait(driver, timeout).until(elem)

        # elems = driver.find_elements_by_class_name("tab")
        # for elem in elems:
        #     print(elem.get_attribute("href"))

            # if 'alarms' in elem.get_attribute("href"):
            #     elem.send_keys(Keys.RETURN)

        # assert "No results found." not in driver.page_source
        time.sleep(10)
        self.driver.close()

    def pageAlarms(self):
        for elem in self.driver.find_elements_by_class_name("NeAlarmTblImg"):
            print(elem.get_attribute('innerHTML'))