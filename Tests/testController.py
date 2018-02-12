import serial
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QMessageBox

from Equip.writeTestResult import WriteResult
from Tests.gain_test import GainTest
from Tests.flatness_test import FlatnessTest
from Tests.dsa_test import DsaTest
from Tests.intermod_test import IModTest
from Tests.bitAlarm_test import BitAlarmTest
from Tests.alc_test import AlcTest
from Equip.equip import *
from Equip.instrument import *
import Equip.commands as cmd


class TestContoller(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(str, int)
    resSignal = QtCore.pyqtSignal(str, str, str, str, str, int)
    conSignal = QtCore.pyqtSignal()
    msgSignal = QtCore.pyqtSignal(str, str, str, int)
    dsaResSignal = QtCore.pyqtSignal(str, dict)
    progressBarSignal = QtCore.pyqtSignal(str, float, float)
    fillTestLogSignal = QtCore.pyqtSignal(str, str)
    comMovieSignal = QtCore.pyqtSignal(str, str)

    def __init__(self, currParent, parent=None):
        QtCore.QThread.__init__(self, parent)

        self.currentThread = QtCore.QThread.currentThread()
        self.controller = self
        self.currParent = currParent  # main program
        self.testArr = []  # checked tests
        self.ser = None  # Com port connection
        self.instr = None  # instruments
        self.whatConn = None  # Ul/Dl
        self.listSettings = currParent.listSettings
        self.stopTestFlag = False
        self.haveConn = False
        self.useCorrection = False

        # self.connectMovie = QMovie('Img/connect2.gif')
        # self.connectMovie.setScaledSize(QSize(30, 30))
        # self.connectMovie.start()
        # self.currParent.movie.setMovie(self.connectMovie)

        # TODO: move testLog to main or db. main better i think
        # try:
        #     self.testLogDl.get('SN')
        #     self.testLogUl.get('SN')
        # except AttributeError:
        #     self.testLogDl = {}
        #     self.testLogUl = {}

        self.getTests(currParent)

    def run(self):
        # TODO: com port and instrument initialisation problem
        if len(self.testArr) is 0:
            # self.sendMsg('w', "Warning", "You have to choice minimum one test", 1)
            self.msgSignal.emit('w', "Warning", "You have to choice minimum one test", 1)
            return
        self.getComConn()
        if self.haveConn:
            self.whatConn = self.checkUlDl()
        else:
            return

        if self.whatConn is None:
            return

        self.logSignal.emit('START TEST', 0)
        self.instr.gen.write(":OUTP:STAT ON")
        self.stopTestFlag = False
        self.runTests()

        self.ser.close()
        self.comMovieSignal.emit('', '')
        self.instr.gen.write(":OUTP:STAT OFF")
        self.instr.sa.write("CALC:MARK:CPS 0")
        self.writeResults()

    def runTests(self):
        if self.currParent.checkGainTest.isChecked():
            if self.stopTestFlag:
                return
            GainTest(self)

        if self.currParent.checkGainTest.isChecked():
            if self.stopTestFlag:
                return
            FlatnessTest(self)

        if self.currParent.checkDsaTest.isChecked():
            if self.stopTestFlag:
                return
            DsaTest(self)

        if self.currParent.checkImTest.isChecked():
            if self.stopTestFlag:
                return
            IModTest(self)

        if self.currParent.checkBitAlarmTest.isChecked():
            if self.stopTestFlag:
                return
            BitAlarmTest(self, self.currParent)

        if self.currParent.checkAlcTest.isChecked():
            if self.stopTestFlag:
                return
            AlcTest(self, self.currParent)
        self.progressBarSignal.emit('Done', 100, 100)

    def getTests(self, currParent):
        if currParent.checkGainTest.isChecked():
            self.testArr.append('Gain test')
        if currParent.checkGainTest.isChecked():
            self.testArr.append('Flatness test')
        if currParent.checkDsaTest.isChecked():
            self.testArr.append('DSA test')
        if currParent.checkImTest.isChecked():
            self.testArr.append('IM test')
        if currParent.checkBitAlarmTest.isChecked():
            self.testArr.append('Alarm test')
        if currParent.checkAlcTest.isChecked():
            self.testArr.append('AlcTest')

    def getComConn(self):
        baud = 57600
        port = "COM1"
        try:
            self.ser = serial.Serial(port, baud, timeout=0.5)
            if self.ser.isOpen():
                self.ser.write(binascii.unhexlify('AAAA543022556677403D01'))
                rx = binascii.hexlify(self.ser.readline())
                band = int(rx[26:34], 16) / 1000
                print(band)
                self.comMovieSignal.emit(str(self.ser.port), str(self.ser.baudrate))
                self.logSignal.emit("Connected to port " + str(self.ser.port), 0)
                self.haveConn = True
        except Exception as e:
            self.haveConn = False
            self.logSignal.emit('Connection problem: ' + str(e), 1)
            self.comMovieSignal.emit('', '')
            self.msgSignal.emit('c', 'Connection problem', str(e), 1)
            if self.ser is not None:
                if self.ser.isOpen():
                    self.ser.close()

    def getParent(self):
        return self.currParent

    def checkUlDl(self):
        self.ser.write(binascii.unhexlify(cmd.setSalcOpMode))
        self.ser.write(binascii.unhexlify(cmd.reset))
        setAlc(self.ser, cmd.setAlcInDl, 255, cmd.shiftDlIn)
        setAlc(self.ser, cmd.setAlcInUl, 255, cmd.shiftUlIn)
        setAlc(self.ser, cmd.setAlcInDl, 255, cmd.shiftDlOut)
        setAlc(self.ser, cmd.setAlcInUl, 255, cmd.shiftUlOut)

        setDSA(self.ser, cmd, 'Dl', self.currParent.listSettings[5], self.currParent.listSettings[6],
               self.currParent.listSettings[7])
        setDSA(self.ser, cmd, 'Ul', self.currParent.listSettings[8], self.currParent.listSettings[9],
               self.currParent.listSettings[10])

        self.whatConn = None
        Dl = self.currParent.listSettings[1]
        Ul = self.currParent.listSettings[2]

        for i in [Dl, Ul]:
            self.progressBarSignal.emit('Check connection', 0, 0)
            if i == 0:
                continue
            try:
                self.instr = Instrument(i, self.currParent)
                if self.instr is None:
                    self.stopTestFlag = True
                    return
            except Exception as e:
                self.currParent.sendMsg('c', 'Instrument initialisation error', str(e), 1)
            self.instr.gen.write(":OUTP:STAT ON")
            time.sleep(3)
            if float(getAvgGain(self)) > -50:
                if i == Dl:
                    self.logSignal.emit("Testing DownLink", 0)
                    self.whatConn = "Dl"
                    self.fillTestLogSignal.emit('SN', str(self.currParent.rfbSN.text()))
                    self.fillTestLogSignal.emit('RF', str(self.currParent.rfbTypeCombo.currentText()))
                    break
                elif i == Ul:
                    self.logSignal.emit("Testing UpLink", 0)
                    self.whatConn = "Ul"
                    self.fillTestLogSignal.emit('SN', str(self.currParent.rfbSN.text()))
                    self.fillTestLogSignal.emit('RF', str(self.currParent.rfbTypeCombo.currentText()))
                    break
        if self.whatConn is None:
            self.logSignal.emit("No signal", 2)
            self.whatConn = None
            self.ser.close()
            self.comMovieSignal.emit('', '')
            return
        self.instr.gen.write(":OUTP:STAT OFF")
        time.sleep(1)
        return self.whatConn

    def writeResults(self):
        dlMustToBe = ulMustToBe = dlPresent = ulPresent = False
        if self.currParent.atrSettings.get('freq_band_dl_1').find('@') != -1 or self.currParent.atrSettings.get(
                'freq_band_dl_2').find('@') != -1:
            dlMustToBe = True
        if self.currParent.atrSettings.get('freq_band_ul_1').find('@') != -1 or self.currParent.atrSettings.get(
                'freq_band_ul_2').find('@') != -1:
            ulMustToBe = True
        if dlMustToBe and len(self.currParent.testLogDl) > 0:
            dlPresent = True
        if ulMustToBe and len(self.currParent.testLogUl) > 0:
            ulPresent = True
        if (dlMustToBe and not dlPresent) or (ulMustToBe and not ulPresent):
            self.msgSignal.emit('i', 'RFBcheck', 'Connect second side of the RF', 1)
        elif dlMustToBe == dlPresent and ulMustToBe == ulPresent:
            self.msgSignal.emit('i', 'RFBcheck', 'Test complete', 1)
            if self.currParent.rfbSN.text().upper() != 'XXXX':
                WriteResult(self, self.currParent.testLogDl, self.currParent.testLogUl)

