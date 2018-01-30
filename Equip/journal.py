from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt5 import QtCore, QtGui, QtWidgets
import ast
from Equip.equip import toFloat




class Journal():
    parent = None
    def __init__(self,parent):
        Journal.parent = parent

        self.current_hover = [0, 0]
        parent.tableJournal.cellEntered.connect(self.cellHover)
        self.feelJournal()

    def cellHover(self, row, column):
        item = Journal.parent.tableJournal.item(row, column)
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        #print(row,column)
        if column == 6:
            q = "select dsa1 from dsa_results where rfb = (select id from test_results where sn = '%s' and dateTest = '%s' and band_type = '%s')" % (Journal.parent.tableJournal.item(row, 1).text(), Journal.parent.tableJournal.item(row, 2).text(),Journal.parent.tableJournal.item(row, 3).text())
        elif column == 7:
            q = "select dsa2 from dsa_results where rfb = (select id from test_results where sn = '%s' and dateTest = '%s' and band_type = '%s')" % (Journal.parent.tableJournal.item(row, 1).text(), Journal.parent.tableJournal.item(row, 2).text(),Journal.parent.tableJournal.item(row, 3).text())
        elif column == 8:
            q = "select dsa3 from dsa_results where rfb = (select id from test_results where sn = '%s' and dateTest = '%s' and band_type = '%s')" % (Journal.parent.tableJournal.item(row, 1).text(), Journal.parent.tableJournal.item(row, 2).text(),Journal.parent.tableJournal.item(row, 3).text())
        else:
            q = ''

        if q != '':
            conn,cursor = Journal.parent.getConnDb()
            rows = cursor.execute(q).fetchone()
            conn.close()
            #print(rows)
            #Journal.parent.tableJournal.setToolTip(item.text())
            if rows != None:
                dict =  ast.literal_eval(rows[0])
                toToolTip = ""

                for k in sorted(dict.keys()):
                    tab = ""
                    for i in range(1,5 - len(str(k))):
                        tab += " "
                    if k == sorted(dict.keys())[len(dict.keys()) - 1]:
                        toToolTip = toToolTip + str(k) + tab + "=> " + str(dict.get(k))
                    else:
                        toToolTip = toToolTip + str(k) + tab + " => " + str(dict.get(k)) + "\n"
                Journal.parent.tableJournal.setToolTip(toToolTip)
            else:
                Journal.parent.tableJournal.setToolTip("Data not found")
        else:
            Journal.parent.tableJournal.setToolTip('')
            #QtWidgets.QToolTip.showText(event.globalPos(), item.text(), self)
##        Journal.parent.setToolTip(item.text())
##        print(item.text())
##        old_item = Journal.parent.tableJournal.item(self.current_hover[0], self.current_hover[1])
##        if self.current_hover != [row,column]:
##            old_item.setBackground(QBrush(QColor('white')))
##            item.setBackground(QBrush(QColor('yellow')))
##        self.current_hover = [row, column]



    def feelJournal(self):
        Journal.parent.tableJournal.setRowCount(0)
        Journal.parent.tableJournal.clear()
        headers = ['RFB','SN','Date test','Band','Gain','Flatnes','DSA 1','DSA 2','DSA 3','IMod','BIT','ALC In','ALC Out']
        # TODO: FIX QObject::connect: Cannot queue arguments of type 'Qt::Orientation'
        Journal.parent.tableJournal.setHorizontalHeaderLabels(headers)
        conn, cursor = Journal.parent.getConnDb()
        dateBegin = int(str(Journal.parent.journalDateStart.date().toPyDate()).replace('-', ''))
        dateEnd   = int(str(Journal.parent.journalDateStop.date().toPyDate()).replace('-', ''))
        q1 = "select * from test_results where cast(substr(dateTest,0,9) AS INTEGER) between %s and %s" % (dateBegin, dateEnd)
        q = "select * from ("+q1+") where (rfb_type like '%"+Journal.parent.journalFilter.text()+"%' or sn like '%"+Journal.parent.journalFilter.text()+"%') order by dateTest DESC"
        rows = cursor.execute(q).fetchall()
        for row in rows:
            numrows = Journal.parent.tableJournal.rowCount()
            Journal.parent.tableJournal.insertRow(numrows)
            j = 1
            while j < len(row):
                if row[j] == None:
                    toCell = ''
                else:
                    toCell = row[j]
                Journal.parent.tableJournal.setItem(numrows, j-1, QTableWidgetItem(str(toCell)))
                if toCell == 'Pass': Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.green)
                if toCell == 'Warning': Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.yellow)
                if toCell == 'Fail': Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.red)
                if j == 5:
                    q = "select gain_dl_min, gain_dl_max, gain_ul_min, gain_ul_max from ATR where rfb_type = '%s'" % (row[1])
                    limits = cursor.execute(q).fetchall()[0]
                    if str(row[5]).isdigit() == True:
                        gain = toFloat(row[5])
                        #print(row[4])
##                        if row[4] == 'Dl':
##                            if limits[0] <= gain <= limits[1]:
##                                Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.green)
##                            else:
##                                Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.red)
##                        if row[4] == 'Ul':
##                            if limits[2] <= gain <= limits[3]:
##                                Journal.parent.tableJournal.item(numrows, j-1).setBackground(QtCore.Qt.green)




##                alcInIndex = headers.index("ALC In")
##                print(alcInIndex)
##                Journal.parent.tableJournal.setItem(numrows,alcInIndex , QTableWidgetItem(str(toCell)))
##                if 100 <= int(toCell) <= 130: Journal.parent.tableJournal.item(numrows, alcInIndex).setBackground(QtCore.Qt.green)
##                elif 85 <= int(toCell) <= 145: Journal.parent.tableJournal.item(numrows, alcInIndex).setBackground(QtCore.Qt.yellow)
##                else:                     Journal.parent.tableJournal.item(numrows, alcInIndex).setBackground(QtCore.Qt.red)
                j += 1


        conn.close()

##    def getSelectedRow(parent):
##        print('1 '+str(parent))
##        indexes = parent.tableJournal.selectionModel().selectedRows()
##        for index in sorted(indexes):
##            print('Row %d is selected' % index.row())