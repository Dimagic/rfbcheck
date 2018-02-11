from Equip.equip import *
import Equip.commands as cmd
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore

class DsaTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(DsaTest, self).__init__(parent)
        testController.logSignal.emit("***** Start DSA test *****", 3)

        self.testController = testController
        self.parent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.whatConn = testController.whatConn
        self.listSettings = self.parent.listSettings
        self.ser = testController.ser
        self.to_DsaResult = {}

        if self.whatConn == 'Dl':
            self.freq = self.listSettings[1]
        else:
            self.freq = self.listSettings[2]

        self.sa.write(":SENSE:FREQ:center "+str(self.freq)+" MHz")
        self.gen.write(":FREQ:FIX "+str(self.freq)+" MHz")
        self.sa.write(":SENSE:FREQ:span 1 MHz")
        self.sa.write("BAND:VID 1 KHZ")
        if self.testController.getParent().testSetDsaShort.isChecked():
            self.forDSAtest = [0, 0.5, 1, 2, 4, 8, 16, 31]
        else:
            self.forDSAtest = np.arange(0, 31.5, 0.5)

        # TODO: useCorrection in main or testController?
        self.testController.useCorrection = False
        self.dsaTest(testController.listSettings, 1)
        self.dsaTest(testController.listSettings, 2)
        self.dsaTest(testController.listSettings, 3)
        self.testController.useCorrection = True
        self.sa.write(":SENSE:FREQ:span 3 MHz")

    def dsaTest(self, listSet, dsaType):
        # TODO: write DSA result to DB fail
        self.ser.write(binascii.unhexlify(cmd.reset))
        time.sleep(1)
        if self.whatConn == "Dl":
            dsa1 = listSet[5]
            dsa2 = listSet[6]
            dsa3 = listSet[7]
            ampl = listSet[3]
        elif self.whatConn == "Ul":
            dsa1 = listSet[8]
            dsa2 = listSet[9]
            dsa3 = listSet[10]
            ampl = listSet[4]
        else:
            self.testController.logSignal.emit("ERR - DSA test set Dl/Ul fail", 2)
            return
        if dsaType == 3:
            dsa1test = toFloat(dsa1) + toFloat(dsa3)
            dsa2test = toFloat(dsa2)
            dsa3test = 0
        elif dsaType == 2:
            dsa1test = toFloat(dsa1) + toFloat(dsa2)
            dsa2test = 0
            dsa3test = toFloat(dsa3)
        elif dsaType == 1:
            dsa1test = 0
            dsa2test = toFloat(dsa2)
            dsa3test = toFloat(dsa3)

        else:
            self.testController.msgSignal.emit('c', 'Error', 'Incorrect DSA type', 1)
            return

        setDSA(self.ser, cmd, self.whatConn, dsa1test, dsa2test, dsa3test)

        # set ampl for test
        if listSet[11] != 0:
            self.testController.instr.gen.write("POW:AMPL "+str(listSet[11])+" dBm")
        else:
            setAmplTo(self.ser, cmd, self.gen, ampl, self.testController)
            time.sleep(2)
        self.testController.useCorrection = False

        haveWarning = False
        haveFail = False
        for j, i in enumerate(self.forDSAtest):
            if self.testController.stopTestFlag:
                setDSA(self.ser, cmd, self.whatConn, dsa1, dsa2, dsa3)
                return

            if dsaType == 3:
                dsaName = 'DSA 3'
                dsa3test = toFloat(i)
            elif dsaType == 2:
                dsaName = 'DSA 2'
                dsa2test = toFloat(i)
            else:
                dsaName = 'DSA 1'
                dsa1test = toFloat(i)

            self.testController.progressBarSignal.emit(dsaName, len(self.forDSAtest)-1, j)

            setDSA(self.ser, cmd, self.whatConn, dsa1test, dsa2test, dsa3test)
            curGain = round(getAvgGain(self.testController), 2)

            if i == 0:
                d1 = curGain
            delta = round(curGain - d1 + i, 2)
            self.testController.logSignal.emit(dsaName + ': ' + str(i) + '    Gain: ' + str(curGain) +
                                               '    Delta: ' + str(delta), 3)
# if gain more then SA display line
            if dsaType == 1:
                k = '1'
                self.to_DsaResult.update({i: delta})
            elif dsaType == 2:
                k = '2'
                self.to_DsaResult.update({i: delta})
            else:
                k = '3'
                self.to_DsaResult.update({i: delta})
            if abs(delta) > 1 and i < 30:
                haveFail = True
            elif abs(delta) > 0.4 and i < 30:
                haveWarning = True

        self.testController.dsaResSignal.emit(self.testController.whatConn+k, self.to_DsaResult)
        self.to_DsaResult = {}

        # if have warning or fail
        if not haveWarning:
            self.testController.resSignal.emit(dsaName, self.testController.whatConn, '', 'Pass', '', 1)
            self.testController.fillTestLogSignal.emit(dsaName, 'Pass')
        elif haveWarning and not haveFail:
            self.testController.resSignal.emit(dsaName, self.testController.whatConn, '', 'Warning', '', -1)
            self.testController.fillTestLogSignal.emit(dsaName, 'Warning')

        else:
            # q = self.testController.msgSignal.emit('w', 'Warning', '%s test fail' % dsaName, 3)
            q = self.parent.sendMsg('w', 'Warning', '%s test fail' % dsaName, 3)
            if q == QMessageBox.Retry:
                self.dsaTest(listSet, dsaType)
                return
            elif q == QMessageBox.Cancel:
                # parent.startTestBtn.setText('Start')
                self.testController.stopTestFlag = True
            self.testController.resSignal.emit(dsaName, self.testController.whatConn, '', 'Fail', '', 0)
            self.testController.fillTestLogSignal.emit(dsaName, 'Fail')

        setDSA(self.ser, cmd, self.whatConn, dsa1, dsa2, dsa3)
