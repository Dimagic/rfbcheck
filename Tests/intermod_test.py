from Equip.equip import *
import Equip.commands as cmd
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class IModTest(QtCore.QThread):
    def __init__(self, testController, mainParent, freq, parent=None):
        super(IModTest, self).__init__(parent)
        testController.logSignal.emit("***** Start IMod test *****", 3)

        self.testController = testController
        self.mainParent = mainParent
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.listSettings = mainParent.listSettings
        self.instrument = testController.instr

        # self.listLog = mainParent.listLog
        # self.sa = mainParent.instr.sa
        # self.gen = mainParent.instr.gen
        # self.parent = mainParent
        # self.testController = testController

        # setAmplTo(self,parent.ser, cmd, self.instrument, self.sa, self.gen, 0,parent)
        if testController.whatConn == 'Dl':
            pow = self.listSettings[3]
        elif testController.whatConn == 'Ul':
            pow = self.listSettings[4]
        else:
            pass

        try:
            self.mToneTest(freq, pow)
        except Exception as e:
            testController.msgSignal.emit('w', 'mToneTest error', str(e), 1)
            return

    def mToneTest(self, freq, pow):
        setAmplTo(self.testController.ser, cmd, self.gen, pow, self.testController)
        # (conn, cmd, gen, ampl, parent)
        self.testController.progressBarSignal.emit('Intermodulation', 0, 0)

        haveFail = False
        self.sa.write(":SENSE:FREQ:span 3 MHz")
        self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
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
        print(n1, n2)
        self.testController.useCorrection = True

        freq, ampl = self.instrument.getPeakTable()
        delta = abs(abs(ampl[0]) - abs(ampl[len(ampl) - 1]))

        print(ampl)

        if len(freq) > 3:
            self.parent.sendMsg('Intermodulation FAIL: to many peaks', 2)
            haveFail = True
        if delta > 0.7:
            self.testController.logSignal.emit('Delta between peaks FAIL: ' + str(round(delta, 3)) + " dBm", 3)
            self.testController.logSignal.emit(str(freq[0] / 1000) + " MHz " + str(ampl[0]) + " dBm", 3)
            self.testController.logSignal.emit(
                str(freq[len(freq) - 1] / 1000) + " MHz " + str(round(ampl[len(ampl) - 1], 3)) + " dBm", 3)
            haveFail = True
        self.gen.write(":OUTP:MOD:STAT OFF")
        time.sleep(1)
        d = n1 - n2

        if abs(abs(d) - 3) > 0.6:
            self.testController.logSignal.emit('Falling per tone(dBc) FAIL: ' + str(round(d, 3)), 2)
            haveFail = True
        else:
            self.testController.logSignal.emit('Delta between peaks PASS: ' + str(round(delta, 3)) + " dBm", 1)
            self.testController.logSignal.emit('Falling per tone(dBc) PASS: ' + str(round(d, 3)), 1)

        if haveFail is False:
            self.testController.resSignal.emit('Intermodulation', self.testController.whatConn, '', 'Pass', '', 1)
            if self.testController.whatConn == 'Dl':
                self.testController.testLogDl.update({'IMod': 'Pass'})
            else:
                self.testController.testLogUl.update({'IMod': 'Pass'})
        else:
            q = self.testController.sendMsg('w', 'Warning', 'IMod test fail', 3)
            if q == QMessageBox.Retry:
                self.mToneTest(self.gen, self.sa, freq, pow)
                return
            elif q == QMessageBox.Cancel:
                self.parent.stopTestFlag = True
            self.testController.resSignal.emit('Intermodulation', self.testController.whatConn, '', 'Fail', '', 0)
            if self.testController.whatConn == 'Dl':
                self.testController.testLogDl.update({'IMod': 'Fail'})
            else:
                self.testController.testLogUl.update({'IMod': 'Fail'})

        self.sa.write(":CALC:MARK1:STAT 1")
        self.sa.write("CALC:MARK:CPS 0")
##        gen.write(":OUTP:STAT OFF")
##        self.parent.TestPrBar.setValue(1)

##def getAmpl(sa):
##    return float(sa.query("CALC:MARK:Y?"))
