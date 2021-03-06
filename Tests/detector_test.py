import time
import binascii
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
import Equip.commands as cmd
from Equip.config import Config
from Equip.equip import setAmplTo, getCrc


class DetectorTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(DetectorTest, self).__init__(parent)
        testController.logSignal.emit("***** Start detector test *****", 0)
        self.config = Config()
        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.ser = testController.ser
        self.frwDetArr = []
        self.revDetArr = []
        self.tmpFrwDetArr = []
        self.tmpRevDetArr = []
        self.freqDl = self.mainParent.listSettings[1]
        self.freqUl = self.mainParent.listSettings[2]
        self.reqAddr = {'ulPowCal': '320D', 'ulRvsCal': '320E',
                        'dlPowCal': '3209', 'dlRvsCal': '320A',
                        'dlDet': '402A', 'ulDet': '402B'}
        self.prefToSend = 'AAAA543022556677'
        self.gen.write("POW:AMPL -60 dBm")
        self.sa.write("DISP:WIND:TRAC:Y:RLEV 50 dBm")

        if not self.getPampCurrent():
            self.testController.sendMsg('i', 'RFBCheck', self.testController.whatConn + ' PAMP Current fail', 1)
            return

        if self.testController.whatConn == "Dl":
            if 'Forw. detector' in self.testController.testArr:
                self.forwardTest(self.freqDl)
            if 'Rev. detector' in self.testController.testArr:
                self.reversTest(self.freqDl)
        elif self.testController.whatConn == "Ul":
            if 'Forw. detector' in self.testController.testArr:
                self.forwardTest(self.freqUl)
            if 'Rev. detector' in self.testController.testArr:
                self.reversTest(self.freqUl)
        self.writeDataToAdem()

    def preTest(self):
        self.ser.write(binascii.unhexlify(cmd.setSalcOpMode))
        for i in ['3244', '3245', '3246', '3247']:
            self.send('SetAlc', i + '00FF', None)

    def getPampCurrent(self):
        currLimits = {'dlPampCurrent': '3262', 'ulPampCurrent': '3263'}
        for i in currLimits.keys():
            if self.testController.whatConn.upper() not in i.upper():
                continue
            addr = currLimits.get(i)
            rx = self.send(i, addr, None)
            current = int(rx[rx.find(addr) + len(addr): len(rx) - 2], 16)
            limAddr = str(int(addr) + 10)
            rx = self.send(i, limAddr, None)
            hexStr = rx[rx.find(limAddr) + len(limAddr): (len(rx) - 2)]
            minLimit = int(hexStr[:4], 16)
            maxLimit = int(hexStr[5:], 16)
            if minLimit <= current <= maxLimit:
                self.testController.logSignal.emit(self.testController.whatConn +
                                                   ' PAMP Current = ' + str(current) + ' :PASS', 1)
                return True
            else:
                self.testController.logSignal.emit(self.testController.whatConn +
                                                   ' PAMP Current = ' + str(current) + ' :FAIL', -1)
                return False

    def forwardTest(self, freq):
        self.frwDetArr.clear()
        self.preTest()
        haveFail = False
        self.setNaOffset(freq)
        arrDetector = []
        if self.testController.whatConn == "Dl":
            addrDet = 'dlDet'
            addrAnch = 'dlPowCal'
        else:
            addrDet = 'ulDet'
            addrAnch = 'ulPowCal'

        rx = self.send(addrAnch, self.reqAddr.get(addrAnch), None)
        anchorHex = rx[rx.find(self.reqAddr.get(addrAnch)) + 4: rx.find(self.reqAddr.get(addrAnch)) + 8]
        anchor = int(anchorHex, 16)
        self.tmpFrwDetArr.append(anchor)
        self.tmpFrwDetArr.append(0)

        setAmplTo(self.ser, cmd, self.gen, anchor, self.testController)
        currPower = float(self.gen.query("POW:AMPL?"))
        oldDetector = 10000
        for i in range(-1, anchor):
            if self.testController.stopTestFlag:
                return
            self.gen.write("POW:AMPL " + str(currPower) + " dBm")
            time.sleep(1)
            rx = self.send(addrDet, self.reqAddr.get(addrDet), None)
            detector = int(rx[rx.find(self.reqAddr.get(addrDet)) + 8: rx.find(self.reqAddr.get(addrDet)) + 12], 16)
            self.frwDetArr.append(detector)
            arrDetector.append(rx[rx.find(self.reqAddr.get(addrDet)) + 8: rx.find(self.reqAddr.get(addrDet)) + 12])
            delta = oldDetector - detector
            oldDetector = detector
            if delta < int(self.config.getConfAttr('limits', 'fwr_pwr_detector')):
                status = -1
                haveFail = True
            else:
                status = 0
            self.testController.logSignal.emit("Pout forw. " + self.testController.whatConn + ": " + str(anchor) +
                                               ": Detector: " + str(detector) +
                                               " Delta: " + str(delta) + "", status)
            currPower -= 1
            anchor -= 1
            self.testController.progressBarSignal.emit("Forward detector test", anchor - 1, i)
        while len(arrDetector) < 64:
            arrDetector.append('0000')
        arrDetector.reverse()

        detToSend = ''
        for i in arrDetector:
            detToSend += i
        addrToSend = str(hex(int(self.reqAddr.get(addrAnch), 16) - 8))[2:]
        toSend = addrToSend + anchorHex + '0000' + detToSend
        while len(toSend) < 528:
            toSend += '0'
        #     write detector calibration
        # self.send('SetDet', toSend, None)

        if haveFail:
            q = self.testController.sendMsg('i', 'RFBCheck', 'Forward detector test fail', 3)
            if q == QMessageBox.Retry:
                self.forwardTest(self.freqDl)
                return
            elif q == QMessageBox.Ignore:
                self.testController.resSignal.emit('Forw. detector', self.testController.whatConn, '', 'Fail', '', -1)
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
        else:
            self.testController.resSignal.emit('Forw. detector', self.testController.whatConn, '', 'Pass', '', 1)

    def reversTest(self, freq):
        self.revDetArr.clear()
        self.preTest()
        haveFail = False
        self.setNaOffset(freq)
        if self.testController.whatConn == "Dl":
            addrDet = 'dlDet'
            addrAnch = 'dlRvsCal'
        else:
            addrDet = 'ulDet'
            addrAnch = 'ulRvsCal'

        rx = self.send(addrAnch, self.reqAddr.get(addrAnch), None)
        anchorHex = rx[rx.find(self.reqAddr.get(addrAnch)) + 4: rx.find(self.reqAddr.get(addrAnch)) + 8]
        anchor = int(anchorHex, 16)
        self.tmpRevDetArr.append(anchor)
        self.tmpRevDetArr.append(0)

        setAmplTo(self.ser, cmd, self.gen, anchor, self.testController)
        currPower = float(self.gen.query("POW:AMPL?"))
        self.testController.sendMsg('i', 'RFBCheck', 'Disconnect signal analyzer cable and press Ok', 1)
        oldDetector = 10000
        for i in range(-1, anchor):
            if self.testController.stopTestFlag:
                return
            self.gen.write("POW:AMPL " + str(currPower) + " dBm")
            time.sleep(1)
            rx = self.send(addrDet, self.reqAddr.get(addrDet), None)
            detector = int(rx[rx.find(self.reqAddr.get(addrDet)) + 12: rx.find(self.reqAddr.get(addrDet)) + 16], 16)
            self.revDetArr.append(detector)
            delta = oldDetector - detector
            oldDetector = detector
            if delta < int(self.config.getConfAttr('limits', 'rvs_pwr_detector')):
                status = -1
                haveFail = True
            else:
                status = 0
            self.testController.logSignal.emit("Pout rev. " + self.testController.whatConn + ": " + str(anchor) +
                                               ": Detector: " + str(detector) +
                                               " Delta: " + str(delta) + "", status)
            currPower -= 1
            anchor -= 1
            self.testController.progressBarSignal.emit("Reverse detector test", anchor - 1, i)
        if haveFail:
            q = self.testController.sendMsg('i', 'RFBCheck', 'Reverse detector test fail', 3)
            if q == QMessageBox.Retry:
                self.testController.sendMsg('i', 'RFBCheck', 'Reconnect signal analyzer cable and press Ok', 1)
                self.reversTest(self.freqUl)
                return
            elif q == QMessageBox.Ignore:
                self.testController.resSignal.emit('Rev. detector', self.testController.whatConn, '', 'Fail', '', -1)
            elif q == QMessageBox.Cancel:
                self.testController.stopTestFlag = True
        else:
            self.testController.resSignal.emit('Rev. detector', self.testController.whatConn, '', 'Pass', '', 1)

    def send(self, param, addr, addr2):
        self.ser.flushInput()
        self.ser.flushOutput()
        namePar = param
        # if addr2 is not None:
        #     toSend = 'AAAA54%s556677%s' % addr2, addr
        #     return
        if param == 'SetAlc':
            toSend = 'AAAA543024556677' + addr
        elif param == 'SetDet':
            toSend = 'AAAA54302D556677' + addr
        else:
            toSend = self.prefToSend + addr
        crc = getCrc(toSend)
        toSend += crc
        print(toSend)
        writingBytes = self.ser.write(binascii.unhexlify(toSend))
        outWait = int(self.ser.outWaiting())
        inWait = int(self.ser.inWaiting())

        k = 0
        while outWait != 0:
            if k > 15:
                print(namePar + ':OUT ERROR')
                print('--------------------------')
                return False
            else:
                time.sleep(0.5)
                outWait = int(self.ser.outWaiting())
                k += 1
        k = 0
        while inWait == 0:
            if k > 15:
                print(namePar + ':IN ERROR', -1)
                print('--------------------------')
                return False
            else:
                time.sleep(0.5)
                inWait = int(self.ser.inWaiting())
                k += 1

        rx = str(binascii.hexlify(self.ser.read(self.ser.inWaiting()))).replace("b'", "").replace("'", "").upper()
        if addr in rx:
            print(namePar)
            print('Tx: ' + str(toSend)[:95].upper())
            print('written ' + str(writingBytes) + ' bytes')
            print('Rx: ' + str(rx))
            print(namePar + ': OK')
            print('--------------------------')
            return rx

    def setNaOffset(self, freq):
        conn, cursor = self.mainParent.getConnDb()
        rows = cursor.execute("select delta from calSaToGen where freq = :n", {'n': freq}).fetchone()
        conn.close()
        self.sa.write("DISP:WIND:TRAC:Y:RLEV:OFFS " +
                      str(int(self.mainParent.saAtten.text()) + abs(float(rows[0]))))

    def writeDataToAdem(self):
        if self.testController.sendMsg('i', 'RFBCheck', 'Save detector data?', 2) == QMessageBox.Cancel:
            return
        lenDet = 64
        self.frwDetArr = self.frwDetArr + self.tmpFrwDetArr[::-1]
        self.revDetArr = self.revDetArr + self.tmpRevDetArr[::-1]
        for j, i in enumerate([self.frwDetArr, self.revDetArr]):
            if len(i) == 0:
                continue
            for row, data in enumerate(i):
                k = str(hex(i[row])).replace("0x", "")
                while len(k) < 4:
                    k = '0' + k
                i[row] = k
            i = i[::-1]
            while len(i) < lenDet:
                i.insert(2, '0000')
            strToSend = ''
            for row in i:
                strToSend += row
            if self.testController.whatConn == 'Dl':
                listAdr = ['3201', '3202']
            else:
                listAdr = ['3205', '3206']
            self.send('SetDet', listAdr[j], None)



