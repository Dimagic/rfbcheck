import csv
import logging
import os
import serial
from PyQt5 import QtCore, QtGui

from Tests.detector_test import DetectorTest
from Tests.gain_test import GainTest
from Tests.flatness_test import FlatnessTest
from Tests.dsa_test import DsaTest
from Tests.intermod_test import IModTest
from Tests.bitAlarm_test import BitAlarmTest
from Tests.alc_test import AlcTest
from Tests.rloss_test import ReturnLossTest

from Equip.selectComPort import SelectComPort
from Equip.writeTestResult import WriteResult
from Equip.equip import *
from Equip.instrument import *
import Equip.commands as cmd


class TestContoller(QtCore.QThread, SelectComPort):
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

        LOG_FILENAME = './rfbcheck.log'
        logging.basicConfig(filename=LOG_FILENAME, level=logging.ERROR)
        logging.debug('This message should go to the log file')

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
        self.getTests(currParent)

    def run(self):
        if len(self.testArr) is 0:
            self.sendMsg('w', "Warning", "You have to choice minimum one test", 1)
            return
        try:
            self.getComConn()
            if self.haveConn:
                self.whatConn = self.checkUlDl()
            else:
                return
            if self.whatConn is None:
                return
            if self.stopTestFlag:
                self.ser.close()
                return
            # TODO: send message if load set file is fail
            self.readAdemSettings()
            self.logSignal.emit('START TEST', 0)
            self.instr.gen.write(":OUTP:STAT ON")
            self.stopTestFlag = False
            self.runTests()
        except Exception as e:
            self.stopTestFlag = True
            self.sendMsg('c', 'Test error', str(e), 1)
            logging.exception(str(self.currParent.startTestTime) + ": " +
                              self.currParent.rfbTypeCombo.currentText() + " " + self.currParent.rfbSN.text())
            self.ser.close()
            self.comMovieSignal.emit('', '')
            return
        else:
            self.ser.close()
            self.comMovieSignal.emit('', '')
            self.instr.gen.write(":OUTP:STAT OFF")
            self.instr.sa.write("CALC:MARK:CPS 0")
            self.writeResults()

    def runTests(self):

        if 'Gain + flatness' in self.testArr:
            if self.stopTestFlag:
                return
            GainTest(self)

        if 'Gain + flatness' in self.testArr:
            if self.stopTestFlag:
                return
            FlatnessTest(self)

        if 'DSA' in self.testArr:
            if self.stopTestFlag:
                return
            DsaTest(self)

        if 'IMod' in self.testArr:
            if self.stopTestFlag:
                return
            IModTest(self)

        if 'BIT alarm' in self.testArr:
            if self.stopTestFlag:
                return
            BitAlarmTest(self, self.currParent)

        if 'ALC' in self.testArr:
            if self.stopTestFlag:
                return
            AlcTest(self, self.currParent)

        if 'Return loss' in self.testArr:
            if self.stopTestFlag:
                return
            ReturnLossTest(self)

        if 'Forw. detector' in self.testArr or 'Rev. detector' in self.testArr:
            if self.stopTestFlag:
                return
            DetectorTest(self)

        self.progressBarSignal.emit('Done', 100, 100)
        # print(self.currParent.testLogDl)

    def getTests(self, currParent):
        model = currParent.testTable.model()
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            item = model.item(i, 0)
            if item.checkState() == 2:
                self.testArr.append(model.data(index))

    def getComConn(self):
        port, baud = self.getCurrPortBaud()
        try:
            self.ser = serial.Serial(port, int(baud), timeout=0.5)
            if self.ser.isOpen():
                self.ser.write(binascii.unhexlify('AAAA543022556677403D01'))
                time.sleep(.5)
                tx = binascii.hexlify(self.ser.readline())
                if tx == b'':
                    raise serial.portNotOpenError
                self.comMovieSignal.emit(str(self.ser.port), str(self.ser.baudrate))
                self.logSignal.emit("Connected to port " + str(self.ser.port), 0)
                self.haveConn = True
        except Exception as e:
            self.haveConn = False
            self.logSignal.emit('Connection problem: ' + str(e), -1)
            self.comMovieSignal.emit('', '')
            self.sendMsg('c', 'Connection problem', 'Connection to\n'
                                                    'port: ' + port + '\n'
                                                    'baud: ' + baud + '\n'
                                                    'Fail: ' + str(e), 1)
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
        self.progressBarSignal.emit('Check connection', 0, 0)

        for i in [Dl, Ul]:
            if self.stopTestFlag:
                return
            if i == 0:
                continue
            try:
                self.instr = Instrument(i, self.currParent)
                if self.instr is None:
                    self.stopTestFlag = True
                    return
            except Exception as e:
                self.sendMsg('c', 'Instrument initialisation error', str(e), 1)

            if self.currParent.gainSA.isChecked():
                self.instr.gen.write(":OUTP:STAT ON")
                time.sleep(3)
                gain = float(getAvgGain(self))
                self.instr.gen.write(":OUTP:STAT OFF")
                time.sleep(1)
                if gain > -50:
                    uldl = True
                else:
                    uldl = False
            else:
                self.instr.na.write(":SENS1:FREQ:CENT " + str(i) + "E6")
                self.instr.na.write(":SENS1:FREQ:SPAN 30E6")
                self.instr.na.write(":CALC1:PAR1:DEF S12")
                self.instr.na.write(":CALC1:MARK1 ON")
                self.instr.na.write(":CALC1:MARK1:X " + str(i) + 'E6')
                time.sleep(2)
                self.instr.na.write(":CALC1:MARK1:X " + str(i) + 'E6')
                gain = self.instr.na.query(":CALC1:MARK1:Y?")
                gain = gain[:gain.find(',')]
                gain = round(float(gain), 2)
                if gain > 0:
                    uldl = True
                else:
                    uldl = False
            if uldl:
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
        else:
            return self.whatConn

    def writeResults(self):
        if self.currParent.toBeOrNotToBe():
            self.msgSignal.emit('i', 'RFBcheck', 'Test complete', 1)
            if self.currParent.rfbSN.text().upper() != 'XXXX':
                WriteResult(self, self.currParent.testLogDl, self.currParent.testLogUl)

    def sendMsg(self, icon, msgTitle, msgText, typeQestions):
        self.msgSignal.emit(icon, msgTitle, msgText, typeQestions)
        while self.currParent.answer is None:
            time.sleep(.05)
        else:
            forReturn = self.currParent.answer
            self.currParent.answer = None
            return forReturn

    def readAdemSettings(self):
        # stm32f103vet6
        try:
            file = os.path.join(os.path.dirname(__file__), '..', 'setFiles',
                                self.currParent.rfbTypeCombo.currentText() + '.CSV')
            f = open(file, 'r')
            f.close()
        except Exception as e:
            self.sendMsg('w', 'Can\'t open file settings', str(e), 1)
            self.stopTestFlag = True
            return

        valuesDict = {}
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                keyVal = row.get('# 0 1182685875')
                if keyVal == '# Do not delete above this line!':
                    continue
                # if keyVal[:4] != 'ALC_':
                #     continue
                lenNewArr = int(row.get(None)[3])
                arr = row.get(None)[4:4 + lenNewArr]
                valuesDict.update({keyVal: arr})
