import time

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
from Equip.equip import strToFreq, toFloat


class ReturnLossTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(ReturnLossTest, self).__init__(parent)
        q = testController.sendMsg('i', 'RFBCheck', 'Please connect NA to RF input and press Ok.', 2)
        if q == QMessageBox.Cancel:
            return

        testController.logSignal.emit("***** Start return loss test *****", 3)
        self.testController = testController
        self.mainParent = testController.getParent()
        self.na = testController.instr.na
        self.atrSettings = self.mainParent.atrSettings
        self.rfBands = {'band_dl_1': self.atrSettings.get('freq_band_dl_1'),
                        'band_ul_1': self.atrSettings.get('freq_band_ul_1'),
                        'band_dl_2': self.atrSettings.get('freq_band_dl_2'),
                        'band_ul_2': self.atrSettings.get('freq_band_ul_2')}
        self.returnLossTest()

    def returnLossTest(self):
        currRloss = self.getReturnLoss()
        rlossmax = self.atrSettings.get('rloss_max')

        if currRloss > rlossmax:
            q = self.testController.sendMsg('i', 'RFBCheck', 'Return loss test fail: ' + str(currRloss), 3)
            if q == QMessageBox.Retry:
                self.returnLossTest()
            else:
                self.testController.resSignal.emit('RLoss', self.testController.whatConn,
                                                   '-', str(currRloss), str(rlossmax), 0)
        else:
            self.testController.resSignal.emit('RLoss', self.testController.whatConn,
                                               '-', str(currRloss), str(rlossmax), 1)
        self.testController.fillTestLogSignal.emit('RLoss', str(currRloss))
        self.testController.logSignal.emit("Return loss: " + str(currRloss) + " dB", 0)

    def getReturnLoss(self):
        rlossArr = []
        for i in self.rfBands:
            if self.rfBands.get(i) == '':
                continue
            if self.testController.whatConn.upper() in i.upper():
                start, stop = strToFreq(self.rfBands.get(i))
                self.na.write(":SENS1:FREQ:STAR " + str(start) + "E6")
                self.na.write(":SENS1:FREQ:STOP " + str(stop) + "E6")
                self.na.write(":CALC1:PAR1:DEF S22")
                self.na.write(":SENS1:AVER OFF")
                self.na.write(":CALC1:MARK1 ON")
                time.sleep(2)
                steep = 0.5
                tmpRange = np.arange(start, stop + steep, steep)
                for k, j in enumerate(tmpRange):
                    self.testController.progressBarSignal.emit('Return loss', len(tmpRange) - 1, k)
                    self.na.write(":CALC1:MARK1:X " + str(j) + 'E6')
                    curList = self.na.query(":CALC1:MARK1:Y?")
                    currentGain = round(toFloat(curList[:curList.find(',')]), 2)
                    rlossArr.append(currentGain)
        return max(rlossArr)



