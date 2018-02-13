from Equip.equip import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class GainTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(GainTest, self).__init__(parent)
        if testController.stopTestFlag:
            return
        testController.logSignal.emit("***** Start Gain test *****", 3)
        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.freqDl = self.mainParent.listSettings[1]
        self.freqUl = self.mainParent.listSettings[2]
        self.whatConn = testController.whatConn
        self.ser = self.testController.ser
        gainDlMin = self.mainParent.atrSettings.get('gain_dl_min')
        gainDlMax = self.mainParent.atrSettings.get('gain_dl_max')
        gainUlMin = self.mainParent.atrSettings.get('gain_ul_min')
        gainUlMax = self.mainParent.atrSettings.get('gain_ul_max')
        if self.testController.whatConn == "Dl":
            self.gainTest(self.freqDl, gainDlMin, gainDlMax)
        elif self.testController.whatConn == "Ul":
            self.gainTest(self.freqUl, gainUlMin, gainUlMax)

    def gainTest(self, freq, gainMin, gainMax):
        self.testController.progressBarSignal.emit('Gain', 0, 0)
        self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
        self.gen.write(":FREQ:FIX " + str(freq) + " MHz")
        self.gen.write("POW:AMPL -45 dBm")
        time.sleep(1)
        self.testController.useCorrection = True
        ampl = getAvgGain(self.testController)
        genPow = float(self.gen.query("POW:AMPL?"))
        currentGain = round(abs(genPow) + ampl, 1)
        self.testController.logSignal.emit("Gain " + self.whatConn + " = " + str(currentGain) + " dBm", 0)
        if gainMin <= currentGain <= gainMax:
            self.testController.resSignal.emit('Gain', self.whatConn, str(gainMin), str(currentGain), str(gainMax), 1)
        else:
            q = self.testController.sendMsg('w', 'Warning', 'Gain test fail. Gain ' + self.whatConn + ' = ' +
                                            str(currentGain) + ' dBm', 3)
            if q == QMessageBox.Retry:
                self.gainTest(freq, gainMin, gainMax)
            elif q == QMessageBox.Ignore:
                self.testController.resSignal.emit('Gain', self.whatConn, str(gainMin), str(currentGain),
                                                   str(gainMax), 0)
                self.testController.fillTestLogSignal.emit('Gain', str(currentGain))
                return
            elif q == QMessageBox.Cancel:
                self.testController.resSignal.emit('Gain', self.whatConn, str(gainMin), str(currentGain),
                                                   str(gainMax), 0)
                self.testController.stopTestFlag = True
        self.testController.fillTestLogSignal.emit('Gain', str(currentGain))
        return






