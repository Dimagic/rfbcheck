import datetime
import sqlite3

class WriteResult:
    def __init__(self, testController, testLogDl, testLogUl):
        self.testController = testController
        self.parent = testController.getParrent()
        try:
            dateTest = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")
            if len(testLogDl) > 0:
                self.writingToDB(self.parent, testLogDl, 'Dl', dateTest)
            if len(testLogUl) > 0:
                self.writingToDB(self.parent, testLogUl, 'Ul', dateTest)
        except Exception as e:
            testController.sendMsgSignal.emit('w', 'Write results to DB error', str(e), 1)
            return

        self.testController.testLogDl = {}
        self.testController.testLogUl = {}

    def writingToDB(self, parent, currTestLog, band, dateTest):
        conn, cursor = parent.getConnDb()
        try:
            cursor.execute("insert into test_results(rfb_type,sn,dateTest,band_type,gain,flatness,dsa1,dsa2,dsa3,imod,"
                           "bit,alcin,alcout,test_status) values (:rfb_type,:sn,:dateTest,:band_type,:gain,"
                           ":flatness,:dsa1,:dsa2,:dsa3,:imod,:bit,:alcin,:alcout,:test_status)",
                        {'rfb_type': parent.rfbTypeCombo.currentText(), 'sn': parent.rfbSN.text(), 'dateTest': dateTest,
                         'band_type': band, 'gain': currTestLog.get('Gain'),\
                        'flatness': currTestLog.get('Flatness'), 'dsa3': currTestLog.get('DSA 3'),
                         'dsa2': currTestLog.get('DSA 2'), 'dsa1': currTestLog.get('DSA 1'),
                        'imod': currTestLog.get('IMod'), 'bit': currTestLog.get('BIT'), 'alcin': currTestLog.get('ALC in'),
                         'alcout': currTestLog.get('ALC out'), 'test_status': ''})
            conn.commit()

            # print(self.testController.to_DsaUlDl.keys())
            if 'Ul1' in self.testController.to_DsaUlDl.keys() and band == 'Ul':
                q = "insert into dsa_results (rfb,dsa1,dsa2,dsa3) values ((select max(id) from test_results " \
                    "where band_type = 'Ul' and sn = '%s'),'%s','%s','%s')" % (parent.rfbSN.text(),
                                                                               self.testController.to_DsaUlDl.get('Ul1'),
                                                                               self.testController.to_DsaUlDl.get('Ul2'),
                                                                               self.testController.to_DsaUlDl.get('Ul3'))
                cursor.execute(q)
                conn.commit()
            if 'Dl1' in self.testController.to_DsaUlDl.keys() and band == 'Dl':
                q = "insert into dsa_results (rfb,dsa1,dsa2,dsa3) values ((select max(id) from test_results " \
                    "where band_type = 'Dl' and sn = '%s'),'%s','%s','%s')" % (parent.rfbSN.text(),
                                                                               self.testController.to_DsaUlDl.get('Dl1'),
                                                                               self.testController.to_DsaUlDl.get('Dl2'),
                                                                               self.testController.to_DsaUlDl.get('Dl3'))
                cursor.execute(q)
                conn.commit()
            self.testController.logSignal.emit('Writing test result complete', 0)

        except sqlite3.DatabaseError as err:
                self.testController.sendMsgSignal.emit('c', 'Querry error', str(err), 1)
                conn.close()
        else:
                conn.close()
                # report(parent,parent.rfbSN.text(),dateTest)




