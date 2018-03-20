from Equip.equip import *
import Equip.commands as cmd
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class IModTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(IModTest, self).__init__(parent)
        testController.logSignal.emit("***** Start IMod test *****", 0)
        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.listSettings = self.mainParent.listSettings
        self.instrument = testController.instr
        if testController.whatConn == 'Dl':
            genPow = self.listSettings[3]
            freq = self.listSettings[1]
        elif testController.whatConn == 'Ul':
            genPow = self.listSettings[4]
            freq = self.listSettings[2]
        else:
            self.testController.sendMsg('c', 'IMod test error', 'testController.whatConn = ' +
                                               testController.whatConn, 1)
            return
        try:
            self.mToneTest(freq, genPow)
        except Exception as e:
            q = self.testController.sendMsg('w', 'mToneTest error', str(e), 1)
            if q == QMessageBox.Ok:
                testController.stopTestFlag = True
                return

    def mToneTest(self, freq, genPow):
        freqForSignal = freq
        self.gen.write(":OUTP:MOD:STAT OFF")
        if self.testController.stopTestFlag:
            return
        setAmplTo(self.testController.ser, cmd, self.gen, genPow, self.testController)
        self.testController.progressBarSignal.emit('Intermodulation', 0, 0)
        haveFail = False
        self.sa.write(":SENSE:FREQ:span 4 MHz")
        self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
        self.sa.write("BAND:VID 1 KHZ")
        self.sa.write(":CALC:MARK1:STAT 0")
        self.sa.write("CALC:MARK:CPS 1")
        self.gen.write(":FREQ:FIX " + str(freq) + " MHz")
        self.gen.write(":OUTP:MOD:STAT OFF")
        # self.gen.write(":OUTP:STAT ON")
        time.sleep(1)
        # TODO: use corr parent or test controller?
        self.testController.useCorrection = False
        n1 = getAvgGain(self.testController)

        self.gen.write(":OUTP:MOD:STAT ON")
        time.sleep(2)
        n2 = getAvgGain(self.testController)
        self.testController.useCorrection = True
        freq, ampl = self.instrument.getPeakTable()
        delta = abs(abs(ampl[0]) - abs(ampl[len(ampl) - 1]))
        for i, j in enumerate(freq):
            self.testController.logSignal.emit('Peak: ' + str(j/1000000) + " MHz -> " + str(ampl[i]) + " dB", 0)
        if len(freq) > 3:
            self.testController.logSignal.emit('Peaks FAIL: to many peaks', -1)
            haveFail = True
        else:
            self.testController.logSignal.emit('Peaks Pass', 1)
        if delta > 1.5:
            self.testController.logSignal.emit('Delta between peaks FAIL: ' + str(round(delta, 3)) + " dBm", -1)
            self.testController.logSignal.emit(str(freq[0] / 1000) + " MHz " + str(ampl[0]) + " dBm", -1)
            self.testController.logSignal.emit(
                str(freq[len(freq) - 1] / 1000) + " MHz " + str(round(ampl[len(ampl) - 1], 3)) + " dBm", -1)
            haveFail = True
        time.sleep(1)
        d = n1 - n2
        if abs(abs(d) - 3) > 1:
            self.testController.logSignal.emit('Falling per tone(dBc) FAIL: ' + str(round(d, 3)), -1)
            haveFail = True
        else:
            self.testController.logSignal.emit('Delta between peaks PASS: ' + str(round(delta, 3)) + " dBm", 1)
            self.testController.logSignal.emit('Falling per tone(dBc) PASS: ' + str(round(d, 3)), 1)
        if not haveFail:
            self.testController.resSignal.emit('Intermodulation', self.testController.whatConn, '', 'Pass', '', 1)
            self.testController.fillTestLogSignal.emit('IMod', 'Pass')
        else:
            self.getSignalData(freqForSignal)
            q = self.testController.sendMsg('w', 'Warning', 'IMod test fail', 3)
            if q == QMessageBox.Retry:
                self.mToneTest(freq, genPow)
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
            self.testController.resSignal.emit('Intermodulation', self.testController.whatConn, '', 'Fail', '', 0)
            self.testController.fillTestLogSignal.emit('IMod', 'Fail')
        self.gen.write(":OUTP:MOD:STAT OFF")
        self.sa.write(":CALC:MARK1:STAT 1")
        self.sa.write("CALC:MARK:CPS 0")

    def getSignalData(self, freq):
        accur = .02
        signalDict = {}
        self.sa.write("TRAC1:MODE MAXH")
        self.sa.write("CALC:MARK:CPS 0")
        time.sleep(3)
        arrFreq = np.arange(freq - 2, freq + 2 + accur, accur)
        for i in arrFreq:
            # self.testController.progressBarSignal.emit('Intermodulation', 0, 0)
            self.sa.write(":CALC1:MARK1:X " + str(i) + 'E6')
            time.sleep(.05)
            gain = self.sa.query(":CALC1:MARK1:Y?")
            signalDict.update({round(i, 2): toFloat(gain)})
        self.sa.write("TRAC1:MODE WRIT")
        self.testController.fillTestLogSignal.emit('Imod_signal', str(signalDict))