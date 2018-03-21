from Equip.config import Config
from Equip.equip import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class GainTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(GainTest, self).__init__(parent)
        if testController.stopTestFlag:
            return
        testController.logSignal.emit("***** Start Gain test *****", 0)
        self.config = Config()
        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.na = testController.instr.na
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
        if self.mainParent.gainSA.isChecked():
            self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
            self.gen.write(":FREQ:FIX " + str(freq) + " MHz")
            self.gen.write("POW:AMPL " + self.config.getConfAttr('gen_gainFlatPow') + " dBm")
            time.sleep(1)
            self.testController.useCorrection = True
            ampl = getAvgGain(self.testController)
            genPow = float(self.gen.query("POW:AMPL?"))
            currentGain = round(abs(genPow) + ampl, 2)
        else:
            self.na.write(":SENS1:FREQ:CENT " + str(freq) + "E6")
            self.na.write(":SENS1:FREQ:SPAN 30E6")
            self.na.write(":CALC1:MARK1 ON")
            self.na.write(":SENS1:AVER ON")
            time.sleep(2)
            self.na.write(":CALC1:MARK1:X " + str(freq) + 'E6')
            currentGain = self.na.query(":CALC1:MARK1:Y?")
            currentGain = currentGain[:currentGain.find(',')]
            currentGain = round(float(currentGain) + float(self.mainParent.naAtten1.text()), 2)

        self.testController.logSignal.emit("Gain " + self.whatConn + " = " + str(currentGain) + " dBm", 0)
        if (currentGain > gainMax) and (currentGain - gainMax <= 5):
            self.testController.resSignal.emit('Gain', self.whatConn, str(gainMin), str(currentGain),
                                              str(gainMax), 2)
        elif gainMin <= currentGain <= gainMax:
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






