from Equip.equip import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class GainTest(QtCore.QThread):
    def __init__(self, testController, mainParent, parent=None):
        super(GainTest, self).__init__(parent)
        if testController.stopTestFlag:
            QtCore.QThread.yieldCurrentThread()

        testController.logSignal.emit("***** Start Gain test *****", 3)

        self.testController = testController
        self.mainParent = mainParent

        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.freqDl = mainParent.listSettings[1]
        self.freqUl = mainParent.listSettings[2]
        self.whatConn = testController.whatConn

        if self.mainParent.stopTestFlag:
            return
        self.ser = self.testController.ser.ser
        gainDlMin = self.mainParent.atrSettings.get('gain_dl_min')
        gainDlMax = self.mainParent.atrSettings.get('gain_dl_max')
        gainUlMin = self.mainParent.atrSettings.get('gain_ul_min')
        gainUlMax = self.mainParent.atrSettings.get('gain_ul_max')
        if self.testController.whatConn == "Dl":
            testController.testLogDl.update({'SN': self.mainParent.rfbSN.text()})
            self.gainTest(self.freqDl, gainDlMin, gainDlMax)
        elif self.testController.whatConn == "Ul":
            testController.testLogUl.update({'SN': self.mainParent.rfbSN.text()})
            self.gainTest(self.freqUl, gainUlMin, gainUlMax)

    def gainTest(self, freq, gainMin, gainMax):
        self.testController.progressBarSignal.emit('Gain', 0, 0)
        self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
        self.gen.write(":FREQ:FIX " + str(freq) + " MHz")
        self.gen.write("POW:AMPL -45 dBm")
        time.sleep(1)
        ampl = getAvgGain(self.testController)
        genPow = float(self.gen.query("POW:AMPL?"))
        currentGain = round(abs(genPow) + ampl, 1)
        self.testController.logSignal.emit("Gain " + self.whatConn + " = " + str(currentGain) + " dBm", 0)
        if gainMin <= currentGain <= gainMax:
            self.testController.resSignal.emit('Gain', self.whatConn, str(gainMin), str(currentGain), str(gainMax), 1)
        else:
            q = self.mainParent.sendMsg('w', 'Warning',
                                        'Gain test fail. Gain ' + self.whatConn + ' = ' + str(currentGain) + ' dBm', 3)
            if q == QMessageBox.Retry:
                self.gainTest(freq, gainMin, gainMax)
                return
            elif q == QMessageBox.Ignore:
                self.testController.resSignal.emit('Gain', self.whatConn, str(gainMin), str(currentGain), str(gainMax),
                                                   0)
            elif q == QMessageBox.Cancel:
                self.testController.resSignal.emit('Gain', self.testController.whatConn, str(gainMin), str(currentGain),
                                                   str(gainMax), 0)
                self.testController.stopTestFlag = True
        if self.whatConn == 'Dl':
            self.testController.testLogDl.update({'Gain': currentGain})
        else:
            self.testController.testLogUl.update({'Gain': currentGain})
