import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget
from Forms.listAtr import Ui_newWindow

class newWindow(QWidget):
     def __init__(self, parent=None):
        super(newWindow, self).__init__(parent)

        self.ui=Ui_newWindow()
        self.ui.setupUi(self)