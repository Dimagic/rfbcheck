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
        self.na = testController.instr.na
        self.freqDl = self.mainParent.listSettings[1]
        self.freqUl = self.mainParent.listSettings[2]
        self.whatConn = self.testController.whatConn
        self.atrSettings = self.mainParent.atrSettings
        self.listSettings = self.mainParent.listSettings
        self.ser = testController.ser
        self.gainDict = {}

        self.rfBands = {'band_dl_1': self.atrSettings.get('freq_band_dl_1'),
                        'band_ul_1': self.atrSettings.get('freq_band_ul_1'),
                        'band_dl_2': self.atrSettings.get('freq_band_dl_2'),
                        'band_ul_2': self.atrSettings.get('freq_band_ul_2')}

        testController.instr.sa.write("TRAC1:MODE MAXH")
        if testController.whatConn == "Dl":
            if self.mainParent.gainSA.isChecked():
                self.flatnessTest(self.listSettings[1], self.atrSettings.get('flat_dl_max'))
            else:
                self.flatnessTestNa(self.atrSettings.get('flat_dl_max'))
        elif testController.whatConn == "Ul":
            if self.mainParent.gainSA.isChecked():
                self.flatnessTest(self.listSettings[2], self.atrSettings.get('flat_ul_max'))
            else:
                self.flatnessTestNa(self.atrSettings.get('flat_ul_max'))
        testController.instr.sa.write("TRAC1:MODE WRIT")


    def flatnessTest(self, freq, flat):
        if self.rfBands.get('band_dl_2').find('@') == -1 and self.rfBands.get('band_ul_2').find('@') == -1:
            self.testController.logSignal.emit("RFB has one range of frequency", 0)

            if self.whatConn == 'Dl':
                start, stop = strToFreq(self.rfBands.get('band_dl_1'))
                self.getFlatness(start, stop)
            else:
                start, stop = strToFreq(self.rfBands.get('band_ul_1'))
                self.getFlatness(start, stop)
        else:
            self.testController.logSignal.emit("RFB has two ranges of frequency", 0)
            for k in self.rfBands.keys():
                if self.rfBands.get(k).find('@') == -1:
                    continue
                start, stop = strToFreq(self.rfBands.get(k))
                if self.testController.whatConn == 'Dl':
                    if k.find('_dl_') != -1 and self.rfBands.get(k).find('@') != -1:
                        self.getFlatness(start, stop)
                else:
                    if k.find('_ul_') != -1 and self.rfBands.get(k).find('@') != -1:
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
            q = self.testController.sendMsg('w', 'Warning', 'Flatness test fail: ' + str(currFlat) + ' dB', 3)
            if q == QMessageBox.Retry:
                self.testController.instr.sa.write("TRAC1:CLE:ALL")
                self.flatnessTest(freq, flat)
                return
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
            self.testController.resSignal.emit('Flatness', self.testController.whatConn, '0', str(currFlat), str(flat), 0)
        self.testController.fillTestLogSignal.emit('Flatness', str(currFlat))

    def fillTestLog(self, flat):
        minKey = min(self.gainDict.keys(), key=(lambda k: self.gainDict[k]))
        maxKey = max(self.gainDict.keys(), key=(lambda k: self.gainDict[k]))
        minGain = self.gainDict.get(minKey)
        maxGain = self.gainDict.get(maxKey)
        currFlat = round(maxGain - minGain, 2)
        self.testController.logSignal.emit("Flatness = " + str(currFlat) + " dBm", 0)
        if currFlat <= flat and (minGain > -50 and maxGain > -50):
            self.testController.resSignal.emit('Flatness', self.testController.whatConn, '0', str(currFlat), str(flat),
                                               1)
        else:
            q = self.testController.sendMsg('w', 'Warning', 'Flatness test fail: ' + str(currFlat) + ' dB', 3)
            if q == QMessageBox.Retry:
                self.testController.instr.sa.write("TRAC1:CLE:ALL")
                if self.mainParent.gainSA.isChecked():
                    self.flatnessTest(freq, flat)
                else:
                    self.flatnessTestNa(flat)
                return
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
            self.testController.resSignal.emit('Flatness', self.testController.whatConn, '0', str(currFlat), str(flat),
                                               0)

        self.testController.fillTestLogSignal.emit('Flatness 1', str(currFlat))


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

    def flatnessTestNa(self, flat):
        for i in self.rfBands:
            if self.testController.whatConn.upper() in i.upper():
                start, stop = strToFreq(self.rfBands.get(i))
                self.na.write(":SENS1:FREQ:STAR " + str(start) + "E6")
                self.na.write(":SENS1:FREQ:STOP " + str(stop) + "E6")
                self.na.write(":CALC1:PAR1:DEF S12")
                self.na.write(":SENS1:AVER ON")
                self.na.write(":CALC1:MARK1 ON")
                time.sleep(1)
                for j in np.arange(start, stop + 0.5, 0.5):
                    self.na.write(":CALC1:MARK1:X " + str(j) + 'E6')
                    curList = self.na.query(":CALC1:MARK1:Y?")
                    currentGain = round(toFloat(curList[:curList.find(',')]),2)
                    self.gainDict.update({j: currentGain})
        self.fillTestLog(flat)

                # self.na.write(":CALC1:MARK1 ON")
                # self.na.write(":CALC1:MARK2 ON")
                #
                # self.na.write(":CALC1:MARK1:FUNC:TYPE MAX")
                #
                # self.na.write(":CALC1:MARK2:FUNC:TYPE MIN")


                # self.na.write(":CALC1:MARK:MATH:FLAT ON")

                # self.na.write(":CALC1:MARK1 ON")
                # self.na.write(":CALC1:MARK1:FUNC:TYPE MIN")
                # self.na.write(":CALC1:MARK1:FUNC:PEXC .5")
                # self.na.write(":CALC1:MARK1:FUNC:EXEC")

                # self.na.write(":CALC2:MARK2 ON")
                # self.na.write(":CALC2:MARK2:FUNC:TYPE MIN")
                # self.na.write(":CALC2:MARK2:FUNC:PEXC .5")
                # self.na.write(":CALC2:MARK2:FUNC:EXEC")

                # self.na.write(":CALC1:MARK2:FUNC:TYPE PEAK")
                # self.na.write(":CALC1:MARK2:FUNC:PEXC .5")
                # self.na.write(":CALC1:MARK2:FUNC:PPOL POS")
                # self.na.write(":CALC1:MARK2:FUNC:EXEC")
                #
                # self.na.write(":CALC1:MARK:MATH:FLAT ON")
                # flat = list(self.na.query(":CALC1:MARK:MATH:FLAT:DATA?"))
                # print(flat)

                # self.na.write(":CALC1:PAR1:DEF S12")


                # self.na.write(":CALC1:MARK:MATH:FLAT ON")
                # flat = self.na.query(":CALC1:MARK:MATH:FLAT:DATA?")
                # print(flat)

                # self.na.write(":CALC1:MARK1 ON")
                # self.na.write(":SENS1:AVER ON")
                # time.sleep(2)
                # self.na.write(":CALC1:MARK1:FUNC:TYPE PEAK")
                # self.na.write(":CALC1:MARK1:FUNC:PEXC .5")
                # self.na.write(":CALC1:MARK1:FUNC:PPOL POS")
                # self.na.write(":CALC1:MARK1:FUNC:EXEC")
        #         time.sleep(.2)
        #         freqPeak = self.na.query(":CALC1:MARK1:X?")
        #         time.sleep(.2)
        #         valuePeak = self.na.query(":CALC1:MARK1:Y?")
        #         time.sleep(.2)
        #         peakPos.update({freqPeak: valuePeak})
        #
        #         self.na.write(":CALC1:MARK1:FUNC:PPOL NEG")
        #         self.na.write(":CALC1:MARK1:FUNC:EXEC")
        #         time.sleep(.2)
        #         freqPeak = self.na.query(":CALC1:MARK1:X?")
        #         time.sleep(.2)
        #         valuePeak = self.na.query(":CALC1:MARK1:Y?")
        #         time.sleep(.2)
        #         peakNeg.update({freqPeak: valuePeak})
        # print(peakPos)
        # print(peakNeg)


