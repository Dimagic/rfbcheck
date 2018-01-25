# RFBCheck
# v0.1.23 20180124

from Forms.form import Ui_MainWindow
from Tests.testController import *
from Equip.applySetFile import *
from Equip.calibration import *
from Equip.journal import *
from Equip.printReport import *
from Equip.editRFB import *
from Tests.bitAlarm_test import *
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
import threading


class TestTime(threading.Thread):
    def __init__(self, parent):
        startTime = datetime.datetime.now()
        while parent.testIsRun:
            timeTest = datetime.datetime.now() - startTime
            parent.testTimeLbl.setText(str(timeTest)[:7])
            time.sleep(.5)


class mainProgram(QtWidgets.QMainWindow, QtCore.QObject, Ui_MainWindow):
    def __init__(self, form, parent=None):
        super(mainProgram, self).__init__(parent)

        self.useCorrection = True
        self.testLogDl = {}
        self.testLogUl = {}

        self.runTest = None
        self.listSettings = []

        self.calibrSaToGen = {}
        self.calibrGenToSa = {}

        self.myThread = None

        self.to_DsaUlDl = {}
        self.to_DsaResult = {}

        self.atrSettings = {}
        self.instr = None
        self.setupUi(form)

        self.TestPrBar.setValue(0)
        self.whatConn = None
        self.band = None

        self.stopTestFlag = False
        self.testIsRun = False

        self.col = ['RFB type', 'DL c.freq', 'UL c.freq', 'DL IM pow', 'UL IM pow', 'DL DSA1', 'DL DSA2', 'DL DSA3',
                    'UL DSA1', 'UL DSA2', 'UL DSA3', 'DSA pow', 'ALC IN pow']

        self.radioInstrChecked()
        listInstr = self.getInstrAddr()

        if len(listInstr) < 2:
            self.sendLog('Problem of instruments initialisation', 2)
        for i in listInstr:
            self.instrAddrCombo.addItem(str(i))
        self.getCurrInstrAddr()
        self.setInstrBtn.clicked.connect(self.setCurrInstrAddr)
        self.journalUpdateBtn.clicked.connect(self.journalUpdateBtnClick)
        self.tableJournal.clicked.connect(self.getSelectedRow)
        self.printReportBtn.clicked.connect(self.printReportBtnClicked)

        self.clrLogBtn.clicked.connect(self.clrLogBtnClick)
        self.connectComBtn.clicked.connect(self.connectComBtnClick)
        self.connectComBtn.setText("Connect")
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
        self.applySetBtn.clicked.connect(self.applySetFile)

        self.startTestBtn.setEnabled(False)
        self.applySetBtn.setEnabled(False)

        conn, cursor = self.getConnDb()
        rfbList = cursor.execute("select name from rfb_type order by name")

        for i in rfbList:
            self.rfbTypeCombo.addItem(str(i).replace("('", "").replace("',)", ""))
            if len(self.editRfbCombo) == 0: self.editRfbCombo.addItem('New')
            self.editRfbCombo.addItem(str(i).replace("('", "").replace("',)", ""))

        rep = Report(None, None, None, self)
        rep.getTemplates(self)

        self.rfbIsChecked()
        self.rfbTypeCombo.activated.connect(self.rfbIsChecked)

        self.journalDateStart.setDate(QtCore.QDate.currentDate().addMonths(-1))
        self.journalDateStop.setDate(QtCore.QDate.currentDate())

        self.newRfbBtn.clicked.connect(self.on_newRfbBtn_clicked)

        conn.close()
        Journal(self)

    def on_newRfbBtn_clicked(self):
        self.dialog = EditRFB(self, self)
        self.dialog.setWindowIcon(QtGui.QIcon("Img/ico32_pgn_icon.ico"))
        self.dialog.show()

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

    def calibrationBtnClick(self):
        self.t = Thread(name='calibration', target=Calibration, args=(self,))
        self.t.start()

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
                self.sendMsg('c', 'Querry error', str(err), 0)
                conn.close()

    def connectComBtnClick(self):
        pass

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
                    'UL DSA1', 'UL DSA2', 'UL DSA3', 'DSA pow', 'ALC IN pow']
        rows = cursor.execute("select * from test_settings where rfb_type = :n",
                              {'n': self.rfbTypeCombo.currentText()}).fetchall()
        # TODO: if not fined setting??? need error
        for rowSetttings in rows:
            self.listSettings = list(rowSetttings)[1:]
        conn.close()

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
        return sqlite3.connect('rfb.db')

    def timeNow(self):
        return str(datetime.datetime.today().strftime("%H:%M:%S"))

    def startBtnEnabled(self):
        if ((self.rfbSN.text().isdigit() == True and len(self.rfbSN.text()) >= 8)
                or (self.rfbSN.text().upper() == 'XXXX')):
            self.startTestBtn.setEnabled(True)
        else:
            self.startTestBtn.setEnabled(False)

    def applySetFile(self):
        applySetFile(self.rfbTypeCombo.currentText(), self)

    def sendMsg(self, icon, msgTitle, msgText, typeQestions):
        # TODO: threading problem "QApplication: Object event filter cannot be in a different thread."
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
        msg.setWindowIcon(QtGui.QIcon("Img/ico32_pgn_icon.ico"))
        if typeQestions == 1:
            msg.setStandardButtons(QMessageBox.Ok)
        elif typeQestions == 2:
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        elif typeQestions == 3:
            msg.setStandardButtons(QMessageBox.Ignore | QMessageBox.Retry | QMessageBox.Cancel)
        return msg.exec_()

    def getInstrAddr(self):
        return (visa.ResourceManager().list_resources())

    def getConnDb(self):
        try:
            conn = self.connectDb()
            cursor = conn.cursor()
            return conn, cursor
        except Exception as e:
            self.sendLog(str(e), 2)

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
            self.genAtten.setText(str(row[1]))
            self.currNaNameLbl.setText(str(row[2]))
        conn.close()

    def radioInstrChecked(self):
        if self.setSaRadio.isChecked() == True:
            self.saAtten.setEnabled(True)
            self.genAtten.setEnabled(False)
        if self.setGenRadio.isChecked() == True:
            self.saAtten.setEnabled(False)
            self.genAtten.setEnabled(True)
        if self.setNaRadio.isChecked() == True:
            self.saAtten.setEnabled(False)
            self.genAtten.setEnabled(False)

    def setCurrInstrAddr(self):
        conn, cursor = self.getConnDb()
        try:
            if self.setSaRadio.isChecked():
                self.currSaNameLbl.setText(getInstrName(self.instrAddrCombo.currentText()))
                cursor.execute("update instruments set address = :n, useAtten = :n2, fullName = :n3 where name = 'SA'",
                               {'n': self.instrAddrCombo.currentText(), 'n2': int(self.saAtten.text()),
                                'n3': self.currSaNameLbl.text()})

            elif self.setGenRadio.isChecked():
                self.currGenNameLbl.setText(getInstrName(self.instrAddrCombo.currentText()))
                cursor.execute("update instruments set address = :n, useAtten = :n2, fullName = :n3 where name = 'GEN'",
                               {'n': self.instrAddrCombo.currentText(), 'n2': int(self.genAtten.text()),
                                'n3': self.currGenNameLbl.text()})

            elif self.setNaRadio.isChecked():
                self.currNaNameLbl.setText(getInstrName(self.instrAddrCombo.currentText()))
                cursor.execute("update instruments set address = :n, useAtten = :n2, fullName = :n3 where name = 'NA'",
                               {'n': self.instrAddrCombo.currentText(), 'n2': 0, 'n3': self.currNaNameLbl.text()})
            else:
                pass
                # TODO: ERROR (set current instrument address)
            conn.commit()
        except Exception as e:
            conn.close()
            self.sendMsg('w', "Warning", str(e), 1)
        else:
            conn.close()
            self.getCurrInstrAddr()

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
        except Exception as e:
            self.sendMsg('w', 'Warning', 'Incorrect value of attenuator', 1)

    def checkRecordInDb(self):
        conn, cursor = self.getConnDb()
        try:
            row = cursor.execute("select rfb_type from test_results where sn = :n1",
                                 {'n1': self.rfbSN.text()}).fetchone()
            conn.close()
            if row != None and row[0] != self.rfbTypeCombo.currentText():
                self.sendMsg('w', 'Warning',
                             'SN: ' + str(self.rfbSN.text()) + ' already exist. RFB type: ' + str(row[0]), 1)
                # self.startTestBtn.setText("Start")
                return False
            else:
                return True
        except sqlite3.DatabaseError as err:
            self.sendMsg('c', 'Querry error', str(err), 1)
            conn.close()

    # Run tests ----------------------------------------------------------------
    def startThreadTest(self):
        print(self.startTestBtn.text())

        if self.calibrLbl.text() == 'False':
            self.sendMsg('w', 'Warning', 'Need to do the calibration', 1)
            return
        if self.checkRecordInDb():
            if self.startTestBtn.text() == "Start":
                self.isItCalibr = False
                self.myThread = TestContoller(self)
                self.myThread.logSignal.connect(self.sendLog, QtCore.Qt.QueuedConnection)
                self.myThread.resSignal.connect(self.tableResultAddItem, QtCore.Qt.QueuedConnection)
                self.myThread.msgSignal.connect(self.sendMsg, QtCore.Qt.QueuedConnection)
                self.myThread.dsaResSignal.connect(self.set_DSAtoSql, QtCore.Qt.QueuedConnection)
                self.myThread.progressBarSignal.connect(self.setProgressBar, QtCore.Qt.QueuedConnection)

                self.myThread.started.connect(self.on_started)
                self.myThread.finished.connect(self.on_finished)
                self.myThread.start()
            elif self.startTestBtn.text() == "Stop":
                if self.sendMsg('i', 'Stop test', 'Are you sure?', 2) == QMessageBox.Ok:
                    self.myThread.stopTestFlag = True
            else:
                self.sendMsg('c', 'Error', 'Starting thread is fail', 1)

    # Signals procedures -------------------------------------------------------
    def on_started(self):
        self.testIsRun = True
        self.tt = Thread(name='testTimer', target=TestTime, args=(self,))
        self.tt.start()
        if self.testLogDl.get('SN') != self.rfbSN.text() or self.testLogUl.get('SN') != self.rfbSN.text():
            self.clrLogBtnClick()

        self.rfbTypeCombo.setEnabled(False)
        self.rfbSN.setEnabled(False)
        self.testsGroupBox.setEnabled(False)
        self.startTestBtn.setText('Stop')

    def on_finished(self):
        self.testIsRun = False
        self.whatConn = None
        self.rfbTypeCombo.setEnabled(True)
        self.rfbSN.setEnabled(True)
        self.testsGroupBox.setEnabled(True)
        self.startTestBtn.setText('Start')

    def setProgressBar(self, testName, barMax, barCurr):
        if self.currTestLbl.text() != testName:
            self.currTestLbl.setText(testName)
            self.TestPrBar.setMaximum(barMax)
            self.TestPrBar.setValue(0)

        self.TestPrBar.setValue(barCurr)

    def set_DSAtoSql(self, key, value):
        self.to_DsaResult.update({key: value})

    def tableResultAddItem(self, mesname, dlul, mesmin, mes, mesmax, status):
        numrows = self.tableResult.rowCount()
        self.tableResult.insertRow(numrows)
        self.tableResult.setItem(numrows, 0, QTableWidgetItem(mesname))
        self.tableResult.setItem(numrows, 1, QTableWidgetItem(dlul))
        self.tableResult.setItem(numrows, 2, QTableWidgetItem(mesmin))
        self.tableResult.setItem(numrows, 3, QTableWidgetItem(mes))
        self.tableResult.setItem(numrows, 4, QTableWidgetItem(mesmax))
        if status == 1:
            icon = QtGui.QIcon(QtGui.QPixmap('Img/pass.png'))
        elif status == 0:
            icon = QtGui.QIcon(QtGui.QPixmap('Img/fail.png'))
        else:
            icon = QtGui.QIcon(QtGui.QPixmap('Img/warning.png'))
        self.tableResult.setItem(numrows, 5, QTableWidgetItem(icon, ""))
        item = self.tableResult.item(numrows, 0)
        self.tableResult.scrollToItem(item, QAbstractItemView.PositionAtTop)
        self.tableResult.selectRow(numrows)

    def sendLog(self, msg, clr):
        self.listLog.addItem(msg)
        numrows = len(self.listLog)
        self.listLog.item(numrows - 1).setBackground(QtCore.Qt.white)
        self.listLog.scrollToBottom()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = QtWidgets.QMainWindow()
    prog = mainProgram(form)
    form.setWindowIcon(QtGui.QIcon("Img/ico32_pgn_icon.ico"))
    form.show()
    app.exec_()
    sys.exit(app.exec_())
