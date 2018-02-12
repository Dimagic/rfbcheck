from Equip.equip import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class FlatnessTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(FlatnessTest, self).__init__(parent)
        testController.logSignal.emit("***** Start Flatness test *****", 3)

        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.freqDl = self.mainParent.listSettings[1]
        self.freqUl = self.mainParent.listSettings[2]
        self.whatConn = self.testController.whatConn
        self.atrSettings = self.mainParent.atrSettings
        self.listSettings = self.mainParent.listSettings
        self.ser = testController.ser
        self.gainDict = {}

        testController.instr.sa.write("TRAC1:MODE MAXH")
        if testController.whatConn == "Dl":
            self.flatnessTest(self.listSettings[1], self.atrSettings.get('flat_dl_max'))
        elif testController.whatConn == "Ul":
            self.flatnessTest(self.listSettings[2], self.atrSettings.get('flat_ul_max'))
        else:
            self.testController.msgSignal.emit("w", "Warning", "Flatness_test Dl/Ul", 1)
        testController.instr.sa.write("TRAC1:MODE WRIT")

    def flatnessTest(self, freq, flat):
        rfBands = {'band_dl_1': self.atrSettings.get('freq_band_dl_1'),
                   'band_ul_1': self.atrSettings.get('freq_band_ul_1'),
                   'band_dl_2': self.atrSettings.get('freq_band_dl_2'),
                   'band_ul_2': self.atrSettings.get('freq_band_ul_2')}
        if rfBands.get('band_dl_2').find('@') == -1 and rfBands.get('band_ul_2').find('@') == -1:
            self.testController.logSignal.emit("RFB has one range of frequency", 0)

            if self.whatConn == 'Dl':
                start, stop = strToFreq(rfBands.get('band_dl_1'))
                self.getFlatness(start, stop)
            else:
                start, stop = strToFreq(rfBands.get('band_ul_1'))
                self.getFlatness(start, stop)
        else:
            self.testController.logSignal.emit("RFB has two ranges of frequency", 0)
            for k in rfBands.keys():
                if rfBands.get(k).find('@') == -1:
                    continue
                start, stop = strToFreq(rfBands.get(k))
                if self.testController.whatConn == 'Dl':
                    if k.find('_dl_') != -1 and rfBands.get(k).find('@') != -1:
                        self.getFlatness(start, stop)
                else:
                    if k.find('_ul_') != -1 and rfBands.get(k).find('@') != -1:
                        self.getFlatness(start, stop)
        minGain = maxGain = None
        minFreq = maxFreq = None
        t = False
        for i in self.gainDict:
            if not t:
                minGain = maxGain = round(self.gainDict.get(i), 2)
                minFreq = maxFreq = i
                t = True
            if minGain > self.gainDict.get(i):
                minGain = round(self.gainDict.get(i), 2)
                minFreq = i
            if maxGain < self.gainDict.get(i):
                maxGain = round(self.gainDict.get(i), 2)
                maxFreq = i

        genPow = float(self.gen.query("POW:AMPL?"))
        self.testController.logSignal.emit("MIN = " + str(genPow - minGain) + " dBm on freq = " + str(minFreq) + " MHz",
                                           0)
        self.testController.logSignal.emit("MAX = " + str(genPow - maxGain) + " dBm on freq = " + str(maxFreq) + " MHz",
                                           0)
        currFlat = round(abs(minGain - maxGain), 1)
        self.testController.logSignal.emit("Flatness = " + str(currFlat) + " dBm", 0)
        if currFlat <= flat and (minGain > -50 and maxGain > -50):
            self.testController.resSignal.emit('Flatness', self.testController.whatConn, '0', str(currFlat), str(flat), 1)
        else:
            q = self.mainParent.sendMsg('w', 'Warning', 'Flatness test fail: ' + str(currFlat) + ' dB', 3)
            if q == QMessageBox.Retry:
                self.testController.instr.sa.write("TRAC1:CLE:ALL")
                self.flatnessTest(freq, flat)
                return
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
            self.testController.resSignal.emit('Flatness', self.testController.whatConn, '0', str(currFlat), str(flat), 0)
        self.testController.fillTestLogSignal.emit('Flatness', str(currFlat))

    def getFlatness(self, start, stop):
        self.testController.useCorrection = True
        self.sa.write("CALC:MARK:CPS 0")
        self.sa.write("CALC:MARK1:X " + str(start) + " MHz")
        self.sa.write("CALC:MARK1:STAT 1")
        self.sa.write(":SENSE:FREQ:center " + str(start + (stop - start) / 2) + " MHz")
        # refLvl = float(self.sa.query("DISP:WIND:TRAC:Y:RLEV:OFFS?"))
        band = int(stop - start)
        self.testController.logSignal.emit("Bandwidth = " + str(band) + " MHz", 0)
        self.testController.logSignal.emit(
            "RG-test start Freq: " + str(start) + " MHz; end Freq: " + str(stop) + " MHz", 0)
        self.sa.write(":SENSE:FREQ:span " + str(band + 5) + " MHz")
        self.gen.write(":FREQ:FIX " + str(start) + " MHz")
        time.sleep(1)
        rangeGain = np.arange(start, stop + 0.5, 0.5)
        for j, i in enumerate(rangeGain):
            if self.testController.stopTestFlag:
                return
            self.testController.progressBarSignal.emit('Flatness', len(rangeGain) - 1, j)
            self.gen.write(":FREQ:FIX " + str(i) + " MHz")
            time.sleep(.2)
            self.sa.write("CALC:MARK1:X " + str(i) + " MHz")
            saToGen = self.mainParent.calibrSaToGen.get(i)
            genToSa = self.mainParent.calibrGenToSa.get(i)
            # currentGain = getAvgGain(self.testController)
            currentGain = float(self.sa.query("CALC:MARK1:Y?")) - saToGen - genToSa
            self.gainDict.update({i: currentGain})

        self.sa.write("CALC:MARK1:STAT 0")
        self.sa.write("CALC:MARK:CPS 1")