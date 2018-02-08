from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog
from PyQt5.uic import loadUi


class SelectUser(QtWidgets.QDialog):
    def __init__(self, parent):
        super(SelectUser, self).__init__(parent)
        self.currParent = parent
        self.dialog = loadUi('Forms/selectuser.ui', self)
        self.dialog.setWindowTitle('Select user')
        self.dialog.setWindowIcon(parent.appIcon)
        self.dialog.show()
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.okPressed)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancelPressed)
        self.addUserBtn.clicked.connect(self.addUser)
        self.getUsers()

    def getUsers(self):
        conn, cursor = self.currParent.getConnDb()
        rows = cursor.execute("select name from users order by name").fetchall()
        for row in rows:
            self.userComboBox.addItem(str(row[0]))
        conn.close()

    def addUser(self):
        nameUser, ok = QInputDialog.getText(self, 'New user', 'Enter new user name:')
        if ok:
            try:
                conn, cursor = self.currParent.getConnDb()
                q = "select count() from users where upper(name) = '%s'" % (str(nameUser).upper())
                count = cursor.execute(q).fetchone()[0]
                if int(count) > 0:
                    self.currParent.sendMsg('w', 'New user', 'User %s already present' % str(nameUser), 1)
                    self.addUser()
                else:
                    q = "insert into users (name) values ('%s')" % str(nameUser)
                    print(q)
                    cursor.execute(q)
                    conn.commit()
                    conn.close()
            except Exception as e:
                self.currParent.sendMsg('c', 'New user error', str(e), 1)
            finally:
                self.getUsers()

    def okPressed(self):
        try:
            conn, cursor = self.currParent.getConnDb()
            q = "update settings set lastUser = '%s'" % (str(self.userComboBox.currentText()))
            cursor.execute(q)
            conn.commit()
            conn.close()
            self.currParent.setUser()
        except Exception as e:
            self.currParent.sendMsg('c', 'Writing new user error', str(e), 1)
        finally:
            self.dialog.close()

    def cancelPressed(self):
        self.dialog.close()
