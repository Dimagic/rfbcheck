from Equip.equip import *
import Equip.commands as cmd
import time
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class AlcTest(QtCore.QThread):
    def __init__(self, testController, mainParent, parent=None):
        super(AlcTest, self).__init__(parent)

        if testController.stopTestFlag:
            return

        self.testController = testController
        self.mainParent = testController.getParent()
        self.ser = testController.ser
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.atrSettings = mainParent.atrSettings
        self.listSettings = testController.listSettings

        self.whatConn = testController.whatConn
        self.parent = mainParent
        self.sa.write(":SENSE:FREQ:span 3 MHz")

        self.alcInMin = self.atrSettings.get('alc_in_min')
        self.alcInMax = self.atrSettings.get('alc_in_max')
        self.alcOutMin = self.atrSettings.get('alc_out_min')
        self.alcOutMax = self.atrSettings.get('alc_out_max')

        if self.testController.whatConn == "Dl":
            self.inPow = self.listSettings[12]
            self.outPow = self.listSettings[14]
        else:
            self.inPow = self.listSettings[13]
            self.outPow = self.listSettings[15]
        if self.inPow != 0:
            self.gen.write("POW:AMPL " + str(self.inPow) + " dBm")
            # self.gen.write(":OUTP:STAT ON")
            time.sleep(1)
        else:
            setAmplTo(self.ser, cmd, self.gen, self.inPow, self.testController)
            # (conn, cmd, gen, ampl, parent)

        self.testController.useCorrection = False
        if self.whatConn == 'Dl':
            # self.sa.write(":SENSE:FREQ:center "+str(parent.listSettings[1])+" MHz")
            self.alcInTest(self.ser, cmd.setAlcInDl, self.whatConn, cmd.shiftDlIn)
            self.alcOutTest(self.ser, cmd.setAlcOutDl, self.whatConn, cmd.shiftDlOut)
        elif self.whatConn == 'Ul':
            # self.sa.write(":SENSE:FREQ:center "+str(parent.listSettings[2])+" MHz")
            self.alcInTest(self.ser, cmd.setAlcInUl, self.whatConn, cmd.shiftUlIn)
            self.alcOutTest(self.ser, cmd.setAlcOutUl, self.whatConn, cmd.shiftUlOut)
        else:
            print('ALC ERROR')
        self.testController.useCorrection = True
        # self.gen.write(":OUTP:STAT OFF")

    def alcInTest(self, conn, alc, whatConn, shift):
        self.testController.logSignal.emit("***** Start ALC in test *****", 0)
        setAlc(conn, alc, 255, shift)
        ampl = getAvgGain(self.testController)
        table = {}

        for j, i in enumerate(range(70, 161, 1)):
            setAlc(conn, alc, i, shift)
            time.sleep(0.3)
            ampl = getAvgGain(self.testController)
            self.testController.progressBarSignal.emit('ALC IN = ' + str(i) + '; meas = ' + str(ampl)[:5] + ' dBm',
                                                       161 - 70 - 1, j)
            if ampl > -10 and len(table) != 0:
                break
            if ampl > -10 and len(table) == 0:
                n = -1
                while n <= 10:
                    setAlc(conn, alc, i - n, shift)
                    time.sleep(1)
                    ampl = getAvgGain(self.testController)
                    self.testController.logSignal.emit('ALC IN = ' + str(i - n) +
                                                       '; meas = ' + str(ampl)[:7] + ' dBm', -1)
                    if -20.0 <= ampl <= -10.0:
                        table[i + 1] = ampl
                    n += 1
                break
            self.testController.logSignal.emit('ALC IN = ' + str(i) + '; meas = ' + str(ampl)[:7] + ' dBm', 0)
            if -20.0 <= ampl <= -10.0:
                table[i] = ampl
        self.parent.TestPrBar.setValue(161)

        if len(table) == 0:
            q = self.testController.sendMsg('w', 'Warning', 'ALC In test fail', 3)
            if q == QMessageBox.Retry:
                self.alcInTest(conn, alc, whatConn, shift)
            elif q == QMessageBox.Cancel:
                setAlc(conn, alc, 255, shift)
                self.testController.stopTestFlag = True
            elif q == QMessageBox.Ignore:
                setAlc(conn, alc, 255, shift)
            self.testController.logSignal.emit('ALC ' + whatConn + ' IN: FAIL', -1)
            self.testController.resSignal.emit('ALC test', self.testController.whatConn, str(self.alcInMin), 'fail',
                                               str(self.alcInMax), 0)
            self.testController.fillTestLogSignal.emit(self.parent, 'ALC in', 'Fail')
            return
        else:
            for n in range(1, 255, 1):
                if table.get(n) is not None:
                    minVal = table[n]
                    minKey = n
                    break
            for i in (10, 15, 20):
                for k in table:
                    if abs(i - abs(table[k])) < abs(i - abs(minVal)):
                        minVal = round(table[k], 1)
                        minKey = k

                self.testController.logSignal.emit(
                    'ALC ' + whatConn + ' IN (-' + str(i) + '): ' + str(minKey) + ' <-- ' + str(minVal)[:6] + ' dBm', 0)
                if i == 15:
                    if 100 <= minKey <= 130:
                        self.testController.resSignal.emit('ALC IN', self.testController.whatConn, str(self.alcInMin),
                                                           str(round(minVal, 1)) + ' ( in = ' + str(minKey) + ' )',
                                                           str(self.alcInMax), 1)
                    elif 85 <= minKey <= 145:
                        self.testController.resSignal.emit('ALC IN', self.testController.whatConn, str(self.alcInMin),
                                                           str(round(minVal, 1)) + ' ( in = ' + str(minKey) + ' )',
                                                           str(self.alcInMax), 2)
                    else:
                        self.testController.resSignal.emit('ALC IN', self.testController.whatConn, str(self.alcInMin),
                                                           str(round(minVal, 1)) + ' ( in = ' + str(minKey) + ' )',
                                                           str(self.alcInMax), 0)
                    self.testController.fillTestLogSignal.emit('ALC in', str(minKey))

        setAlc(conn, alc, 255, shift)

    def alcOutTest(self, conn, alc, whatConn, shift):
        if self.outPow != 0:
            self.gen.write("POW:AMPL " + str(self.inPow) + " dBm")
            time.sleep(1)
        else:
            setAmplTo(self.ser, cmd, self.gen, self.inPow, self.testController)

        setAlc(conn, alc, 4, shift)  # when 0 -> setAlc not work
        self.testController.logSignal.emit("***** Start ALC out test *****", 0)
        time.sleep(1)
        ampl = round(getAvgGain(self.testController), 1)
        setAlc(conn, alc, 255, shift)
        if ampl <= self.alcOutMin:
            self.testController.logSignal.emit('ALC ' + whatConn + ' OUT: PASS ' + str(ampl) + ' dBm', 1)
            self.testController.resSignal.emit('ALC OUT', self.testController.whatConn, str(self.alcOutMin), str(ampl),
                                               str(self.alcOutMax), 1)
            self.testController.fillTestLogSignal.emit('ALC out', str(ampl))
        else:
            self.testController.logSignal.emit('ALC ' + whatConn + ' OUT: FAIL ' + str(ampl) + ' dBm', -1)
            q = self.testController.sendMsg('w', 'Warning', 'ALC Out test. Gain: ' + str(ampl) + ' dBm', 3)
            if q == QMessageBox.Retry:
                self.alcOutTest(conn, alc, whatConn, shift)
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
                setAlc(conn, alc, 255, shift)
            elif q == QMessageBox.Ignore:
                setAlc(conn, alc, 255, shift)
            self.testController.resSignal.emit('ALC OUT', self.testController.whatConn, str(self.alcOutMin),
                                                             str(ampl), str(self.alcOutMax), 0)
            self.testController.fillTestLogSignal.emit('ALC out', str(ampl))
            return

    def fillTestLog(self, alcType, status):
        if self.testController.whatConn == 'Dl':
            self.testController.testLogDl.update({alcType: status})
        elif self.testController.whatConn == 'Ul':
            self.testController.testLogUl.update({alcType: status})
