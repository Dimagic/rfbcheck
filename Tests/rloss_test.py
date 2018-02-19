import time
from PyQt5 import QtCore


class ReturnLossTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(ReturnLossTest, self).__init__(parent)
        testController.logSignal.emit("***** Start return loss test *****", 3)

        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.na
        self.returnLossTest()

    def returnLossTest(self):
        return
        center = 766.5
        start = 758
        end = 775

        self.na.write(":SENS1:FREQ:%s 806E6") % center
        self.na.write(":SENS1:FREQ:%s 36E6") % (end - start)
        self.na.write(":CALC1:PAR1:DEF S12")
        self.na.write(":CALC1:MARK1 ON")
        time.sleep(3)
        arr = []
        for i in range(start, end):
            self.na.write(":CALC1:MARK1:X " + str(i) + 'E6')
            gain = self.na.query(":CALC1:MARK1:Y?")
            arr.append(gain)
