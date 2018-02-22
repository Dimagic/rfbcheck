from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
import serial.tools.list_ports


class SelectComPort(QtWidgets.QDialog):
    def __init__(self, parent):
        super(SelectComPort, self).__init__(parent)
        self.currParent = parent
        self.dialog = loadUi('Forms/comPort.ui', self)
        self.dialog.setWindowTitle('Select port')
        self.dialog.setWindowIcon(parent.appIcon)

        port, baud = self.getCurrPortBaud()
        self.currentPort.setText(port)
        self.currentBaud.setText(baud)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.okPressed)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancelPressed)

        self.bauds = [4800, 9600, 19200, 38400, 57600, 115200, 230400]
        # self.onlyInt = QIntValidator()
        # self.baud.setValidator(self.onlyInt)

        self.getPortsBauds()

    def getPortsBauds(self):
        pass
        # Get available COM ports
        listCom = list(serial.tools.list_ports.comports())
        if len(listCom) > 0:
            for i in listCom:
                self.portBox.addItem(i[0])
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
            self.currParent.sendMsg('w', 'Warning', 'COM ports not found', 1)
        for i in self.bauds:
            self.baudBox.addItem(str(i))
        self.dialog.show()

    def getCurrPortBaud(self):
        try:
            conn, cursor = self.currParent.getConnDb()
            q = "select port, baud from settings"
            rows = cursor.execute(q).fetchone()
            return str(rows[0]), str(rows[1])
        except Exception as e:
            self.currParent.sendMsg('c', 'Get port settings error', str(e), 1)
        finally:
            conn.close()

    def okPressed(self):
        try:
            conn, cursor = self.currParent.getConnDb()
            q = "update settings set port = '%s', baud = %s" % (str(self.portBox.currentText()),
                                                                str(self.baudBox.currentText()))
            cursor.execute(q)
            conn.commit()
            conn.close()
            self.getCurrPortBaud()
            self.currParent.sendMsg('i', 'Save settings', 'Done', 1)
        except Exception as e:
            self.currParent.sendMsg('c', 'Writing port settings error', str(e), 1)
        finally:
            self.dialog.close()

    def cancelPressed(self):
        self.dialog.close()