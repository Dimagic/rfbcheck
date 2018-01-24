# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RFBedit.ui'
#
# Created: Wed Jan  3 15:40:19 2018
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_RFBedit(object):
    def setupUi(self, RFBedit):
        RFBedit.setObjectName("RFBedit")
        RFBedit.setWindowModality(QtCore.Qt.ApplicationModal)
        RFBedit.resize(513, 389)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Img/ico32_pgn_icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        RFBedit.setWindowIcon(icon)
        self.tableAtrSettings = QtWidgets.QTableWidget(RFBedit)
        self.tableAtrSettings.setGeometry(QtCore.QRect(10, 100, 241, 241))
        self.tableAtrSettings.setObjectName("tableAtrSettings")
        self.tableAtrSettings.setColumnCount(2)
        self.tableAtrSettings.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        item.setFont(font)
        self.tableAtrSettings.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        item.setFont(font)
        self.tableAtrSettings.setHorizontalHeaderItem(1, item)
        self.label = QtWidgets.QLabel(RFBedit)
        self.label.setGeometry(QtCore.QRect(30, 10, 31, 20))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(RFBedit)
        self.label_2.setGeometry(QtCore.QRect(30, 40, 31, 20))
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.ademCombo = QtWidgets.QComboBox(RFBedit)
        self.ademCombo.setGeometry(QtCore.QRect(70, 40, 111, 22))
        self.ademCombo.setObjectName("ademCombo")
        self.rfbName = QtWidgets.QLineEdit(RFBedit)
        self.rfbName.setGeometry(QtCore.QRect(70, 10, 111, 20))
        self.rfbName.setObjectName("rfbName")
        self.closeBtn = QtWidgets.QPushButton(RFBedit)
        self.closeBtn.setGeometry(QtCore.QRect(430, 350, 75, 23))
        self.closeBtn.setObjectName("closeBtn")
        self.saveBtn = QtWidgets.QPushButton(RFBedit)
        self.saveBtn.setGeometry(QtCore.QRect(10, 350, 75, 23))
        self.saveBtn.setObjectName("saveBtn")
        self.newAdem = QtWidgets.QLineEdit(RFBedit)
        self.newAdem.setGeometry(QtCore.QRect(70, 70, 111, 20))
        self.newAdem.setObjectName("newAdem")
        self.label_3 = QtWidgets.QLabel(RFBedit)
        self.label_3.setGeometry(QtCore.QRect(0, 70, 61, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.tableTestSettings = QtWidgets.QTableWidget(RFBedit)
        self.tableTestSettings.setGeometry(QtCore.QRect(260, 100, 241, 241))
        self.tableTestSettings.setObjectName("tableTestSettings")
        self.tableTestSettings.setColumnCount(2)
        self.tableTestSettings.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        item.setFont(font)
        self.tableTestSettings.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        item.setFont(font)
        self.tableTestSettings.setHorizontalHeaderItem(1, item)

        self.retranslateUi(RFBedit)
        QtCore.QMetaObject.connectSlotsByName(RFBedit)

    def retranslateUi(self, RFBedit):
        _translate = QtCore.QCoreApplication.translate
        RFBedit.setWindowTitle(_translate("RFBedit", "RFB settings edit..."))
        item = self.tableAtrSettings.horizontalHeaderItem(0)
        item.setText(_translate("RFBedit", "Paremetr"))
        item = self.tableAtrSettings.horizontalHeaderItem(1)
        item.setText(_translate("RFBedit", "Value"))
        self.label.setText(_translate("RFBedit", "RFB:"))
        self.label_2.setText(_translate("RFBedit", "Adem:"))
        self.closeBtn.setText(_translate("RFBedit", "Close"))
        self.saveBtn.setText(_translate("RFBedit", "Save"))
        self.label_3.setText(_translate("RFBedit", "New adem:"))
        item = self.tableTestSettings.horizontalHeaderItem(0)
        item.setText(_translate("RFBedit", "Paremetr"))
        item = self.tableTestSettings.horizontalHeaderItem(1)
        item.setText(_translate("RFBedit", "Value"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    RFBedit = QtWidgets.QDialog()
    ui = Ui_RFBedit()
    ui.setupUi(RFBedit)
    RFBedit.show()
    sys.exit(app.exec_())

