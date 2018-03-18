#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt
from Forms.RFBedit import *
import re
import sqlite3
import sys


class EditRFB(QtWidgets.QDialog, Ui_RFBedit):
    def __init__(self, RFBedit, parent):
        super(EditRFB, self).__init__(parent)
        self.ui = Ui_RFBedit()
        self.ui.setupUi(self)
        self.parent = parent

        self.listATRSettings = {}
        self.listTestSettings = {}

        self.listATRNameColumn = []
        self.listTestNameColumn = []

        self.listNameColumn = []

        self.ui.saveBtn.clicked.connect(self.saveBtnClicked)
        self.ui.closeBtn.clicked.connect(self.closeBtnClicked)
        self.ui.showAllBtn.clicked.connect(self.showAllBtnClicked)

        self.ui.newAdem.textChanged.connect(self.isThisNewAdem)
        self.ui.rfbName.textChanged.connect(self.isThisNewRfb)

        self.getSettings('ATR')
        self.initTableSettings('ATR')
        self.getSettings('test_settings')
        self.initTableSettings('test_settings')

        rows = self.selectQuery("select name from adem_type")
        for row in rows:
            self.ui.ademCombo.addItem(row[0])

        self.ui.rfbName.setText(self.parent.editRfbCombo.currentText())
        if self.ui.rfbName.text() != 'New':
            self.ui.rfbName.setEnabled(False)
            allAdems = [self.ui.ademCombo.itemText(i) for i in range(self.ui.ademCombo.count())]
            q = "select adem from rfb_type where name = '%s'" % self.ui.rfbName.text()
            currAdem = self.selectQuery(q)[0][0]
            for i, j in enumerate(allAdems):
                if currAdem == j:
                    self.ui.ademCombo.setCurrentIndex(i)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeBtnClicked(self):
        self.close()

    def isThisNewRfb(self):
        rfb = self.ui.rfbName.text().replace(' ', '').upper()
        item = QtWidgets.QTableWidgetItem(rfb)
        item.setFlags(QtCore.Qt.ItemIsEditable)
        self.ui.tableAtrSettings.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem(rfb)
        item.setFlags(QtCore.Qt.ItemIsEditable)
        self.ui.tableTestSettings.setItem(0, 1, item)

    def isThisNewAdem(self):
        pass
        # if len(self.ui.newAdem.text().replace(' ','')) > 0:
        #     self.ui.ademCombo.setEnabled(False)
        # else:
        #     self.ui.ademCombo.setEnabled(True)

    def initTableSettings(self, table):
        if table == 'ATR':
            currTable = self.ui.tableAtrSettings
            currList = self.listATRSettings
        else:
            currTable = self.ui.tableTestSettings
            currList = self.listTestSettings
        currTable.clear()
        currTable.setRowCount(0)
        currTable.setHorizontalHeaderLabels(['Settings', 'Value'])

        for i, j in enumerate(self.listNameColumn[1:]):
            row = currTable.rowCount()
            currTable.insertRow(row)
            item = QTableWidgetItem(QtWidgets.QTableWidgetItem(j))
            item.setFlags(QtCore.Qt.ItemIsEditable)
            currTable.setItem(row, 0, item)
            if self.parent.editRfbCombo.currentText() == 'New':
                item = QtWidgets.QTableWidgetItem('')
                if i == 0: item.setFlags(QtCore.Qt.ItemIsEditable)
                currTable.setItem(row, 1, item)
            elif str(currList.get(j)) == 'None':
                item = QtWidgets.QTableWidgetItem('')
                if i == 0:
                    item = QtWidgets.QTableWidgetItem(str(self.ui.rfbName.text()))
                    item.setFlags(QtCore.Qt.ItemIsEditable)
                currTable.setItem(row, 1, item)
            else:
                item = QtWidgets.QTableWidgetItem(str(currList.get(j)))
                if i == 0:
                    item = QtWidgets.QTableWidgetItem(str(self.ui.rfbName.text()))
                    item.setFlags(QtCore.Qt.ItemIsEditable)
                currTable.setItem(row, 1, item)

        #self.ui.tableAtrSettings.resizeColumnsToContents()

    def showAllBtnClicked(self):
        pass
        # self.dialog = EditRFB(self, self)
        # self.dialog.setWindowIcon(self.appIcon)
        # self.dialog.show()

    def saveBtnClicked(self):
        if len(self.ui.newAdem.text()) != 0:                                             #
            atrName = self.ui.newAdem.text().replace(' ', '').upper()                    # If  new ADEM
            q = self.checkDoubleRecords('adem_type', 'name', atrName)                    #
            if q != 0:                                                                   #
               self.parent.sendMsg('w', 'Warning', 'Adem '+atrName+' already present', 1)
               return
            query = "insert into adem_type (name) values(%s)" % atrName
            self.insertQuery(query)
            if self.checkDoubleRecords('adem_type', 'name', atrName) != 0:
                self.parent.sendMsg('i', 'Done', 'Adem '+atrName+' writed to data base', 1)

        if self.parent.editRfbCombo.currentText() == 'New':                              #
            rfbName = self.ui.rfbName.text().replace(' ', '')                            # If new RFB
            q = self.checkDoubleRecords('rfb_type', 'name', rfbName)                     #
            if q != 0:                                                                   #
                self.parent.sendMsg('w', 'Warning', 'RFB '+rfbName+' already present', 1)
                return

        for k in ['ATR', 'test_settings']:
            if k == 'ATR':
                currTable = self.ui.tableAtrSettings
            else:
                currTable = self.ui.tableTestSettings
            listToWrite = {}
            listToWrite.update({'tmp': k})

            for i in range(0, currTable.rowCount(), 1):
                value = currTable.item(i, 1).text()
                key = currTable.item(i, 0).text()
                if k == 'ATR':
                    if value == '' and key not in ["freq_band_ul_1", "freq_band_dl_1",
                                                   "freq_band_ul_2", "freq_band_dl_2"]:
                       self.parent.sendMsg('w', 'Warning', 'Need to fill all values', 1)
                       return
                    # check freq. expression
                    if value != '' and key in ["freq_band_ul_1", "freq_band_dl_1", "freq_band_ul_2", "freq_band_dl_2"]:
                        r = re.findall('[0-9]+', value)
                        if len(r) != 2:
                            self.parent.sendMsg('w', 'Warning', 'Incorrect freq. line.\n'
                                                                ' You have to use expression like "Freq@Freq"', 1)
                            return
                listToWrite.update({key: value})
            self.writeUpdateRfb(listToWrite)
        self.parent.sendMsg('i', 'Save...', 'Saving data complite', 1)
        self.close()

    def writeUpdateRfb(self, data):
        adem = self.ui.newAdem.text().replace(' ', '').upper()
        if adem == '':
            adem = self.ui.ademCombo.currentText()
        query = "insert or replace into rfb_type (name,adem) values ('%s','%s')" % \
                (self.ui.rfbName.text().replace(' ', '').upper(), adem)
        self.insertQuery(query)

        currTable = data.get('tmp')
        del data['tmp']

        keys = data.keys()
        values = []
        for k in keys:
            values.append(data.get(k))
        query = "insert or replace into %s" % currTable
        query = query + "(" + ','.join((str(n) for n in keys)) + ") values('" + "','".join((str(k) for k in values)) + "')"
        print(query)
        self.insertQuery(query)

    def insertQuery(self, query):
        try:
            conn, cursor = self.parent.getConnDb()
            cursor.execute(query)
            conn.commit()
            conn.close()
        except Exception as e:
            self.parent.sendMsg('w', 'EditRFB@insertQuery', str(e), 1)

    def selectQuery(self, query):
        try:
            conn, cursor = self.parent.getConnDb()
            rows = cursor.execute(query).fetchall()
            conn.close()
            return rows
        except Exception as e:
            self.parent.sendMsg('w', 'EditRFB@insertQuery', str(e), 1)

    def checkDoubleRecords(self, table, name, value):
        query = "select count() from %s where %s = '%s'" % (table, name, value.upper())
        rows = self.selectQuery(query)
        r = re.findall('[0-9]+', str(rows[0]))
        return int(r[0])

    def getSettings(self, table):
        query = "PRAGMA table_info(%s)" % table
        self.listNameColumn = []
        listValue = []
        rows = self.selectQuery(query)
        for row in rows:
            if row[0] == 0:
                self.listNameColumn.append(table)
            else:
                self.listNameColumn.append(row[1])

        if self.parent.editRfbCombo.currentText() == 'New':
            return
        query = "select * from %s where %s = '%s'" % (table, self.listNameColumn[1],
                                                      self.parent.editRfbCombo.currentText())
        rows = self.selectQuery(query)
        if rows == []:
            listValue = []
        else:
            listValue = rows[0]
        if table == 'ATR':
            self.listATRSettings = dict(zip(self.listNameColumn, listValue))
        else:
            self.listTestSettings = dict(zip(self.listNameColumn, listValue))




