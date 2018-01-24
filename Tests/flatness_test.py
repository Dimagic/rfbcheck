import numpy as np
from Equip.equip import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class FlatnessTest(QtCore.QThread):
    def __init__(self, testController, mainParent, parent=None):
        super(FlatnessTest, self).__init__(parent)
        if testController.stopTestFlag: QtCore.QThread.yieldCurrentThread()
        testController.logSignal.emit("***** Start Flatness test *****", 3)

        self.testController = testController
        self.mainParent = mainParent
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.freqDl = mainParent.listSettings[1]
        self.freqUl = mainParent.listSettings[2]
        self.whatConn = testController.whatConn

        self.ser = testController.ser

        if testController.whatConn == "Dl":
            testController.testLogDl.update({'SN': self.mainParent.rfbSN.text()})
            self.flatnessTest(self.mainParent, self.mainParent.instr.sa, self.mainParent.instr.gen,
                              self.mainParent.listSettings[1], self.mainParent.atrSettings.get('flat_dl_max'))
        elif testController.whatConn == "Ul":
            testController.testLogUl.update({'SN': self.mainParent.rfbSN.text()})
            self.flatnessTest(self.mainParent, self.mainParent.instr.sa, self.mainParent.instr.gen,
                              self.mainParent.listSettings[2], self.mainParent.atrSettings.get('flat_ul_max'))
        else:
            self.testController.msgSignal.emit("w", "Warning", "Flatness_test Dl/Ul", 1)

    def flatnessTest(self, parent, sa, gen, freq, flat):
        self.gainDict = {}
        rfBands = {'band_dl_1': parent.atrSettings.get('freq_band_dl_1'),
                   'band_ul_1': parent.atrSettings.get('freq_band_ul_1'),
                   'band_dl_2': parent.atrSettings.get('freq_band_dl_2'),
                   'band_ul_2': parent.atrSettings.get('freq_band_ul_2')}

        if rfBands.get('band_dl_2').find('@') == -1 and rfBands.get('band_ul_2').find('@') == -1:
            self.testController.logSignal.emit("RFB has one range of frequency", 0)
            if parent.whatConn == 'Dl':
                start, stop = strToFreq(parent, rfBands.get('band_dl_1'))
                self.getFlatness(parent, sa, gen, start, stop, freq)
            else:
                start, stop = strToFreq(parent, rfBands.get('band_ul_1'))
                self.getFlatness(parent, sa, gen, start, stop, freq)
        else:
            self.testController.logSignal.emit("RFB has two ranges of frequency", 0)
            for k in rfBands.keys():
                if rfBands.get(k).find('@') == -1:
                    continue
                start, stop = strToFreq(parent, rfBands.get(k))
                print(start, stop)
                if parent.whatConn == 'Dl':
                    if k.find('_dl_') != -1 and rfBands.get(k).find('@') != -1:
                        self.getFlatness(parent, sa, gen, start, stop, rfBands.get(k))
                else:
                    if k.find('_ul_') != -1 and rfBands.get(k).find('@') != -1:
                        self.getFlatness(parent, sa, gen, start, stop, rfBands.get(k))

        minGain = maxGain = None
        t = False
        print(self.gainDict)

        for i in self.gainDict:
            if t == False:
                minGain = maxGain = round(self.gainDict.get(i), 2)
                minFreq = maxFreq = i
                t = True
            if minGain > self.gainDict.get(i):
                minGain = round(self.gainDict.get(i), 2)
                minFreq = i
            if maxGain < self.gainDict.get(i):
                maxGain = round(self.gainDict.get(i), 2)
                maxFreq = i
        genPow = float(gen.query("POW:AMPL?"))
        self.testController.logSignal.emit("MIN = " + str(genPow - minGain) + " dBm on freq = " + str(minFreq) + " MHz",
                                           0)
        self.testController.logSignal.emit("MAX = " + str(genPow - maxGain) + " dBm on freq = " + str(maxFreq) + " MHz",
                                           0)
        currFlat = round(abs(minGain - maxGain), 1)
        self.testController.logSignal.emit("Flatness = " + str(currFlat) + " dBm", 0)
        if currFlat <= flat and (minGain > -50 and maxGain > -50):
            self.testController.resSignal.emit('Flatness', parent.whatConn, '0', str(currFlat), str(flat), 1)
        else:
            q = parent.sendMsg('w', 'Warning', 'Flantes test fail: ' + str(currFlat) + ' dB', 3)
            if q == QMessageBox.Retry:
                self.flatnessTest(parent, sa, gen, freq, flat)
                return
            elif q == QMessageBox.Cancel:
                parent.stopTestFlag = True
            self.testController.resSignal.emit('Flatness', parent.whatConn, '0', str(currFlat), str(flat), 0)
        if parent.whatConn == 'Dl':
            parent.testLogDl.update({'Flatness': currFlat})
        else:
            parent.testLogUl.update({'Flatness': currFlat})

    def getFlatness(self, parent, sa, gen, start, stop, freq):
        parent.useCorrection = True
        sa.write(":SENSE:FREQ:center " + str(start + (stop - start) / 2) + " MHz")
        refLvl = float(sa.query("DISP:WIND:TRAC:Y:RLEV:OFFS?"))
        band = int(stop - start)
        self.testController.logSignal.emit("Bandwidth = " + str(band) + " MHz", 0)
        self.testController.logSignal.emit(
            "RG-test start Freq: " + str(start) + " MHz; end Freq: " + str(stop) + " MHz", 0)
        sa.write(":SENSE:FREQ:span " + str(band + 5) + " MHz")
        gen.write(":FREQ:FIX " + str(start) + " MHz")
        time.sleep(1)
        currentGain = getAvgGain(parent)

        rangeGain = np.arange(start, stop + 0.5, 0.5)
        minGain = maxGain = round(currentGain, 2)
        minFreq = maxFreq = rangeGain[0]
        ##        parent.TestPrBar.reset()
        ##        parent.TestPrBar.setRange(start*10,stop*10-5)
        ##        parent.TestPrBar.setValue(0)

        for j, i in enumerate(rangeGain):
            if self.mainParent.stopTestFlag == True: return
            self.testController.progressBarSignal.emit('Flatness', len(rangeGain) - 1, j)
            gen.write(":FREQ:FIX " + str(i) + " MHz")
            currentGain = getAvgGain(parent)
            # self.testController.logSignal.emit("Freq: "+str(i)+" Gain: " +str(currentGain)[:5]+" dB",0)
            self.gainDict.update({i: currentGain})
