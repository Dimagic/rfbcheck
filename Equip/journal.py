from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import QtCore, QtGui, QtWidgets
from Equip.equip import toFloat
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import ast


class Journal:
    parent = None

    def __init__(self, parent):
        Journal.parent = parent
        self.parent = parent
        # self.current_hover = [0, 0]
        parent.tableJournal.cellDoubleClicked.connect(self.tableDoubleClick)
        parent.tableJournal.cellEntered.connect(self.cellHover)
        self.signalId = None
        self.flatness = None
        self.limitsDict = {}
        self.feelJournal()

    def cellHover(self, row, column):
        item = Journal.parent.tableJournal.item(row, column)
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        qrow = "select id from test_results where sn = '%s' and dateTest = '%s' and band_type = '%s'" % \
               (Journal.parent.tableJournal.item(row, 1).text(),
                Journal.parent.tableJournal.item(row, 2).text(),
                Journal.parent.tableJournal.item(row, 3).text())

        if column == 4:
            minGain = self.limitsDict.get(Journal.parent.tableJournal.item(row, 0).text() +
                                          Journal.parent.tableJournal.item(row, 3).text() + '_gainMin')
            maxGain = self.limitsDict.get(Journal.parent.tableJournal.item(row, 0).text() +
                                          Journal.parent.tableJournal.item(row, 3).text() + '_gainMax')
            # print(minGain, maxGain)
            Journal.parent.tableJournal.setToolTip('min: ' + str(minGain) + ' max: ' + str(maxGain))
            return
        else:
            Journal.parent.tableJournal.setToolTip('')

        if column == 5:
            q = "select id from flat_result where rfb  = (%s)" % qrow
        elif column == 9:
            q = "select id from imod_result where rfb  = (%s)" % qrow
        elif column == 6:
            q = "select dsa1 from dsa_results where rfb = (%s)" % qrow
        elif column == 7:
            q = "select dsa2 from dsa_results where rfb = (%s)" % qrow
        elif column == 8:
            q = "select dsa3 from dsa_results where rfb = (%s)" % qrow
        else:
            q = ''

        if q != '':
            try:
                conn, cursor = Journal.parent.getConnDb()
                rows = cursor.execute(q).fetchone()
                conn.close()
            except Exception as e:
                print(q, str(e))
                return
            if rows is not None:
                if column in [5, 9]:
                    Journal.parent.tableJournal.setToolTip("Double click for view signal")
                    self.signalId = rows[0]
                    return
                else:
                    self.signalId = None
                currDict = ast.literal_eval(rows[0])
                toToolTip = ""
                for k in sorted(currDict.keys()):
                    tab = ""
                    for i in range(1, 5 - len(str(k))):
                        tab += " "
                    if k == sorted(currDict.keys())[len(currDict.keys()) - 1]:
                        toToolTip = toToolTip + str(k) + tab + "=> " + str(currDict.get(k))
                    else:
                        toToolTip = toToolTip + str(k) + tab + " => " + str(currDict.get(k)) + "\n"
                Journal.parent.tableJournal.setToolTip(toToolTip)
            else:
                Journal.parent.tableJournal.setToolTip("Data not found")
                self.signalId = None
        else:
            Journal.parent.tableJournal.setToolTip('')

    def feelJournal(self):
        Journal.parent.tableJournal.setRowCount(0)
        Journal.parent.tableJournal.clear()
        headers = ['RFB', 'SN', 'Date test', 'Band', 'Gain', 'Flatnes', 'DSA 1', 'DSA 2', 'DSA 3', 'IMod', 'BIT',
                   'ALC In', 'ALC Out', 'RLoss', 'Status', 'User']
        Journal.parent.tableJournal.setHorizontalHeaderLabels(headers)
        conn, cursor = Journal.parent.getConnDb()
        dateBegin = int(str(Journal.parent.journalDateStart.date().toPyDate()).replace('-', ''))
        dateEnd = int(str(Journal.parent.journalDateStop.date().toPyDate()).replace('-', ''))
        q1 = "select * from test_results where cast(substr(dateTest,0,9) AS INTEGER) between %s and %s" \
             % (dateBegin, dateEnd)
        q = "select * from ("+q1+") where (rfb_type like '%"+Journal.parent.journalFilter.text()+"%' or sn like '%" + \
            Journal.parent.journalFilter.text()+"%') order by dateTest DESC"
        rows = cursor.execute(q).fetchall()
        for row in rows:
            numrows = Journal.parent.tableJournal.rowCount()
            Journal.parent.tableJournal.insertRow(numrows)
            limitsDictKey = row[1] + row[4]
            j = 1
            while j < len(row):

                if row[j] is None:
                    toCell = ''
                else:
                    toCell = row[j]
                Journal.parent.tableJournal.setItem(numrows, j-1, QTableWidgetItem(str(toCell)))
                if toCell == 'Pass':
                    Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.green)
                if toCell == 'Warning':
                    Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.yellow)
                if toCell == 'Fail':
                    Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.red)
                if j == 5:
                    q = "select gain_dl_min, gain_dl_max, gain_ul_min, gain_ul_max from ATR where rfb_type = '%s'" \
                        % (row[1])
                    limits = cursor.execute(q).fetchall()[0]
                    try:
                        if toFloat(row[5]):
                            gain = toFloat(row[5])
                            if str(row[4]) == 'Dl':
                                self.limitsDict.update({limitsDictKey + '_gainMin': limits[0],
                                                        limitsDictKey + '_gainMax': limits[1]})
                                if not limits[0]-2 <= gain <= limits[1]+5:
                                    Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.red)
                                elif not limits[0] <= gain <= limits[1]:
                                    Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.yellow)
                            else:
                                self.limitsDict.update({limitsDictKey + '_gainMin': limits[2],
                                                        limitsDictKey + '_gainMax': limits[3]})
                                if not limits[2]-2 <= gain <= limits[3]+5:
                                    Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.red)
                                elif not limits[2] <= gain <= limits[3]:
                                    Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.yellow)
                    except:
                        j += 1
                        continue
                j += 1
        conn.close()
        try:
            self.parent.onResize
        except Exception as e:
            self.parent.sendMsg('c', 'RFBCheck', 'Filling fail:\n' + str(e), 1)

    def deleteRecords(self):
        sn, dateTest = self.getSelectedRow()
        q = self.parent.sendMsg('i', 'Delete record', 'Will be remove test record for RF board %s. Are you sure?'
                                % sn, 2)
        if q == QtWidgets.QMessageBox.Ok:
            try:
                conn, cursor = Journal.parent.getConnDb()
                arrRemove = []
                q1 = "select id from test_results where sn = '%s' and dateTest = '%s'" % (sn, dateTest)
                arrRemove.append("delete from dsa_results where rfb = (%s)" % q1)
                arrRemove.append("delete from imod_result where rfb = (%s)" % q1)
                arrRemove.append("delete from flat_result where rfb = (%s)" % q1)
                arrRemove.append("delete from test_results where sn = '%s' and dateTest = '%s'" % (sn, dateTest))
                for i in arrRemove:
                    cursor.execute(i)
                conn.commit()
                conn.close
                self.feelJournal()
            except Exception as e:
                self.parent.sendMsg('w', 'Delete test record error', str(e), 1)

    def getSelectedRow(self):
        sn = self.parent.tableJournal.item(self.parent.tableJournal.currentRow(), 1).text()
        dateTest = self.parent.tableJournal.item(self.parent.tableJournal.currentRow(), 2).text()
        return sn, dateTest

    def tableDoubleClick(self, row, column):
        if self.signalId:
            if column == 5:
                self.signalPlot(row, column)
            if column == 9:
                self.imodPlot(row, column)

    def signalPlot(self, row, column):
        try:
            conn, cursor = Journal.parent.getConnDb()
            q = "select signal from flat_result where id = %s" % self.signalId
            rows = cursor.execute(q).fetchone()
            keys = sorted(ast.literal_eval(rows[0]).keys())
            signalDict = ast.literal_eval(rows[0])
            x1 = []
            x2 = []
            y1 = []
            y2 = []
            old = None
            for k in keys:
                if old is None:
                    old = k
                    x1.append(k)
                    y1.append(signalDict.get(k))
                elif k - old != .5:
                    x2.append(k)
                    y2.append(signalDict.get(k))
                    old = k
                if len(y2) == 0:
                    x1.append(k)
                    y1.append(signalDict.get(k))
                    old = k
                else:
                    x2.append(k)
                    y2.append(signalDict.get(k))
                    old = k
            sn, dateTest = self.getSelectedRow()
            rfb = Journal.parent.tableJournal.item(row, 0).text()
            whatConn = Journal.parent.tableJournal.item(row, 3).text()
            locator = matplotlib.ticker.MultipleLocator(base=1)
            plt.figure('Flatness ' + str(rfb) + ' ' + str(sn) + ' ' + str(whatConn))
            if len(x2) != 0:
                axes = plt.subplot(211)
            else:
                axes = plt.subplot(111)
            axes.yaxis.set_major_locator(locator)
            title = ('Flatness test result: %s %s %s\nDate test: %s') % \
                    (str(rfb), str(sn), str(whatConn), str(dateTest))
            plt.title(title)
            plt.ylabel('gain dB')
            plt.grid(True)
            plt.plot(x1, y1, color="blue", linewidth=1, linestyle="-")
            self.setAnnotate(signalDict)
            legendText = 'Flatness = %s dB' % str(self.flatness)
            plt.legend([legendText], loc='upper left')
            if len(x2) != 0:
                axes = plt.subplot(212)
                axes.yaxis.set_major_locator(locator)
                plt.plot(x2, y2, color="blue", linewidth=1, linestyle="-")
                self.setAnnotate(signalDict)
                plt.ylabel('gain dB')
                plt.grid(True)
            plt.xlabel('frequency MHz')
            # plt.savefig(name + ".png")
            plt.show()
        except Exception as e:
            self.parent.sendMsg('w', 'Get signal data error', str(e), 1)
            return

    def imodPlot(self, row, column):
        try:
            conn, cursor = Journal.parent.getConnDb()
            q = "select signal from imod_result where id = %s" % self.signalId
            rows = cursor.execute(q).fetchone()
            keys = sorted(ast.literal_eval(rows[0]).keys())
            signalDict = ast.literal_eval(rows[0])
            maxGain = signalDict.get(max(signalDict.keys(), key=(lambda k: signalDict[k])))
            x1 = []
            y1 = []
            for k in keys:
                x1.append(k)
                y1.append(signalDict.get(k))
            sn, dateTest = self.getSelectedRow()
            rfb = Journal.parent.tableJournal.item(row, 0).text()
            whatConn = Journal.parent.tableJournal.item(row, 3).text()
            plt.figure('IMod ' + str(rfb) + ' ' + str(sn) + ' ' + str(whatConn))
            axes = plt.subplot(111)
            plt.plot(x1, y1, color="blue", linewidth=1, linestyle="-")
            if whatConn == 'Dl':
                freq = cursor.execute("select dl_freq from test_settings where rfb_type = '" + rfb + "'").fetchone()[0]
            else:
                freq = cursor.execute("select ul_freq from test_settings where rfb_type = '" + rfb + "'").fetchone()[0]

            for i in [-1.5, -.5, .5, 1.5]:
                peak = signalDict.get(freq + i)
                annText = 'Peak: %s dB\nfreq. %s MHz' % (str(peak), str(freq + i))
                plt.annotate(annText, xy=(freq + i, peak), xycoords='data',
                             xytext=(freq + i + .5, peak + 1), textcoords='data',
                             size=6, va="center", ha="center",
                             bbox=dict(boxstyle="round4", fc="w"),
                             arrowprops=dict(arrowstyle="-|>",
                                             connectionstyle="arc3,rad=0.2",
                                             relpos=(0., 0.),
                                             fc="w"))
            plt.axhline(y=maxGain - 50, xmin=0, xmax=1, color='red', linewidth=1)
            title = ('Intermodulation test result: %s %s %s\nDate test: %s') % \
                    (str(rfb), str(sn), str(whatConn), str(dateTest))
            plt.title(title)
            plt.ylabel('gain dB')
            plt.xlabel('frequency MHz')
            plt.grid(True)
            plt.show()
            conn.close()
        except Exception as e:
            self.parent.sendMsg('w', 'Get IMod data error', str(e), 1)
            return

    def setAnnotate(self, signalDict):
        minKey, minGain, maxKey, maxGain = self.getMinMaxDict(signalDict)
        annText = 'MIN: %s dB\nfreq. %s MHz' % (str(minGain), str(minKey))
        plt.annotate(annText, xy=(minKey, minGain), xycoords='data',
                     xytext=(minKey, minGain + 1), textcoords='data',
                     size=6, va="center", ha="center",
                     bbox=dict(boxstyle="round4", fc="w"),
                     arrowprops=dict(arrowstyle="-|>",
                                     connectionstyle="arc3,rad=0.2",
                                     relpos=(0., 0.),
                                     fc="w"))
        annText = 'MAX: %s dB\nfreq. %s MHz' % (str(maxGain), str(maxKey))
        plt.annotate(annText, xy=(maxKey, maxGain), xycoords='data',
                     xytext=(maxKey, maxGain - 1), textcoords='data',
                     size=6, va="center", ha="center",
                     bbox=dict(boxstyle="round4", fc="w"),
                     arrowprops=dict(arrowstyle="-|>",
                                     connectionstyle="arc3,rad=0.2",
                                     relpos=(0., 0.),
                                     fc="w"))

    def getMinMaxDict(self, obj):
        minKey = min(obj.keys(), key=(lambda k: obj[k]))
        maxKey = max(obj.keys(), key=(lambda k: obj[k]))
        minGain = obj.get(minKey)
        maxGain = obj.get(maxKey)
        self.flatness = abs(maxGain - minGain)
        return minKey, minGain, maxKey, maxGain