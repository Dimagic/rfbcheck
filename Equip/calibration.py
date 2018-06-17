import sqlite3
import time
import datetime
from PyQt5 import QtCore
import numpy as np
import re
from PyQt5.QtWidgets import QMessageBox
from Equip.instrument import Instrument


class Calibration(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(str, int)
    msgSignal = QtCore.pyqtSignal(str, str, str, int)
    progressBarSignal = QtCore.pyqtSignal(str, float, float)

    def __init__(self, parent):
        super(Calibration, self).__init__(parent)
        self.currParent = parent
        # -------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------
        self.progress = 0
        self.freqForProgr = 0
        self.currParent.useCorrection = False
        self.instr = None
        self.steepFreq = .5
        self.table = None
        self.queryToDb = []
        self.arrQuery = ('Connect SA to Gen using cable with attenuator',
                         'Connect Gen to SA using cable without attenuator')

    def run(self):
        arrFreq = self.getFreq()
        self.freqForProgr = len(arrFreq) * 2
        self.instr = Instrument(arrFreq[0], self.currParent)
        for m, q in enumerate(self.arrQuery):
            if self.sendMsg('i', 'Message', q, 2) == QMessageBox.Cancel:
                self.instr.writeGen(":OUTP:STAT OFF")
                return
            if m == 0:
                self.saAtten = self.currParent.saAtten.text()
                self.table = 'calSaToGen'
            if m == 1:
                self.saAtten = 0
                self.table = 'calGenToSa'
            i = 1
            n = 0
            try:
                while i < len(arrFreq):
                    if arrFreq[i] - arrFreq[i - 1] != self.steepFreq:
                        self.runCalibration(arrFreq[n:i])
                        n = i
                    i += 1
                self.runCalibration(arrFreq[n:i])
                self.writeToDb()
            except Exception as e:
                self.instr.writeGen(":OUTP:STAT OFF")
                self.sendMsg('c', 'RFBCheck: Calibration error', str(e), 1)
                return
        self.sendMsg('i', 'RFBCheck', 'Calibration complite', 1)

    def runCalibration(self, arrFreq):
        startFreq = arrFreq[0]
        stopFreq = arrFreq[len(arrFreq) - 1]
        currBand = stopFreq - startFreq
        centerFreq = startFreq + currBand/2
        self.setInstruments(centerFreq, currBand)
        self.instr.writeSa("CALC:MARK:CPS 1")
        time.sleep(1)

        if len(arrFreq) > 100:
            bands = 0
        else:
            bands = None
        for freq in arrFreq:
            self.progress += 1
            self.progressBarSignal.emit('Calibration', self.freqForProgr - 1, self.progress)
            if bands is not None:
                if bands >= 100:
                    self.setInstruments(freq + 25, 50)
                    bands = 0
                    time.sleep(.1)
                else:
                    bands += 1
            gain = self.instr.saGetGainViaGen(freq)

            delta = round(float(gain + abs(self.instr.getPow())), 2)
            self.queryToDb.append([freq * 10, freq, delta, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")])
            n = "Freq: %s MHz Gain: %s dB Delta: %s dB" % (str(freq), str(gain), str(delta))
            self.logSignal.emit(n, 1)

    def setInstruments(self, centerFreq, currBand):
        self.instr.sa.write("DISP:WIND:TRAC:Y:RLEV:OFFS " + str(self.saAtten) + "")
        self.instr.gen.write("POW:AMPL -5 dBm")
        self.instr.sa.write(":SENSE:FREQ:center " + str(centerFreq) + " MHz")
        self.instr.sa.write(":SENSE:FREQ:span " + str(currBand + 5) + " MHz")
        self.instr.sa.write("BAND:VID 3 KHZ")
        self.instr.gen.write(":OUTP:STAT ON")
        time.sleep(2)

    def getFreq(self):
        conn, cursor = self.currParent.getConnDb()
        if self.currParent.calAllBands.isChecked():
            tmp = cursor.execute(
                "select freq_band_dl_1, freq_band_dl_2, freq_band_ul_1, freq_band_ul_2 from atr")
        else:
            tmp = cursor.execute("select freq_band_dl_1, freq_band_dl_2, freq_band_ul_1, freq_band_ul_2 "
                                 "from atr where rfb_type = :s", {'s': self.currParent.rfbTypeCombo.currentText()})
        arrFreq = []
        for i in tmp:
            for j in i:
                if j != '':
                    startStop = re.findall(r"\d+", j)
                    arrTmp = np.arange(float(startStop[0]), float(startStop[1]) + self.steepFreq, self.steepFreq)
                    arrFreq.append(arrTmp)
        setFreq = set()
        for i in arrFreq:
            setFreq = setFreq | set(i)
        return sorted(list(setFreq))

    def sendMsg(self, icon, msgTitle, msgText, typeQestions):
        self.msgSignal.emit(icon, msgTitle, msgText, typeQestions)
        while self.currParent.answer is None:
            time.sleep(.05)
        else:
            forReturn = self.currParent.answer
            self.currParent.answer = None
            return forReturn

    def writeToDb(self):
        try:
            conn, cursor = self.currParent.getConnDb()
            query = "INSERT OR REPLACE into " + self.table + " values (?, ?, ?, ?)"
            for i in self.queryToDb:
                cursor.execute(query, i).fetchall()
        except sqlite3.DatabaseError as err:
            self.sendMsg('c', 'Querry error', str(err), 1)
            conn.close()
        else:
            conn.commit()
            conn.close()
            self.queryToDb.clear()
            self.logSignal.emit("Writing to DB complete", 0)

    def getParent(self):
        return self.currParent
