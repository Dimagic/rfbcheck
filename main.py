# stylesheet
# import qdarkstyle
import threading
from threading import Thread

from Forms.mainwindow import Ui_MainWindow
from Equip.instrumentSettings import TestSettings
from Equip.selectUser import SelectUser
from Equip.applySetFile import *
from Equip.calibration import *
from Equip.printReport import *
from Equip.editRFB import *
from Equip.journal import *
from Tests.stormFufu_test import StormFufuTest
from Tests.testController import *
from Tests.bitAlarm_test import *
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QMovie, QStandardItem
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QLabel, QAction, QFileDialog
from PIL import Image
from Equip.config import Config

import datetime
import re

version = '0.3.20'


class TestTime(threading.Thread):
    def __init__(self, parent):
        startTime = datetime.datetime.now()
        parent.startTestTime = startTime
        while parent.testIsRun:
            timeTest = datetime.datetime.now() - startTime
            parent.testTimeLbl.setText(str(timeTest)[:7])
            time.sleep(.5)


class mainProgram(QtWidgets.QMainWindow, QtCore.QObject, Ui_MainWindow):
    def __init__(self, form, parent=None):
        super(mainProgram, self).__init__(parent)

        # img = Image.open('Img/connect2.gif')
        # img.show()
        # loadUi('Forms/mainwindow.ui', self)

        # stylesheet
        # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.startTestTime = None
        self.logFile = None
        self.config = Config()

        """ Setting images """
        self.appIcon = QtGui.QIcon("Img/ico32_pgn_icon.ico")
        self.passImg = QtGui.QPixmap('Img/pass.png')
        self.failImg = QtGui.QPixmap('Img/fail.png')
        self.warnImg = QtGui.QPixmap('Img/warning.png')
        self.connectMovie = QMovie('Img/connect2.gif')
        self.greenLedMovie = QMovie('Img/greenLed.gif')
        self.blueLedMovie = QMovie('Img/blueLed.gif')
        self.redLedMovie = QMovie('Img/redLed.gif')

        self.setupUi(form)

        self.tableJournal.resizeEvent = self.onResize
        self.tableResult.resizeEvent = self.onResize

        self.currUser = None
        self.setUser()
        self.answer = None

        """ Setting menu """
        self.menuSelectUser.triggered.connect(self.selectUser)
        self.menuComPort.triggered.connect(self.selectComPort)
        self.menuTestSettings.triggered.connect(self.testSettings)
        self.menuExit.triggered.connect(form.close)
        self.menuExit.setShortcut('Ctrl+Q')

        self.instrAddrCombo.setMouseTracking(True)
        self.instrAddrCombo.installEventFilter(self)
        self.tableJournal.installEventFilter(self)

        self.hotKey = []

        self.testLogDl = {}
        self.testLogUl = {}

        self.runTest = None
        self.listSettings = []

        self.calibrSaToGen = {}
        self.calibrGenToSa = {}

        self.to_DsaUlDl = {}  # results DSA test from DB """

        self.myThread = None
        self.setFileThread = None
        self.tt = None

        self.atrSettings = {}
        self.instr = None

        self.TestPrBar.setValue(0)
        self.whatConn = None
        self.band = None

        self.testIsRun = False

        self.col = ['RFB type', 'DL c.freq', 'UL c.freq', 'DL IM pow', 'UL IM pow', 'DL DSA1', 'DL DSA2', 'DL DSA3',
                    'UL DSA1', 'UL DSA2', 'UL DSA3', 'DSA pow', 'ALC IN pow']

        self.radioInstrChecked()

        self.setInstrBtn.clicked.connect(self.setCurrInstrAddr)
        self.updateInstrBtn.clicked.connect(self.getInstrAddr)
        self.journalUpdateBtn.clicked.connect(self.journalUpdateBtnClick)
        self.tableJournal.clicked.connect(self.getSelectedRow)
        self.printReportBtn.clicked.connect(self.printReportBtnClicked)

        self.clrLogBtn.clicked.connect(self.clrLogBtnClick)
        self.saveLogBtn.clicked.connect(self.saveLogBtnClick)
        self.portLbl.setText("")
        self.baudLbl.setText("")

        self.rfbSN.textEdited.connect(self.startBtnEnabled)
        self.rfbSN.textChanged.connect(self.startBtnEnabled)
        self.journalFilter.textEdited.connect(Journal.feelJournal)
        self.saAtten.editingFinished.connect(self.checkAttenValue)
        self.genAtten.editingFinished.connect(self.checkAttenValue)
        self.setSaRadio.clicked.connect(self.radioInstrChecked)
        self.setGenRadio.clicked.connect(self.radioInstrChecked)
        self.setNaRadio.clicked.connect(self.radioInstrChecked)
        self.calibrationBtn.clicked.connect(self.calibrationBtnClick)
        self.clearCalBtn.clicked.connect(self.clearCalibrationBtnClick)
        self.calAllBands.clicked.connect(self.calAllBandsCheck)
        self.calibrStart.setValidator(QtGui.QIntValidator())
        self.calibrStop.setValidator(QtGui.QIntValidator())
        self.startTestBtn.clicked.connect(self.startThreadTest)
        self.applySetBtn.clicked.connect(self.startThreadLoadSet)
        self.stormFufu.clicked.connect(self.stormFufuTest)
        self.startTestBtn.setEnabled(False)

        conn, cursor = self.getConnDb()
        self.rfbList = cursor.execute("select name from rfb_type order by name")

        """ Get RFB list and fill combobox """
        for i in self.rfbList:
            self.rfbTypeCombo.addItem(str(i).replace("('", "").replace("',)", ""))
            if len(self.editRfbCombo) == 0: self.editRfbCombo.addItem('New')
            self.editRfbCombo.addItem(str(i).replace("('", "").replace("',)", ""))

        """ Get test type list and fill combobox """
        self.testType = cursor.execute("select name from test_type").fetchall()
        for i in self.testType:
            self.testTypeCombo.addItem(i[0])

        rep = Report(None, None, None, self)
        rep.getTemplates(self)

        self.rfbIsChecked()
        self.rfbTypeCombo.activated.connect(self.rfbIsChecked)
        self.setTestsList()
        self.testTypeCombo.activated.connect(self.setTestsList)

        self.journalDateStart.setDate(QtCore.QDate.currentDate().addMonths(-1))
        self.journalDateStop.setDate(QtCore.QDate.currentDate())

        self.newRfbBtn.clicked.connect(self.on_newRfbBtn_clicked)
        conn.close()
        self.journal = Journal(self)

        self.setTestsList()

    def on_newRfbBtn_clicked(self):
        dialog = EditRFB(self, self)
        dialog.setWindowIcon(self.appIcon)
        dialog.show()

    def setUser(self):
        try:
            conn, cursor = self.getConnDb()
            q = "select lastUser from settings"
            self.currUser = cursor.execute(q).fetchone()[0]
            conn.close()
            form.setWindowTitle('RFBCheck %s User: %s' % (version, self.currUser))
        except Exception as e:
            self.sendMsg('c', 'Set user error', str(e), 1)

    def updateDbQuery(self, query):
        try:
            conn, cursor = self.getConnDb()
            cursor.execute(query)
            conn.commit()
            conn.close()
        except Exception as e:
            self.currParent.sendMsg('c', 'Update DB query error', str(e), 1)

    def loadSettings(self):
        pass

    def writeSettings(self):
        pass

    def selectUser(self):
        SelectUser(self)

    def selectComPort(self):
        SelectComPort(self)

    def testSettings(self):
        TestSettings(self)

    def checkTestState(self, b):
        self.sendLog(str(b.text()), 0)

    def journalUpdateBtnClick(self):
        Journal(self)

    def getSelectedRow(self):
        try:
            rfb = (self.tableJournal.item(self.tableJournal.currentItem().row(), 0)).text()
            sn = (self.tableJournal.item(self.tableJournal.currentItem().row(), 1)).text()
            date = (self.tableJournal.item(self.tableJournal.currentItem().row(), 2)).text()
        except AttributeError:
            self.sendMsg('i', 'Message', 'You have to choice one of element in journal table', 1)
            return
        except Exception as e:
            self.sendMsg('w', 'Error', str(e), 1)
            return
        return rfb, sn, date

    def printReportBtnClicked(self):
        try:
            rfb, sn, date = self.getSelectedRow()
            Report(rfb, sn, date, self)
        except Exception as e:
            self.sendMsg('i', 'Print report error', str(e), 1)
            return

    def clrLogBtnClick(self):
        self.listLog.clear()
        self.tableResult.clear()
        self.tableResult.setRowCount(0)
        self.tableResult.setHorizontalHeaderLabels(['Test name', 'Dl/Ul', 'Min', 'Current', 'Max', 'Result'])

    def saveLogBtnClick(self):
        fileLog = './Log/lastRFlog.log'
        count = self.listLog.count()
        if count == 0:
            return
        f = open(fileLog, 'w')
        for i in range(count):
            f.write("%s\n" % self.listLog.item(i).text())
        f.close()
        os.startfile(fileLog)

    def calibrationBtnClick(self):
        self.myThread = Calibration(self)
        self.myThread.logSignal.connect(self.sendLog, QtCore.Qt.QueuedConnection)
        self.myThread.msgSignal.connect(self.sendMsg, QtCore.Qt.QueuedConnection)
        self.myThread.progressBarSignal.connect(self.setProgressBar, QtCore.Qt.QueuedConnection)
        self.myThread.start()

    def calAllBandsCheck(self):
        if self.calAllBands.isChecked():
            self.calibrStart.setEnabled(False)
            self.calibrStop.setEnabled(False)
            self.calibrStart.setText('')
            self.calibrStop.setText('')
        else:
            self.calibrStart.setEnabled(True)
            self.calibrStop.setEnabled(True)

    def clearCalibrationBtnClick(self):
        if self.sendMsg('q', 'Clear calibration table', 'Clear calibration tables. Are you sure?', 2) == QMessageBox.Ok:
            try:
                conn, cursor = self.getConnDb()
                cursor.execute("delete from calGenToSa").fetchall()
                cursor.execute("delete from calSaToGen").fetchall()
                conn.commit()
                conn.close()
                self.sendMsg('q', 'Complete', 'Clearing calibration table complete.', 1)
            except sqlite3.DatabaseError as err:
                self.sendMsg('c', 'Query error', str(err), 0)
                conn.close()

    def rfbIsChecked(self):
        while self.tableSettings.rowCount() > 0:
            n = self.tableSettings.rowCount() - 1
            self.tableSettings.removeRow(n)
        conn, cursor = self.getConnDb()
        self.clrLogBtnClick()
        rows = cursor.execute("select * from rfb_type where name = :n",
                              {'n': self.rfbTypeCombo.currentText()}).fetchall()
        for row in rows:
            self.sendLog("For RFB " + row[1] + " need to use ADEM - " + row[2], 0)
        self.col = ['RFB type', 'DL c.freq', 'UL c.freq', 'DL IM pow', 'UL IM pow', 'DL DSA1', 'DL DSA2', 'DL DSA3',
                    'UL DSA1', 'UL DSA2', 'UL DSA3', 'DSA pow', 'Dl ALC IN pow', 'Ul ALC IN pow', 'Dl ALC OUT pow',
                    'Ul ALC OUT pow']
        rows = cursor.execute("select * from test_settings where rfb_type = :n",
                              {'n': self.rfbTypeCombo.currentText()}).fetchall()
        conn.close()

        if len(rows) == 0:
            msg = 'Test settings for %s not found' % self.rfbTypeCombo.currentText()
            self.sendMsg('c', 'RFBCheck', msg, 1)
            return
        else:
            for rowSetttings in rows:
                self.listSettings = list(rowSetttings)[1:]

        for i, j in enumerate(self.col):
            row = self.tableSettings.rowCount()
            self.tableSettings.insertRow(row)
            self.tableSettings.setItem(row, 0, QtWidgets.QTableWidgetItem(j))
            self.tableSettings.setItem(row, 1, QtWidgets.QTableWidgetItem(str(self.listSettings[i])))
            # self.tableSettings.resizeColumnsToContents()

        conn, cursor = self.getConnDb()

        rows = cursor.execute('PRAGMA table_info (ATR)').fetchall()
        atrKeys = []
        for row in rows:
            atrKeys.append(row[1])
        rows = cursor.execute("select * from ATR where rfb_type = :n",
                              {'n': self.rfbTypeCombo.currentText()}).fetchall()
        for row in rows:
            k = 0
            for n in row:
                self.atrSettings.update({atrKeys[k]: n})
                k += 1
        if len(self.atrSettings) == 0:
            self.sendMsg('w', 'Warning', 'ATR record for ' + self.rfbTypeCombo.currentText() + ' not found', 1)
            self.calibrLbl.setText('False')
            self.dateCalibrLbl.setText(None)
            return
        else:
            self.sendLog('Loading ATR settings for ' + self.atrSettings.get('rfb_type') + ' complite', 0)
        conn.close()
        try:
            calibrationCheck(self)
        except Exception as e:
            self.sendMsg('W', 'Getting calibration error', str(e), 1)
        return

    def connectDb(self):
        try:
            f = open('./DB/rfb.db', 'r')
            f.close()
            return sqlite3.connect('./DB/rfb.db')
        except Exception as e:
            self.sendMsg("c", "Opening DB error", str(e), 1)
            sys.exit(0)

    def timeNow(self):
        return str(datetime.datetime.today().strftime("%H:%M:%S"))

    def startBtnEnabled(self):
        snLen = int(self.config.getConfAttr('limits', 'sn_length'))
        try:
            line = self.rfbSN.text()
            if len(line) > snLen and line[len(line)-snLen:].isnumeric():
                self.getSnViaScanner()
        except Exception as e:
            print(str(e))
        if ((self.rfbSN.text().isdigit() and len(self.rfbSN.text()) >= snLen)
                or (self.rfbSN.text().upper() == 'XXXX')):
            self.startTestBtn.setEnabled(True)
        else:
            self.startTestBtn.setEnabled(False)

    def sendMsg(self, icon, msgTitle, msgText, typeQuestion):
        msg = QMessageBox()
        if icon == 'q':
            msg.setIcon(QMessageBox.Question)
        elif icon == 'i':
            msg.setIcon(QMessageBox.Information)
        elif icon == 'w':
            msg.setIcon(QMessageBox.Warning)
        elif icon == 'c':
            msg.setIcon(QMessageBox.Critical)
        msg.setText(msgText)
        msg.setWindowTitle(msgTitle)
        msg.setWindowIcon(self.appIcon)
        if typeQuestion == 1:
            msg.setStandardButtons(QMessageBox.Ok)
        elif typeQuestion == 2:
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        elif typeQuestion == 3:
            msg.setStandardButtons(QMessageBox.Ignore | QMessageBox.Retry | QMessageBox.Cancel)
        self.answer = msg.exec_()
        return self.answer

    def getInstrAddr(self):
        try:
            rm = visa.ResourceManager()
            rm.timeout = 500
            listInstr = rm.list_resources()
            self.instrAddrCombo.clear()
            for i in listInstr:
                self.instrAddrCombo.addItem(str(i))
            ledLbl = [self.saStat, self.genStat, self.naStat]
            adrLbl = [self.currSaLbl, self.currGenLbl, self.currNaLbl]
            for j in adrLbl:
                i = adrLbl.index(j)
                try:
                    currInstr = rm.open_resource(j.text())
                    currInstr.query('*IDN?')
                    self.greenLedMovie.setScaledSize(QSize(13, 13))
                    ledLbl[i].setMovie(self.greenLedMovie)
                    self.greenLedMovie.start()
                    if j == self.currNaLbl:
                        self.gainNA.setEnabled(True)
                except:
                    self.redLedMovie.setScaledSize(QSize(13, 13))
                    ledLbl[i].setMovie(self.redLedMovie)
                    self.redLedMovie.start()
                    if j == self.currNaLbl:
                        self.gainNA.setEnabled(False)
                        self.gainSA.setChecked(True)
        except Exception as e:
            self.redLedMovie.setScaledSize(QSize(13, 13))
            self.saStat.setMovie(self.redLedMovie)
            self.genStat.setMovie(self.redLedMovie)
            self.naStat.setMovie(self.redLedMovie)
            self.redLedMovie.start()
            self.sendMsg('c', 'Instrument init. error', str(e), 1)

    def getConnDb(self):
        try:
            conn = self.connectDb()
            cursor = conn.cursor()
            return conn, cursor
        except Exception as e:
            self.sendMsg('c', 'Connection DB error', str(e), 1)

    def getCurrInstrAddr(self):
        conn, cursor = self.getConnDb()
        rows = cursor.execute("select address, useAtten, fullName from instruments where name = 'SA'").fetchall()
        for row in rows:
            self.currSaLbl.setText(str(row[0]))
            self.saAtten.setText(str(row[1]))
            self.currSaNameLbl.setText(str(row[2]))
        rows = cursor.execute("select address, useAtten, fullName from instruments where name = 'GEN'").fetchall()
        for row in rows:
            self.currGenLbl.setText(str(row[0]))
            self.genAtten.setText(str(row[1]))
            self.currGenNameLbl.setText(str(row[2]))
        rows = cursor.execute("select address, useAtten, fullName from instruments where name = 'NA'").fetchall()
        for row in rows:
            self.currNaLbl.setText(str(row[0]))
            self.naAtten1.setText(str(row[1]))
            self.currNaNameLbl.setText(str(row[2]))
        conn.close()

    def radioInstrChecked(self):
        self.getCurrInstrAddr()
        self.getInstrAddr()
        radioArr = {self.currSaLbl.text(): self.setSaRadio,
                    self.currGenLbl.text(): self.setGenRadio,
                    self.currNaLbl.text(): self.setNaRadio}

        if self.setSaRadio.isChecked():
            self.saAtten.setEnabled(True)
            self.genAtten.setEnabled(False)
            self.naAtten1.setEnabled(False)
            self.naAtten2.setEnabled(False)
        if self.setGenRadio.isChecked():
            self.saAtten.setEnabled(False)
            self.genAtten.setEnabled(True)
            self.naAtten1.setEnabled(False)
            self.naAtten2.setEnabled(False)
        if self.setNaRadio.isChecked():
            self.saAtten.setEnabled(False)
            self.genAtten.setEnabled(False)
            self.naAtten1.setEnabled(True)
            self.naAtten2.setEnabled(True)

        allItems = [self.instrAddrCombo.itemText(i) for i in range(self.instrAddrCombo.count())]
        for i in radioArr:
            if radioArr.get(i).isChecked():
                for x, j in enumerate(allItems):
                    if j == i:
                        try:
                            self.instrAddrCombo.setCurrentIndex(x)
                        except:
                            self.instrAddrCombo.setCurrentIndex(0)

    def setCurrInstrAddr(self):
        conn, cursor = self.getConnDb()
        try:
            q = "update instruments set address = '', useAtten = '0', fullName = '' where address = '%s'" % (self.instrAddrCombo.currentText())
            self.updateDbQuery(q)
            checkedInstr = visa.ResourceManager().open_resource(self.instrAddrCombo.currentText()).query('*IDN?')
            if self.setSaRadio.isChecked():
                self.currSaNameLbl.setText(checkedInstr)
                cursor.execute("update instruments set address = :n, useAtten = :n2, fullName = :n3 where name = 'SA'",
                               {'n': self.instrAddrCombo.currentText(), 'n2': int(self.saAtten.text()),
                                'n3': self.currSaNameLbl.text()})
            elif self.setGenRadio.isChecked():
                self.currGenNameLbl.setText(checkedInstr)
                cursor.execute("update instruments set address = :n, useAtten = :n2, fullName = :n3 where name = 'GEN'",
                               {'n': self.instrAddrCombo.currentText(), 'n2': int(self.genAtten.text()),
                                'n3': self.currGenNameLbl.text()})
            elif self.setNaRadio.isChecked():
                self.currNaNameLbl.setText(checkedInstr)
                cursor.execute("update instruments set address = :n, useAtten = :n2, fullName = :n3 where name = 'NA'",
                               {'n': self.instrAddrCombo.currentText(), 'n2': int(self.naAtten1.text()), 'n3': self.currNaNameLbl.text()})

            conn.commit()
            conn.close()
            self.sendMsg('i', 'Save changes', 'Done', 1)
            self.getCurrInstrAddr()
            self.getInstrAddr()
        except Exception as e:
            conn.close()
            self.sendMsg('c', 'Save instr. settings error', str(e), 1)

    def checkAttenValue(self):
        try:
            if self.saAtten.text() == '':
                self.saAtten.setText('0')
            else:
                int(self.saAtten.text())
            if self.genAtten.text() == '':
                self.genAtten.setText('0')
            else:
                int(self.genAtten.text())
            if self.naAtten1.text() == '':
                self.naAtten1.setText('0')
            else:
                int(self.naAtten1.text())
            if self.naAtten2.text() == '':
                self.naAtten2.setText('0')
            else:
                int(self.naAtten2.text())
        except Exception:
            self.sendMsg('w', 'Warning', 'Incorrect value of attenuator', 1)

    def checkRecordInDb(self):
        conn, cursor = self.getConnDb()
        try:
            row = cursor.execute("select rfb_type from test_results where sn = :n1",
                                 {'n1': self.rfbSN.text()}).fetchone()
            conn.close()
            if row is not None and row[0] != self.rfbTypeCombo.currentText():
                self.sendMsg('w', 'Warning',
                             'SN: ' + str(self.rfbSN.text()) + ' already exist. RFB type: ' + str(row[0]), 1)
                return False
            else:
                return True
        except sqlite3.DatabaseError as err:
            self.sendMsg('c', 'Query error', str(err), 1)
            conn.close()

    def startThreadLoadSet(self):
        currRFB = self.rfbTypeCombo.currentText()
        try:
            fileForLoad = currRFB + ".csv"
            f = open("./setFiles/" + fileForLoad, 'r')
            f.close()
        except Exception:
            fileForLoad = ""

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Loading file settings for " + currRFB,
                                                  "./setFiles/" + fileForLoad,
                                                  "CSV Files (*.csv)", options=options)
        if not fileName:
            return
        self.setFileThread = ApplySetFile(self, fileName)
        self.setFileThread.logSignal.connect(self.sendLog, QtCore.Qt.QueuedConnection)
        self.setFileThread.msgSignal.connect(self.sendMsg, QtCore.Qt.QueuedConnection)
        self.setFileThread.progressBarSignal.connect(self.setProgressBar, QtCore.Qt.QueuedConnection)
        self.setFileThread.comMovieSignal.connect(self.setComMovie, QtCore.Qt.QueuedConnection)
        self.setFileThread.started.connect(self.on_startedSet)
        self.setFileThread.finished.connect(self.on_finishedSet)
        self.setFileThread.start()

    def on_startedSet(self):
        self.testIsRun = True
        self.setComponentAvail(False)
        # self.tt = Thread(name='testTimer', target=TestTime, args=(self,))
        # self.tt = TestTime(self)
        # self.tt.start()

    def on_finishedSet(self):
        self.testIsRun = False
        self.setComponentAvail(True)

    def setComponentAvail(self, status):
        self.rfbTypeCombo.setEnabled(status)
        self.rfbSN.setEnabled(status)
        self.testsGroupBox.setEnabled(status)
        self.instrumentsGroupBox.setEnabled(status)
        self.gainTestgroupBox.setEnabled(status)
        self.dsaGroupBox.setEnabled(status)
        self.rfbAtrGroupBox.setEnabled(status)
        self.calibrationGroupBox.setEnabled(status)
        self.applySetBtn.setEnabled(status)
        self.instrAddrCombo.setMouseTracking(status)
        self.testTypeCombo.setEnabled(status)

    def startThreadTest(self):
        if self.calibrLbl.text() == 'False':
            self.sendMsg('w', 'Warning', 'Need to do the calibration', 1)
            return
        if self.checkRecordInDb():
            if not self.testIsRun:
                self.isItCalibr = False
                self.myThread = TestContoller(self)
                self.myThread.logSignal.connect(self.sendLog, QtCore.Qt.QueuedConnection)
                self.myThread.resSignal.connect(self.tableResultAddItem, QtCore.Qt.QueuedConnection)
                self.myThread.msgSignal.connect(self.sendMsg, QtCore.Qt.QueuedConnection)
                self.myThread.dsaResSignal.connect(self.set_DSAtoSql, QtCore.Qt.QueuedConnection)
                self.myThread.fillTestLogSignal.connect(self.fillTestLog, QtCore.Qt.QueuedConnection)
                self.myThread.progressBarSignal.connect(self.setProgressBar, QtCore.Qt.QueuedConnection)
                self.myThread.comMovieSignal.connect(self.setComMovie, QtCore.Qt.QueuedConnection)

                self.myThread.started.connect(self.on_started)
                self.myThread.finished.connect(self.on_finished)
                self.myThread.start()
            else:
                q = self.sendMsg('i', 'Stop test', 'Are you sure?', 2)
                if q == QMessageBox.Ok:
                    self.myThread.stopTestFlag = True
                    while self.myThread.isRunning():
                        self.setProgressBar('Canceling', 0, 0)
                    self.setProgressBar('Canceled', 100, 100)

    def on_started(self):
        self.testIsRun = True
        self.answer = None
        if self.testLogDl.get('SN') not in [self.rfbSN.text(), None]:
            self.testLogDl = {}
        if self.testLogUl.get('SN') not in [self.rfbSN.text(), None]:
            self.testLogUl = {}
        if self.testLogDl == {} and self.testLogUl == {}:
            self.clrLogBtnClick()
        self.setComponentAvail(False)
        self.startTestBtn.setText('Stop')
        # self.tt = threading.Thread(name='testTimer', target=TestTime, args=(self,))
        # self.tt.start()
        q = "update settings set lastRfbType = '%s', lastRfbSn = '%s'" % (str(self.rfbTypeCombo.currentText()),
                                                                          str(self.rfbSN.text()))
        self.updateDbQuery(q)

    def on_finished(self):
        Journal(self)
        self.testIsRun = False
        self.whatConn = None
        self.setComponentAvail(True)
        self.startTestBtn.setText('Start')
        self.setProgressBar('Done', 100, 100)

        x = len(self.testLogDl) + len(self.testLogUl) + len(self.to_DsaUlDl)
        if not self.toBeOrNotToBe() and x != 0:
            q = self.sendMsg('i', 'RFBcheck', 'Connect second side of the RF board and press Ok', 2)
            if q == QMessageBox.Ok:
                self.startThreadTest()
            if q == QMessageBox.Cancel:
                # clear result dictionary
                self.testLogDl = {}
                self.testLogUl = {}
                self.to_DsaUlDl = {}

    def stormFufuTest(self):
        self.myThread = StormFufuTest(self)
        self.myThread.msgSignal.connect(self.sendMsg, QtCore.Qt.QueuedConnection)
        self.myThread.start()


    def isNeedLoadSetFile(self):
        try:
            conn, cursor = self.getConnDb()
            lastRfb = cursor.execute("select lastRfbType from settings").fetchone()[0]
            if lastRfb != self.rfbTypeCombo.currentText():
                q = self.sendMsg('q', 'Load set file', 'Do you want load default file\n'
                                                       'settings for RF board %s ?' %
                                 str(self.rfbTypeCombo.currentText()), 2)
                if q == QMessageBox.Ok:
                    pass
                    # self.startThreadLoadSet(False)
                return True
        except Exception as e:
            self.sendMsg('w', 'Load set file error', str(e), 1)
            return False

    def setProgressBar(self, testName, barMax, barCurr):
        if self.currTestLbl.text() != testName:
            self.currTestLbl.setText(testName)
            self.TestPrBar.setMaximum(barMax)
            self.TestPrBar.setValue(0)
        self.TestPrBar.setValue(barCurr)

    def set_DSAtoSql(self, key, value):
        self.to_DsaUlDl.update({key: value})

    def tableResultAddItem(self, mesname, dlul, mesmin, mes, mesmax, status):
        numrows = self.tableResult.rowCount()
        findRow = False
        for i in range(numrows):
            if self.tableResult.item(i, 0).text() == mesname and \
                    self.tableResult.item(i, 1).text() == dlul:
                numrows = i
                findRow = True
                break
        if not findRow or self.tableResult.rowCount() == 0:
            self.tableResult.insertRow(numrows)
        self.tableResult.setItem(numrows, 0, QTableWidgetItem(mesname))
        self.tableResult.setItem(numrows, 1, QTableWidgetItem(dlul))
        self.tableResult.setItem(numrows, 2, QTableWidgetItem(mesmin))
        self.tableResult.setItem(numrows, 3, QTableWidgetItem(mes))
        self.tableResult.setItem(numrows, 4, QTableWidgetItem(mesmax))
        if status == 1:
            icon = QtGui.QIcon(self.passImg)
        elif status == 0:
            icon = QtGui.QIcon(self.failImg)
        else:
            icon = QtGui.QIcon(self.warnImg)
        self.tableResult.setItem(numrows, 5, QTableWidgetItem(icon, ""))
        item = self.tableResult.item(numrows, 0)
        self.tableResult.scrollToItem(item, QAbstractItemView.PositionAtTop)
        self.tableResult.selectRow(numrows)

    def sendLog(self, msg, clr):
        self.listLog.addItem(msg)
        numrows = len(self.listLog)
        if clr == -1:
            self.listLog.item(numrows - 1).setForeground(QtCore.Qt.red)
        if clr == 1:
            self.listLog.item(numrows - 1).setForeground(QtCore.Qt.darkGreen)
        self.listLog.scrollToBottom()

    def fillTestLog(self, key, val):
        if self.myThread.whatConn == 'Dl':
            self.testLogDl.update({key: val})
        elif self.myThread.whatConn == 'Ul':
            self.testLogUl.update({key: val})
        else:
            self.sendLog('fillTestLog Error: ' + str(self.myThread.whatConn) + ' | ' + key + ' : ' + val, 0)

    def setComMovie(self, port, baud):
        if port != '' and baud != '':
            self.baudLbl.setText(str(baud))
            self.portLbl.setText(str(port))
            self.connectMovie.setScaledSize(QSize(30, 30))
            self.movie.setMovie(self.connectMovie)
            self.connectMovie.start()
            self.movie.setVisible(True)
        else:
            self.baudLbl.setText('')
            self.portLbl.setText('')
            self.movie.setVisible(False)

    def toBeOrNotToBe(self):
        dlMustToBe = ulMustToBe = dlPresent = ulPresent = False
        if self.atrSettings.get('freq_band_dl_1').find('@') != -1 or \
                self.atrSettings.get('freq_band_dl_2').find('@') != -1:
            dlMustToBe = True
        if self.atrSettings.get('freq_band_ul_1').find('@') != -1 or \
                self.atrSettings.get('freq_band_ul_2').find('@') != -1:
            ulMustToBe = True
        if dlMustToBe and len(self.testLogDl) > 0:
            dlPresent = True
        if ulMustToBe and len(self.testLogUl) > 0:
            ulPresent = True

        if (dlMustToBe != dlPresent) or (ulMustToBe != ulPresent):
            return False
        elif dlMustToBe == dlPresent and ulMustToBe == ulPresent:
            return True

    def onResize(self, event):
        tables = [self.tableResult, self.tableJournal]
        for i in tables:
            table_width = i.viewport().size().width()
            cols = i.columnCount() or 1
            width = table_width/cols
            for j in range(i.columnCount()):
                i.setColumnWidth(j, width)

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            self.hotKey.append(event.key())
            if len(self.hotKey) > 3:
                self.hotKey.pop(0)
            if sum(self.hotKey) == 33554582:
                self.journal.deleteRecords()
                self.hotKey = []
        if event.type() == QtCore.QEvent.MouseMove:
            try:
                source.setToolTip(visa.ResourceManager().open_resource(source.currentText()).query('*IDN?'))
            except:
                source.setToolTip('Instrument not connected')
        return QtWidgets.QMainWindow.eventFilter(self, source, event)

    def getSnViaScanner(self):
        r = re.findall('[A-Z0-9]+', self.rfbSN.text())
        if len(r) < 2:
            self.sendMsg('w', 'RFBCheck', 'Incorrect serial number', 1)
            self.rfbSN.clear()
            return
        rfType = str(r[0])
        rfSn = str(r[len(r)-1])
        allItems = [self.rfbTypeCombo.itemText(i) for i in range(self.rfbTypeCombo.count())]
        isFound = False
        for x, i in enumerate(allItems):
            if i == rfType:
                self.rfbTypeCombo.setCurrentIndex(x)
                self.rfbIsChecked()
                isFound = True
                break
        if isFound:
            self.rfbSN.setText(rfSn)
        else:
            self.sendMsg('i', 'RFBCheck', 'RF ' + rfType + " not found", 1)

    def setTestsList(self):
        self.tableModel = QtGui.QStandardItemModel(self)
        # self.tableModel.itemChanged.connect(self.itemChanged)
        conn, cursor = self.getConnDb()
        query = "select name from test_list where type = '%s' order by queue" % self.testTypeCombo.currentText()
        rows = cursor.execute(query).fetchall()
        for row in rows:
            item = QtGui.QStandardItem(row[0])
            item.setCheckable(True)
            item.setCheckState(2)
            self.tableModel.appendRow(item)

        self.testTable.setModel(self.tableModel)
        self.testTable.resizeRowsToContents()
        self.testTable.setColumnWidth(0, 300)
        conn.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = QtWidgets.QMainWindow()
    prog = mainProgram(form)
    form.setWindowIcon(prog.appIcon)
    # form.setWindowTitle(prog.setUser())
    form.show()
    app.exec_()
    # sys.exit(app.exec_())
    sys.exit(0)
