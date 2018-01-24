#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from Forms.listAtr import *


class listAtr(Ui_newWindow):
    def __init__(self, parent=None):
        super(listAtr, self).__init__(parent)
        listAtr.show()


class First(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(First, self).__init__(parent)
        self.pushButton = QtWidgets.QPushButton("click me")

        self.setCentralWidget(self.pushButton)

        self.pushButton.clicked.connect(self.on_pushButton_clicked)
        self.dialog = listAtr(self)

    def on_pushButton_clicked(self):
        self.dialog.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = First()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()