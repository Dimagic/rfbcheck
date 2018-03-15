from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMessageBox, QSizePolicy
from Equip.instrument import *
from Equip.equip import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from threading import Thread
import numpy as np
import math
import datetime
import sqlite3
import re


class Calibration(QtWidgets.QDialog):

    def __init__(self, parent):
        super(Calibration, self).__init__(parent)
        self.currParent = parent
        # self.dialog = loadUi('Forms/calibration.ui', self)
        # self.dialog.setWindowTitle('Calibration')
        # self.dialog.setWindowIcon(parent.appIcon)
        # m = PlotCanvas(self)
        # m.move(0, 0)
        # self.dialog.show()

        self.calibration(parent)

    def grafic(self, parent):
        try:
            conn, cursor = parent.getConnDb()
            query = "select * from calGenToSa"
            rows = cursor.execute(query).fetchall()
            freq = {}
            for row in rows:
                freq.update({row[1]: row[2]})
        except Exception as e:
            parent.sendMsg('c', 'DB error', e, 1)
            return
        startFreq = min(freq.keys())
        stopFreq = max(freq.keys())

        bars = ('A', 'B', 'C', 'D', 'E')
        y_pos = np.arange(len(bars))
        height = [3, 12, 5, 18, 45]
        plt.bar(y_pos, height)

        # If we have long labels, we cannot see it properly
        # names = ("very long group name 1", "very long group name 2", "very long group name 3", "very long group name 4",
        #          "very long group name 5")
        # plt.xticks(y_pos, names, rotation=90)

        # Thus we have to give more margin:
        # plt.subplots_adjust(bottom=0.4)

        # It's the same concept if you need more space for your titles
        # plt.title("This is\na very very\nloooooong\ntitle!")
        # plt.subplots_adjust(top=0.7)
        plt.show()

    def calibration(self, parent):
        parent.currTestLbl.setText('Calibration')
        parent.useCorrection = False
        bandList = []
        try:
            if parent.calibrStart.text().isdigit() and parent.calibrStop.text().isdigit():
                start = int(parent.calibrStart.text())
                stop = int(parent.calibrStop.text())
                if start >= stop:
                    parent.sendMsg('w', 'Warning', 'Incorrect frequncy data entered', 1)
                    parent.calibrStart.setText('')
                    parent.calibrStop.setText('')
                    return
                while start < stop:
                    if stop - start < 100:
                        bandList.append([start, stop])
                        break
                    else:
                        start += 100
                        bandList.append([start - 100, start])
            else:
                conn, cursor = parent.getConnDb()
                if parent.calAllBands.isChecked():
                    tmp = cursor.execute(
                        "select freq_band_dl_1, freq_band_dl_2, freq_band_ul_1, freq_band_ul_2 from atr")
                else:
                    tmp = cursor.execute("select freq_band_dl_1, freq_band_dl_2, freq_band_ul_1, freq_band_ul_2 "
                                         "from atr where rfb_type = :s", {'s': parent.rfbTypeCombo.currentText()})
                for i in tmp:
                    for j in i:
                        if j != None and j != '' and j.find('@') != -1:
                            reg = re.findall('[0-9]+', j)
                            start = int(reg[0])
                            stop = int(reg[1])
                            bandList.append([start, stop])
                conn.close()
        except Exception as e:
            parent.sendMsg('c', 'Get ATR settings fail', str(e), 1)
            return

        print(bandList)

        if parent.sendMsg('i', 'Message', 'Connect SA to Gen using cabble whith attenuator', 2) == QMessageBox.Cancel:
            return
        table = 'calSaToGen'
        for i in bandList:
            self.makeCalibr(parent, table, int(parent.saAtten.text()), i)

        if parent.sendMsg('i', 'Message', 'Connect Gen to SA using cabble whithout attenuator',
                          2) == QMessageBox.Cancel:
            return
        table = 'calGenToSa'
        for i in bandList:
            self.makeCalibr(parent, table, 0, i)

        parent.sendMsg('i', 'Message', 'Calibration complete', 1)
        parent.useCorrection = True


    def makeCalibr(self, parent, table, attenuator, freqArr):
        startFreqFull = freqArr[0]
        stopFreqFull = freqArr[1]
        currBand = stopFreqFull - startFreqFull
        centerFreq = startFreqFull
        arrFreq = np.arange(startFreqFull, stopFreqFull + 0.5, 0.5)
        dict = []
        query = "INSERT OR REPLACE into " + table + " values (?, ?, ?, ?)"
        self.t = Thread(target=self.runCalibration,
                        args=(parent, currBand, startFreqFull, stopFreqFull, centerFreq, attenuator, arrFreq, query,))
        self.t.start()
        while self.t.isAlive():
            time.sleep(2)

    def runCalibration(self, parent, currBand, startFreqFull, stopFreqFull, centerFreq, attenuator, arrFreq, query):
        parent.instr = Instrument(centerFreq, parent)
        parent.instr.sa.write("DISP:WIND:TRAC:Y:RLEV:OFFS " + str(attenuator) + "")
        parent.instr.gen.write("POW:AMPL -30 dBm")
        parent.instr.sa.write(":SENSE:FREQ:center " + str(centerFreq + currBand / 2) + " MHz")
        parent.instr.sa.write(":SENSE:FREQ:span " + str(currBand + 5) + " MHz")
        parent.instr.sa.write("BAND:VID 3 KHZ")
        parent.instr.gen.write(":OUTP:STAT ON")
        time.sleep(2)
        try:
            conn, cursor = parent.getConnDb()
        except Exception as e:
            parent.sendMsg('c', 'DB error', e, 1)
            return
        parent.TestPrBar.setRange(int(startFreqFull) * 10, int(stopFreqFull) * 10 - 2)
        first = True
        for i in arrFreq:
            parent.instr.gen.write(":FREQ:FIX " + str(i) + " MHz")
            if first:
                time.sleep(2)
                first = False
            else:
                pass
            parent.TestPrBar.setValue(int(i * 10))
            ampl = getAvgGain(parent)
            delta = round(float(ampl + abs(float(parent.instr.gen.query("POW:AMPL?")))), 2)

            j = int(i * 10)
            dict = [j, int(j) / 10, delta, datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")]
            try:
                cursor.execute(query, dict)
                result = cursor.fetchall()
            except sqlite3.DatabaseError as err:
                parent.sendMsg('c', 'Querry error', str(err), 1)
                conn.close()
                break
            else:
                conn.commit()

        conn.close()
        parent.instr.gen.write(":OUTP:STAT OFF")

    @staticmethod
    def strToFreq(parent, curRange):
        try:
            ind = curRange.find('@')
            start = toFloat(curRange[0:ind])
            stop = toFloat(curRange[ind + 1:])
            return start, stop
        except Exception:
            parent.sendMsg('w', 'Error', 'Convert string: ' + curRange + ' to float fail')
            return 0, 0


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        data = [i%2 for i in range(100)]
        ax = self.figure.add_subplot(111)
        ax.bar(data, data)
        # ax.set_title('PyQt Matplotlib Example')
        self.draw()