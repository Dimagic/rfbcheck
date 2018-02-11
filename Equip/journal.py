from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import QtCore, QtGui, QtWidgets
import ast
from Equip.equip import toFloat


class Journal:
    parent = None

    def __init__(self, parent):
        Journal.parent = parent
        self.parent = parent
        # self.current_hover = [0, 0]
        parent.tableJournal.cellEntered.connect(self.cellHover)
        self.feelJournal()

    @staticmethod
    def cellHover(row, column):
        item = Journal.parent.tableJournal.item(row, column)
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        if column == 6:
            q = "select dsa1 from dsa_results where rfb = (select id from test_results where sn = '%s' and " \
                "dateTest = '%s' and band_type = '%s')" % (Journal.parent.tableJournal.item(row, 1).text(),
                                                           Journal.parent.tableJournal.item(row, 2).text(),
                                                           Journal.parent.tableJournal.item(row, 3).text())
        elif column == 7:
            q = "select dsa2 from dsa_results where rfb = (select id from test_results where sn = '%s' and " \
                "dateTest = '%s' and band_type = '%s')" % (Journal.parent.tableJournal.item(row, 1).text(),
                                                           Journal.parent.tableJournal.item(row, 2).text(),
                                                           Journal.parent.tableJournal.item(row, 3).text())
        elif column == 8:
            q = "select dsa3 from dsa_results where rfb = (select id from test_results where sn = '%s' and " \
                "dateTest = '%s' and band_type = '%s')" % (Journal.parent.tableJournal.item(row, 1).text(),
                                                           Journal.parent.tableJournal.item(row, 2).text(),
                                                           Journal.parent.tableJournal.item(row, 3).text())
        else:
            q = ''

        if q != '':
            conn, cursor = Journal.parent.getConnDb()
            rows = cursor.execute(q).fetchone()
            conn.close()
            if rows is not None:
                currDict = ast.literal_eval(rows[0])
                toToolTip = ""
                for k in sorted(currDict.keys()):
                    tab = ""
                    for i in range(1,5 - len(str(k))):
                        tab += " "
                    if k == sorted(currDict.keys())[len(currDict.keys()) - 1]:
                        toToolTip = toToolTip + str(k) + tab + "=> " + str(currDict.get(k))
                    else:
                        toToolTip = toToolTip + str(k) + tab + " => " + str(currDict.get(k)) + "\n"
                Journal.parent.tableJournal.setToolTip(toToolTip)
            else:
                Journal.parent.tableJournal.setToolTip("Data not found")
        else:
            Journal.parent.tableJournal.setToolTip('')

    def feelJournal(self):
        Journal.parent.tableJournal.setRowCount(0)
        Journal.parent.tableJournal.clear()
        headers = ['RFB', 'SN', 'Date test', 'Band', 'Gain', 'Flatnes', 'DSA 1', 'DSA 2', 'DSA 3', 'IMod', 'BIT',
                   'ALC In', 'ALC Out', 'Status', 'User']
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
                    if str(row[5]).isdigit():
                        gain = toFloat(row[5])
                j += 1
        conn.close()

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
