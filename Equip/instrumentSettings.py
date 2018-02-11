from PyQt5 import QtWidgets
from PyQt5.uic import loadUi


class TestSettings(QtWidgets.QDialog):
    def __init__(self, parent):
        super(TestSettings, self).__init__(parent)
        self.currParent = parent
        self.dialog = loadUi('Forms/initInstrumetSettings.ui', self)
        self.dialog.setWindowTitle('Instrumet settings')
        self.dialog.setWindowIcon(parent.appIcon)

        self.addBtn.clicked.connect(self.addBtnClick)
        self.delBtn.clicked.connect(self.delBtnClick)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.okPressed)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancelPressed)

        self.fillTestListCombo()

        self.dialog.show()

    def fillTestListCombo(self):
        try:
            conn, cursor = self.currParent.getConnDb()
            rows = cursor.execute("select * from test_list").fetchall()
            for row in rows:
                self.testListCombo.addItem(row[1])
            conn.close()
        except Exception as e:
            self.currParent.sendMsg('c', 'Getting test list error', str(e), 1)
            return

    def addBtnClick(self):
        numrows = self.initInstrTable.rowCount()
        self.initInstrTable.insertRow(numrows)

    def delBtnClick(self):
        self.initInstrTable.removeRow(self.initInstrTable.currentRow())

    def okPressed(self):
        for i in range(self.initInstrTable.rowCount()):
            print(self.initInstrTable.item(i, 0).text())


    def cancelPressed(self):
        self.close()
