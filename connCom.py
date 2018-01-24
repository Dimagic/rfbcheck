import serial
from PyQt5.QtWidgets import QMessageBox


class connCom:
    def __init__(self):
        print('Com init')
        self.ser = serial.Serial()
        self.baud = 57600
        self.port = "COM1"
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.5)
            return(self.ser)
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Connection problem")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()



