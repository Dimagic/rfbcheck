import Equip.commands as cmd
from Equip.equip import *
import time
import csv
import os
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore


class BitAlarmTest(QtCore.QThread):
    def __init__(self, testController, mainParent, parent=None):
        super(BitAlarmTest, self).__init__(parent)
        testController.logSignal.emit("***** Start BIT alarm test *****", 3)
        testController.progressBarSignal.emit('BIT Alarm', 0, 0)

        if mainParent.stopTestFlag == True:
            return
        self.testController = testController
        self.parent = mainParent
        self.ser = mainParent.ser.ser
        self.arrAlarms = None
        self.alarms = None

        self.test()

    def test(self):
        currentGain = float(self.parent.instr.sendQerySa("CALC:MARK:Y?"))
        print(currentGain)
        if currentGain >= -50:
            gain = True
        else:
            self.testController.logSignal.emit('No signal', 2)
            return

        self.testController.logSignal.emit('Send IF 1.2 GHz', 0)
        self.sendIfFreq(12000000)
        time.sleep(3)

        self.getAlarms()
        wasAlarm = False
        if cmd.alarmName[1] and cmd.alarmName[7] in self.alarms:
            wasAlarm = True

        n = float(self.parent.instr.sendQerySa("CALC:MARK:Y?"))
        self.testController.logSignal.emit('BIT gain: ' + str(n), 1)
        if n < -10:  # TODO: ??????
            gain = False

        self.testController.logSignal.emit('Send IF 0 GHz', 0)
        self.sendIfFreq(0)
        time.sleep(2)
        self.getAlarms()

        if not gain and wasAlarm:
            self.testController.logSignal.emit('BIT alarm PASS', 1)
            self.testController.resSignal.emit('BIT', self.parent.whatConn, '', 'Pass', '', 1)
            status = 'Pass'
        else:
            q = self.parent.sendMsg('w', 'Warning', 'BIT alarm test fail', 3)
            if q == QMessageBox.Retry:
                self.test()
            elif q == QMessageBox.Cancel:
                self.parent.stopTestFlag = True
            self.testController.logSignal.emit('BIT alarm FAIL', 2)
            self.testController.resSignal.emit('BIT', self.parent.whatConn, '', 'Fail', '', 0)
            status = 'Fail'

        if self.parent.whatConn == 'Dl':
            self.parent.testLogDl.update({'BIT': status})
        else:
            self.parent.testLogUl.update({'BIT': status})

    def getHexAddr(self):
        pref = 'AAAA543022556677'

    def getAlarms(self):
        self.ser.flushInput()
        self.ser.flushOutput()
        toSend = 'AAAA5430225566773220D6'  # GetAlarm
        self.ser.write(binascii.unhexlify(toSend))
        rx = binascii.hexlify(self.ser.readline())
        n = str(rx).find('3220') + 4
        request = str(rx)[n:n + 4]
        k = 0
        for i in request:
            if i == '0':
                k += 1
            else:
                request = request[k:]
                break
        print(str(rx)[n:n + 4])
        print(request)
        strAlarms = bin(int(request, 16))[2:]
        # binary = lambda x: " ".join(reversed( [i+j for i,j in zip( *[ ["{0:04b}".format(int(c,16)) for c in reversed("0"+x)][n::2] for n in [1,0] ] ) ] ))
        # strAlarms = binascii.hexlify(rx[n:n+4])
        print(strAlarms)
        ##        if len(strAlarms) < 16:
        ##            for i,j in enumerate(strAlarms):
        ##                if j == '1':
        ##                    n = i
        ##            strAlarms = strAlarms[:n+1]
        # strAlarms = bin(int(rx[26:30],16))
        print(str(rx))
        ##        print(str(rx).find('3220'))
        print(strAlarms)

        self.arrAlarms = strAlarms.zfill(16)
        self.arrAlarms = self.arrAlarms[::-1]
        print(self.arrAlarms)
        n = 0
        self.alarms = 'Alarms: '
        for i in self.arrAlarms:
            if i == '1':
                self.alarms = self.alarms + cmd.alarmName[n] + '; '
            n += 1
        self.parent.sendLog(self.alarms, 0)

    def sendIfFreq(self, freq):
        loDl, loUl = self.getLoFreq()
        if self.parent.whatConn == 'Dl':
            pref = 'AAAA5430295566775200'
            freqLo = loDl
        elif self.parent.whatConn == 'Ul':
            pref = 'AAAA5430295566775202'
            freqLo = loUl
        freqHex = hex(int(freq)).replace('0x', '')
        while len(freqHex) < 8:
            freqHex = '0' + freqHex
        toSend = pref + freqLo + freqHex
        crc = getCrc(toSend)
        toSend = toSend + '000000000000' + crc
        self.ser.write(binascii.unhexlify(toSend))

    def getLoFreq(self):
        try:
            file = os.path.join(os.path.dirname(__file__), '..', 'setFiles',
                                self.parent.rfbTypeCombo.currentText() + '.CSV')
            f = open(file, 'r')
            f.close()
        except Exception as e:
            self.testController.msgSignal.emit('w', 'Cont open file settings', str(e), 1)
            return
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                arr = row.get(None)
                if type(arr) != list: continue
                if row['# 0 1182685875'] == 'PATH_A_RF_PLL':
                    loDl = ''
                    for i in range(4, 8, 1):
                        loDl += hex(int(arr[i])).replace('0x', '')
                    while len(loDl) < 8:
                        loDl = '0' + loDl
                if row['# 0 1182685875'] == 'PATH_B_RF_PLL':
                    loUl = ''
                    for i in range(4, 8, 1):
                        loUl += hex(int(arr[i])).replace('0x', '')
                    while len(loUl) < 8:
                        loUl = '0' + loUl
            return (loDl, loUl)

##    def getLoFreq(self,addr):
##        self.ser.flushInput()
##        self.ser.flushOutput()
##        pref1 = 'AAAA54'
##        pref2 = '3022556677'
##        crc = getCrc(pref2 + addr)
##        toSend = pref1 + pref2 + addr + crc
##        print(toSend)
##        self.ser.write(binascii.unhexlify(toSend))
##        rx = str(binascii.hexlify(self.ser.readline()))
##        print(rx)
##        n = rx.find(addr) + len(addr)
##        rx = '0x' + rx[n:n+8]
##        print(rx)
##        print(int(rx,16))
##        return(int(rx,16))
