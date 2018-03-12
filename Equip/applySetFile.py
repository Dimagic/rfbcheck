import codecs
import csv
import os
import serial
from PyQt5 import QtCore
from Equip.equip import *
from Equip.selectComPort import SelectComPort


class ApplySetFile(QtCore.QThread, SelectComPort):
    logSignal = QtCore.pyqtSignal(str, int)
    msgSignal = QtCore.pyqtSignal(str, str, str, int)
    progressBarSignal = QtCore.pyqtSignal(str, float, float)
    comMovieSignal = QtCore.pyqtSignal(str, str)

    def __init__(self, currParent, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.ser = None
        self.haveConn = False
        self.currParent = currParent
        self.loadPref = 'aaaa5430'
        self.sizeData = {'CHAR8': 8, 'FLOAT32': 32, 'INT16': 16, 'RawData': 8,
                        'STRING_ARRAY': 128, 'UCHAR8': 8, 'UINT16': 16, 'ULONG32': 32}
        self.arrValue = {}
        for i, j in enumerate(range(33, 47)):
            i = i+1
            if i > 8:
                i = 2**(i-5)
            self.arrValue.update({i: str(hex(j)).replace('0x', '')})

    def run(self):
        self.getComConn()
        if self.haveConn:
            self.readSetFile()
            # self.getParameter()

    def readSetFile(self):
        namePar = '# 0 1182685875'
        try:
            file = os.path.join(os.path.dirname(__file__), '..', 'setFiles',
                                self.currParent.rfbTypeCombo.currentText() + '.CSV')
            f = open(file, 'r')
            f.close()
        except Exception as e:
            self.msgSignal.emit('w', 'Can`t open file settings', str(e), 1)
            return

        csvfile = open(file)
        reader = csv.DictReader(csvfile)
        row_count = sum(1 for row in reader) - 1
        csvfile.close()

        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for l, row in enumerate(reader):
                self.progressBarSignal.emit('Loading set file', row_count, l)
                if str(row.get(namePar)).find("#") != -1:
                    continue
                currData = row.get(None)[4:]
                typeOfData = row.get(None)[2]
                lenOfData = int(row.get(None)[3])
                addrToWrite = row.get(None)[0]
                memVal = self.getValOfMemory(lenOfData, self.sizeData.get(typeOfData))
                toSend = self.loadPref + str(memVal) + '556677' + addrToWrite.replace('0x', '')
                for x, i in enumerate(range(lenOfData)):
                    currVal = currData[i]
                    if row.get(namePar) != 'FILTERS_NAMES':
                        nbits = int(self.sizeData.get(typeOfData))

                    if typeOfData == 'FLOAT32':
                        k = self.floatToHex(currVal)
                    elif row.get(namePar) == 'FILTERS_NAMES':
                        if x == 0:
                            nbits = int(currVal) * 8
                            continue
                        k = binascii.hexlify(codecs.encode(currVal))
                    else:
                        k = hex((int(currVal) + (1 << nbits)) % (1 << nbits))
                    k = self.getcorrectHex(k, nbits)
                    toSend += k
                needLen = int(self.getDictKey(self.arrValue, memVal)) + 8
                toSend = self.getCorrectLine(toSend, needLen)
                toSend += getCrc(toSend)
                self.setParameter(row.get(namePar), addrToWrite.replace('0x', ''), toSend)

        csvfile.close()
        self.ser.close()
        self.comMovieSignal.emit('', '')
        self.logSignal.emit('Load settings file complete', 0)

    def getDictKey(self, dict, val):
        for i, j in dict.items():
            if j == val:
                return int(i)

    def getValOfMemory(self, n, s):
        arrKeys = sorted(self.arrValue.keys())
        for i in arrKeys:
            if i >= int(n*s/8+2):
                return self.arrValue.get(i)

    def tohex(self, val, nbits):
        return self.getcorrectHex(hex((val + (1 << nbits)) % (1 << nbits)), nbits / 4)

    def floatToHex(self, n):
        if n == 0:
            return '0x00000000'
        try:
            return hex(struct.unpack('<I', struct.pack('<f', self.toFloat(n)))[0])
        except Exception as e:
            self.logSignal.emit(str(e), -1)

    def getcorrectHex(self, line, k):
        line = str(line).replace('0x', '').replace("b'", "").replace("'", "")
        if len(line) % 2 != 0:
            line = '0' + line
        while len(line) < k/4:
            line = '0' + line
        return line

    def getCorrectLine(self, line, l):
        if len(line) % 2 != 0:
            line = '0' + line
        while len(line)/2 != l:
            line = line + '0'
        return line

    def toFloat(self, n):
        try:
            return float(n)
        except ValueError:
            self.logSignal.emit('ERR: converting string to float fail', -1)
            return

    def getComConn(self):
        port, baud = self.getCurrPortBaud()
        try:
            self.ser = serial.Serial(port, int(baud), timeout=0.5)
            if self.ser.isOpen():
                self.ser.write(binascii.unhexlify('AAAA543022556677403D01'))
                time.sleep(.5)
                tx = binascii.hexlify(self.ser.readline())
                if tx == b'':
                    raise serial.portNotOpenError
                self.comMovieSignal.emit(str(self.ser.port), str(self.ser.baudrate))
                self.logSignal.emit("Connected to port " + str(self.ser.port), 0)
                self.haveConn = True
        except Exception as e:
            self.haveConn = False
            self.logSignal.emit('Connection problem: ' + str(e), -1)
            self.comMovieSignal.emit('', '')
            self.msgSignal.emit('c', 'Connection problem', 'Connection to\n'
                                                    'port: ' + port + '\n'
                                                    'baud: ' + baud + '\n'
                                                    'Fail: ' + str(e), 1)
            if self.ser is not None:
                if self.ser.isOpen():
                    self.ser.close()

    def setParameter(self, namePar, addr, toSend):
        self.ser.flushInput()
        self.ser.flushOutput()

        writingBytes = self.ser.write(binascii.unhexlify(toSend))
        outWait = int(self.ser.outWaiting())
        inWait = int(self.ser.inWaiting())

        k = 0
        while outWait != 0:
            if k > 15:
                self.logSignal.emit(namePar + ':OUT ERROR', -1)
                print('--------------------------', 0)
                return False
            else:
                time.sleep(0.5)
                outWait = int(self.ser.outWaiting())
                k += 1
        k = 0
        while inWait == 0:
            if k > 5:
                self.logSignal.emit(namePar + ':IN ERROR', -1)
                self.logSignal.emit('--------------------------', 0)
                return False
            else:
                time.sleep(0.5)
                inWait = int(self.ser.inWaiting())
                k += 1

        rx = str(binascii.hexlify(self.ser.read(self.ser.inWaiting()))).replace("b'", "").replace("'", "").upper()
        if addr in rx:
            self.logSignal.emit(namePar, 0)
            self.logSignal.emit('Tx: ' + str(toSend)[:95].upper(), 0)
            self.logSignal.emit('written ' + str(writingBytes) + ' bytes', 0)
            self.logSignal.emit('Rx: ' + str(rx), 0)
            self.logSignal.emit(namePar + ': OK', 1)
            self.logSignal.emit('--------------------------', 0)
            return True

    def getParameter(self):
        namePar = '# 0 1182685875'
        try:
            file = os.path.join(os.path.dirname(__file__), '..', 'setFiles',
                                self.currParent.rfbTypeCombo.currentText() + '.CSV')
            f = open(file, 'r')
            f.close()
        except Exception as e:
            self.msgSignal.emit('w', 'Can`t open file settings', str(e), 1)
            return

        csvfile = open(file)
        reader = csv.DictReader(csvfile)
        row_count = sum(1 for row in reader) - 1
        csvfile.close()

        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if str(row.get(namePar)).find("#") != -1:
                    continue
                addr = str(hex(int(row.get(None)[0], 16) + 1)).replace("0x", "")

                self.ser.flushInput()
                self.ser.flushOutput()

                outWait = int(self.ser.outWaiting())
                inWait = int(self.ser.inWaiting())

                toSend = 'AAAA543022556677'
                toSend += addr
                crc = getCrc(toSend)
                toSend += crc
                print(toSend)
                # print(binascii.unhexlify(toSend))
                self.ser.write(binascii.unhexlify(toSend))
                k = 0
                while outWait != 0:
                    if k > 15:
                        self.logSignal.emit(':OUT ERROR', -1)
                        print('--------------------------', 0)
                        return False
                    else:
                        time.sleep(0.5)
                        outWait = int(self.ser.outWaiting())
                        k += 1
                k = 0
                while inWait == 0:
                    if k > 5:
                        self.logSignal.emit(':IN ERROR', -1)
                        self.logSignal.emit('--------------------------', 0)
                        return False
                    else:
                        time.sleep(0.5)
                        inWait = int(self.ser.inWaiting())
                        k += 1

                rx = str(binascii.hexlify(self.ser.read(self.ser.inWaiting()))).replace("b'", "").replace("'", "").upper()
                print(rx)
                print('--------------------------')

