from Equip.equip import *
import Equip.commands as cmd
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore

class DsaTest(QtCore.QThread):
    def __init__(self, testController, mainParent, parent = None):
        super(DsaTest, self).__init__(parent)
        testController.logSignal.emit("***** Start DSA test *****", 3)

        self.parent = mainParent
        self.testController = testController
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.whatConn = testController.whatConn
        self.listSettings = mainParent.listSettings
        self.ser = testController.ser

        # if self.parent.stopTestFlag:
        #     return

        if self.whatConn == 'Dl':
            self.freq = self.listSettings[1]
        else:
            self.freq = self.listSettings[2]

        self.sa.write(":SENSE:FREQ:center "+str(self.freq)+" MHz")
        self.gen.write(":FREQ:FIX "+str(self.freq)+" MHz")
        self.sa.write(":SENSE:FREQ:span 1 MHz")
        if self.parent.testSetDsaShort.isChecked():
            self.forDSAtest = [0, 0.5, 1, 2, 4, 8, 16, 31]
        else:
            self.forDSAtest = np.arange(0, 31.5, 0.5)

        self.parent.useCorrection = False
        self.dsaTest(testController.listSettings, testController, 1)
        self.dsaTest(testController.listSettings, testController, 2)
        self.dsaTest(testController.listSettings, testController, 3)
        self.parent.useCorrection = True
        self.sa.write(":SENSE:FREQ:span 3 MHz")

    def dsaTest(self, listSet, parent, dsaType):
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
            self.testController.logSignal.emit("ERR - DSA test set Dl/Ul fail",2)
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
            parent.sendMsg('c', 'Error', 'Incorrect DSA type', 1)
            return

        setDSA(self.ser, cmd, self.whatConn, dsa1test, dsa2test, dsa3test)

        # set ampl for test
        if listSet[11] != 0:
            parent.instr.gen.write("POW:AMPL "+str(listSet[11])+" dBm")
        else:
            setAmplTo(self.ser, cmd, self.gen, ampl, parent)
            time.sleep(2)
        parent.useCorrection = False

        haveWarning = False
        haveFail = False
        for j, i in enumerate(self.forDSAtest):
            if self.parent.stopTestFlag:
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
            curGain = round(getAvgGain(parent), 2)

            if i == 0:
                d1 = curGain
            delta = round(curGain - d1 + i, 2)
            self.testController.logSignal.emit(dsaName + ': ' + str(i) + '    Gain: ' + str(curGain) +
                                               '    Delta: ' + str(delta), 3)
# if gain more then SA display line
            if dsaType == 1:
                k = '1'
                # self.testController.dsaResSignal.emit(i,delta) #to sql dsa results
                self.testController.to_DsaResult.update({i: delta})
            elif dsaType == 2:
                k = '2'
                # self.testController.dsaResSignal.emit(i,delta) #to sql dsa results
                self.testController.to_DsaResult.update({i: delta})
            else:
                k = '3'
                # self.testController.dsaResSignal.emit(i,delta) #to sql dsa results
                self.testController.to_DsaResult.update({i: delta})
            if abs(delta) > 1 and i < 30:
                haveFail = True
            elif abs(delta) > 0.4 and i < 30:
                haveWarning = True

        # parent.to_DsaUlDl.update({parent.whatConn+k:parent.to_DsaResult})
        self.testController.to_DsaUlDl.update({self.testController.whatConn+k: self.testController.to_DsaResult})
        # print(parent.to_DsaUlDl)
        self.testController.to_DsaResult = {}

        # if have warning or fail
        if not haveWarning:
            self.testController.resSignal.emit(dsaName, parent.whatConn, '', 'Pass', '', 1)
            self.testController.fillTestLogSignal.emit(self.testController.whatConn, dsaName, 'Pass')
        elif haveWarning and not haveFail:
            self.testController.resSignal.emit(dsaName, parent.whatConn, '', 'Warning', '', -1)
            self.fillTestLog(parent, dsaName, 'Warning')
            self.testController.fillTestLogSignal.emit(self.testController.whatConn, dsaName, 'Warning')
        else:
            q = parent.sendMsg('w', 'Warning', '%s test fail' % dsaName, 3)
            if q == QMessageBox.Retry:
                self.dsaTest(self.ser, cmd, self.whatConn, listSet, parent, dsaType)
                return
            elif q == QMessageBox.Cancel:
                parent.startTestBtn.setText('Start')
                parent.stopTestFlag = True
            self.testController.resSignal.emit(dsaName, parent.whatConn, '', 'Fail', '', 0)
            self.testController.fillTestLogSignal.emit(self.testController.whatConn, dsaName, 'Fail')

        setDSA(self.ser, cmd, self.whatConn, dsa1, dsa2, dsa3)

    # def fillTestLog(self, parent, dsaType, status):
    #         if parent.whatConn == 'Dl':
    #             parent.testLogDl.update({dsaType: status})
    #         else:
    #             parent.testLogUl.update({dsaType: status})
