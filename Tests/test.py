from PyQt5 import QtGui, QtCore

from PyQt5.QtWidgets import QMessageBox


class test(QtCore.QThread):
    def __init__(self):
        pass

    def sendMsg(self, icon, msgTitle, msgText, typeQuestion):
        msg = QMessageBox()
        if icon == 'q':
            msg.setIcon(msg.Question)
        elif icon == 'i':
            msg.setIcon(msg.Information)
        elif icon == 'w':
            msg.setIcon(msg.Warning)
        elif icon == 'c':
            msg.setIcon(msg.Critical)
        msg.setText(msgText)
        msg.setWindowTitle(msgTitle)
        msg.setWindowIcon(QtGui.QIcon("Img/ico32_pgn_icon.ico"))
        if typeQuestion == 1:
            msg.setStandardButtons(msg.Ok)
        elif typeQuestion == 2:
            msg.setStandardButtons(msg.Ok | msg.Cancel)
        elif typeQuestion == 3:
            msg.setStandardButtons(msg.Ignore | msg.Retry | msg.Cancel)
        return msg.exec_()




