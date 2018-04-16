import time

import binascii
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

import Equip.commands as cmd
from Equip.equip import setAmplTo, getCrc, setAlc


class DetectorTest(QtCore.QThread):
    def __init__(self, testController, parent=None):
        super(DetectorTest, self).__init__(parent)
        testController.logSignal.emit("***** Start detector test *****", 0)
        self.testController = testController
        self.mainParent = testController.getParent()
        self.sa = testController.instr.sa
        self.gen = testController.instr.gen
        self.ser = testController.ser
        self.freqDl = self.mainParent.listSettings[1]
        self.freqUl = self.mainParent.listSettings[2]
        self.reqAddr = {'ulPowCal': '320D', 'ulRvsCal': '320E',
                        'dlPowCal': '3209', 'dlRvsCal': '320A',
                        'dlDet': '402A', 'ulDet': '402B'}
        self.prefToSend = 'AAAA543022556677'
        self.gen.write("POW:AMPL -60 dBm")
        self.sa.write("DISP:WIND:TRAC:Y:RLEV 50 dBm")

        if self.testController.whatConn == "Dl":
            self.forwardTest(self.freqDl)
            self.reversTest(self.freqDl)
        elif self.testController.whatConn == "Ul":
            self.forwardTest(self.freqUl)
            self.reversTest(self.freqUl)

    def preTest(self):
        self.ser.write(binascii.unhexlify(cmd.setSalcOpMode))
        for i in ['3244', '3245', '3246', '3247']:
            self.send('SetAlc', i + '00FF')

    def forwardTest(self, freq):
        self.preTest()
        haveFail = False
        arrDetector = []
        if self.testController.whatConn == "Dl":
            addrDet = 'dlDet'
            addrAnch = 'dlPowCal'
        else:
            addrDet = 'ulDet'
            addrAnch = 'ulPowCal'

        rx = self.send(addrAnch, self.reqAddr.get(addrAnch))
        anchor = int(rx[rx.find(self.reqAddr.get(addrAnch)) + 4: rx.find(self.reqAddr.get(addrAnch)) + 8], 16)
        anchorHex = rx[rx.find(self.reqAddr.get(addrAnch)) + 4: rx.find(self.reqAddr.get(addrAnch)) + 8]
        setAmplTo(self.ser, cmd, self.gen, anchor, self.testController)
        currPower = float(self.gen.query("POW:AMPL?"))
        oldDetector = 10000
        for i in range(-1, anchor):
            if self.testController.stopTestFlag:
                return
            self.gen.write("POW:AMPL " + str(currPower) + " dBm")
            time.sleep(1)
            rx = self.send(addrDet, self.reqAddr.get(addrDet))
            detector = int(rx[rx.find(self.reqAddr.get(addrDet)) + 8: rx.find(self.reqAddr.get(addrDet)) + 12], 16)
            arrDetector.append(rx[rx.find(self.reqAddr.get(addrDet)) + 8: rx.find(self.reqAddr.get(addrDet)) + 12])
            delta = oldDetector - detector
            oldDetector = detector
            if delta <= 3:
                status = -1
                haveFail = True
            else:
                status = 0
            self.testController.logSignal.emit("Anch. forw.: " + str(anchor) +
                                               ": Det.: " + str(detector) +
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
        # self.send('SetDet', toSend)

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
        self.preTest()
        haveFail = False
        if self.testController.whatConn == "Dl":
            addrDet = 'dlDet'
            addrAnch = 'dlRvsCal'
        else:
            addrDet = 'ulDet'
            addrAnch = 'ulRvsCal'

        rx = self.send(addrAnch, self.reqAddr.get(addrAnch))
        anchor = int(rx[rx.find(self.reqAddr.get(addrAnch)) + 4: rx.find(self.reqAddr.get(addrAnch)) + 8], 16)
        setAmplTo(self.ser, cmd, self.gen, anchor, self.testController)
        currPower = float(self.gen.query("POW:AMPL?"))
        self.testController.sendMsg('i', 'RFBCheck', 'Disconnect signal analyzer cable and press Ok', 1)
        oldDetector = 10000
        for i in range(-1, anchor):
            if self.testController.stopTestFlag:
                return
            self.gen.write("POW:AMPL " + str(currPower) + " dBm")
            time.sleep(1)
            rx = self.send(addrDet, self.reqAddr.get(addrDet))
            detector = int(rx[rx.find(self.reqAddr.get(addrDet)) + 12: rx.find(self.reqAddr.get(addrDet)) + 16], 16)
            delta = oldDetector - detector
            oldDetector = detector
            if delta <= 3:
                status = -1
                haveFail = True
            else:
                status = 0
            self.testController.logSignal.emit("Anch. rev.: " + str(anchor) +
                                               ": Det.: " + str(detector) +
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

    def send(self, param, addr):
        self.ser.flushInput()
        self.ser.flushOutput()
        namePar = param
        if param == 'SetAlc':
            toSend = 'AAAA543024556677' + addr
        elif param == 'SetDet':
            toSend = 'AAAA54302D556677' + addr
        else:
            toSend = self.prefToSend + addr
        crc = getCrc(toSend)
        toSend += crc
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
