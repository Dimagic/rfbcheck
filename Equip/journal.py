from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import QtCore, QtGui, QtWidgets
from Equip.equip import toFloat
import matplotlib.pyplot as plt
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
        self.feelJournal()

    def cellHover(self, row, column):
        item = Journal.parent.tableJournal.item(row, column)
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        qrow = "select id from test_results where sn = '%s' and dateTest = '%s' and band_type = '%s'" % \
               (Journal.parent.tableJournal.item(row, 1).text(),
                Journal.parent.tableJournal.item(row, 2).text(),
                Journal.parent.tableJournal.item(row, 3).text())
        if column == 5:
            q = "select id from flat_result where rfb  = (%s)" % qrow
        elif column == 6:
            q = "select dsa1 from dsa_results where rfb = (%s)" % qrow
        elif column == 7:
            q = "select dsa2 from dsa_results where rfb = (%s)" % qrow
        elif column == 8:
            q = "select dsa3 from dsa_results where rfb = (%s)" % qrow
        else:
            q = ''

        if q != '':
            conn, cursor = Journal.parent.getConnDb()
            rows = cursor.execute(q).fetchone()
            conn.close()
            if rows is not None:
                if column == 5:
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
                   'ALC In', 'ALC Out', 'RLoss','Status', 'User']
        Journal.parent.tableJournal.setHorizontalHeaderLabels(headers)
        conn, cursor = Journal.parent.getConnDb()
        dateBegin = int(str(Journal.parent.journalDateStart.date().toPyDate()).replace('-', ''))
        dateEnd = int(str(Journal.parent.journalDateStop.date().toPyDate()).replace('-', ''))
        q1 = "select * from test_results where cast(substr(dateTest,0,9) AS INTEGER) between %s and %s" \
             % (dateBegin, dateEnd)
        q = "select * from ("+q1+") where (rfb_type like '%"+Journal.parent.journalFilter.text()+"%' or sn like '%" + \
            Journal.parent.journalFilter.text()+"%') order by dateTest DESC"
        # TODO: set pass/fail for numeric data (make limits dictionary)
        rows = cursor.execute(q).fetchall()
        for row in rows:
            numrows = Journal.parent.tableJournal.rowCount()
            Journal.parent.tableJournal.insertRow(numrows)
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
                    if toFloat(row[5]):
                        gain = toFloat(row[5])
                        if str(row[4]) == 'Dl':
                            if not limits[0]-2 <= gain <= limits[1]+2:
                                Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.red)
                            elif not limits[0] <= gain <= limits[1]:
                                Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.yellow)
                        else:
                            if not limits[2]-2 <= gain <= limits[3]+2:
                                Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.red)
                            elif not limits[2] <= gain <= limits[3]:
                                Journal.parent.tableJournal.item(numrows, j - 1).setBackground(QtCore.Qt.yellow)

                j += 1
        conn.close()
        try:
            self.parent.onResize
        except Exception:
            return

    def deleteRecords(self):
        sn, dateTest = self.getSelectedRow()
        q = self.parent.sendMsg('i', 'Delete record', 'Will be remove test record for RF board %s. Are you sure?'
                                % sn, 2)
        if q == QtWidgets.QMessageBox.Ok:
            try:
                conn, cursor = Journal.parent.getConnDb()
                q1 = "select id from test_results where sn = '%s' and dateTest = '%s'" % (sn, dateTest)
                q2 = "delete from dsa_results where rfb = (%s)" % (q1)
                q3 = "delete from test_results where sn = '%s' and dateTest = '%s'" % (sn, dateTest)
                cursor.execute(q2)
                cursor.execute(q3)
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
        if self.signalId is None or column != 5:
            return
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
                    y1.append(k)
                    x1.append(signalDict.get(k))
                elif k - old != .5:
                    y2.append(k)
                    x2.append(signalDict.get(k))
                    old = k
                if len(y2) == 0:
                    y1.append(k)
                    x1.append(signalDict.get(k))
                    old = k
                else:
                    y2.append(k)
                    x2.append(signalDict.get(k))
                    old = k

            sn, dateTest = self.getSelectedRow()
            rfb = Journal.parent.tableJournal.item(row, 0).text()
            whatConn = Journal.parent.tableJournal.item(row, 3).text()
            name = str(sn) + '_' + str(dateTest)

            plt.figure(str(rfb) + ' ' + str(sn) + ' ' + str(whatConn))
            if len(y2) != 0:
                plt.subplot(211)
            title = ('Flatness test result: %s %s %s\nDate test: %s') % \
                    (str(rfb), str(sn), str(whatConn), str(dateTest))
            plt.title(title)
            plt.ylabel('gain dB')
            plt.grid(True)
            plt.plot(y1, x1, color="blue", linewidth=1, linestyle="-")
            if len(y2) != 0:
                plt.subplot(212)
                plt.plot(y2, x2, color="blue", linewidth=1, linestyle="-")
                plt.ylabel('gain dB')
                plt.grid(True)
            plt.xlabel('frequency MHz')
            # plt.annotate('local max', xy=(2, 1), xytext=(3, 1.5),
            #              arrowprops=dict(facecolor='black', shrink=0.05),
            #              )
            # plt.savefig(name + ".png")
            plt.show()
        except Exception as e:
            self.parent.sendMsg('w', 'Get signal data error', str(e), 1)
            return