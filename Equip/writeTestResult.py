import datetime
import sqlite3

class WriteResult:
    def __init__(self, testController, testLogDl, testLogUl):
        self.testController = testController
        self.parent = testController.getParent()
        try:
            dateTest = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")
            if len(testLogDl) > 0:
                self.writingToDB(self.parent, testLogDl, 'Dl', dateTest)
            if len(testLogUl) > 0:
                self.writingToDB(self.parent, testLogUl, 'Ul', dateTest)
        except Exception as e:
            self.parent.sendMsg('w', 'Write results to DB error', str(e), 1)
            return
        finally:
            self.parent.testLogDl = {}
            self.parent.testLogUl = {}
            self.parent.to_DsaUlDl = {}

    def writingToDB(self, parent, currTestLog, band, dateTest):
        conn, cursor = parent.getConnDb()
        try:
            cursor.execute("insert into test_results(rfb_type,sn,dateTest,band_type,gain,flatness,dsa1,dsa2,dsa3, imod,"
                           "bit,alcin,alcout,rloss,test_status,user) values (:rfb_type,:sn,:dateTest,:band_type,:gain,"
                           ":flatness,:dsa1,:dsa2,:dsa3,:imod,:bit,:alcin,:alcout, :rloss, :test_status, :user)",
                        {'rfb_type': parent.rfbTypeCombo.currentText(), 'sn': parent.rfbSN.text(), 'dateTest': dateTest,
                         'band_type': band, 'gain': currTestLog.get('Gain'),
                        'flatness': currTestLog.get('Flatness'), 'dsa3': currTestLog.get('DSA 3'),
                         'dsa2': currTestLog.get('DSA 2'), 'dsa1': currTestLog.get('DSA 1'),
                        'imod': currTestLog.get('IMod'), 'bit': currTestLog.get('BIT'),
                         'alcin': currTestLog.get('ALC in'), 'alcout': currTestLog.get('ALC out'),
                         'rloss': currTestLog.get('RLoss'), 'test_status': '', 'user': parent.currUser})
            conn.commit()

            q1 = "select id from test_results where sn = '%s' and dateTest = '%s' and band_type = '%s'" % \
                 (parent.rfbSN.text(), dateTest, band)
            q2 = "insert into flat_result (rfb, signal) values ((%s), '%s')" % (q1, currTestLog.get('Signal'))
            print(q2)
            cursor.execute(q2)
            conn.commit()

            if 'Ul1' in self.parent.to_DsaUlDl.keys() and band == 'Ul':
                q = "insert into dsa_results (rfb,dsa1,dsa2,dsa3) values ((select max(id) from test_results " \
                    "where band_type = 'Ul' and sn = '%s'),'%s','%s','%s')" % (parent.rfbSN.text(),
                                                                               self.parent.to_DsaUlDl.get('Ul1'),
                                                                               self.parent.to_DsaUlDl.get('Ul2'),
                                                                               self.parent.to_DsaUlDl.get('Ul3'))
                cursor.execute(q)
                conn.commit()
            if 'Dl1' in self.parent.to_DsaUlDl.keys() and band == 'Dl':
                q = "insert into dsa_results (rfb,dsa1,dsa2,dsa3) values ((select max(id) from test_results " \
                    "where band_type = 'Dl' and sn = '%s'),'%s','%s','%s')" % (parent.rfbSN.text(),
                                                                               self.parent.to_DsaUlDl.get('Dl1'),
                                                                               self.parent.to_DsaUlDl.get('Dl2'),
                                                                               self.parent.to_DsaUlDl.get('Dl3'))
                cursor.execute(q)
                conn.commit()
            self.testController.logSignal.emit('Writing test result complete', 0)

        except sqlite3.DatabaseError as err:
                self.parent.sendMsg('c', 'Querry error', str(err), 1)
                conn.close()
        else:
                conn.close()
                # report(parent,parent.rfbSN.text(),dateTest)




