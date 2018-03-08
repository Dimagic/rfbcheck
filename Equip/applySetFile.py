import csv
import os
import struct

import serial
from PyQt5 import QtCore
from Equip.equip import *


class applySetFile(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(str, int)
    msgSignal = QtCore.pyqtSignal(str, str, str, int)
    progressBarSignal = QtCore.pyqtSignal(str, float, float)
    comMovieSignal = QtCore.pyqtSignal(str, str)

    def __init__(self, currParent, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.ser = None
        self.currParent = currParent
        self.loadPref = 'aaaa5430'
        self.sizeData = {'CHAR8': 8, 'FLOAT32': 32, 'INT16': 16, 'RawData': 8,
                        'STRING_ARRAY': 16, 'UCHAR8': 8, 'UINT16': 16, 'ULONG32': 32}
        self.arrValue = {}
        for i, j in enumerate(range(33, 47)):
            i = i+1
            if i > 8:
                i = 2**(i-5)
            self.arrValue.update({i: str(hex(j)).replace('0x', '')})
        # print(self.arrValue)
        self.getComConn()
        self.readSetFile()

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
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            loadString = []
            for row in reader:
                if str(row.get(namePar)).find("#") != -1:
                    continue
                currData = row.get(None)[4:]
                typeOfData = row.get(None)[2]
                lenOfData = int(row.get(None)[3])
                addrToWrite = row.get(None)[0]
                memVal = self.getValOfMemory(lenOfData, self.sizeData.get(typeOfData))
                loadString = self.loadPref + str(memVal) + '556677' + addrToWrite.replace('0x', '')

                if row.get(namePar).find('HEX') != -1 \
                        or row.get(namePar) == 'FILTERS_NAMES':
                    continue

                for i in range(lenOfData):
                    currVal = currData[i]
                    if typeOfData == 'FLOAT32':
                        print(self.floatToHex(currVal))
                        continue
                    nbits = int(self.sizeData.get(typeOfData))
                    k = hex((int(currVal) + (1 << nbits)) % (1 << nbits))
                    k = self.getcorrectHex(k, nbits)
                    loadString += k
                needLen = int(self.getDictKey(self.arrValue, memVal)) + 8
                loadString = self.getCorrectLine(loadString, needLen)
                loadString = loadString + getCrc(loadString)
                # print(needLen)
                print(int(len(loadString)/2), loadString)
                # writingBytes = parent.ser.ser.write(binascii.unhexlify(loadString))
                print(binascii.unhexlify(loadString))
                self.ser.write(binascii.unhexlify(loadString))
                time.sleep(1)

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
        if '0.0' in n:
            return '0x00000000'
        try:
            return hex(struct.unpack('<I', struct.pack('<f', self.toFloat(n)))[0])
        except Exception as e:
            print(e)

    def getcorrectHex(self, line, k):
        line = line.replace('0x', '')
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
            print('ERR: converting string to float fail')
            return

    def getComConn(self):
        port, baud = 'COM1', '57600'
        try:
            self.ser = serial.Serial(port, int(baud), timeout=0.5)
            if self.ser.isOpen():
                self.ser.write(binascii.unhexlify('AAAA543022556677403D01'))
                rx = binascii.hexlify(self.ser.readline())
                self.comMovieSignal.emit(str(self.ser.port), str(self.ser.baudrate))
                self.logSignal.emit("Connected to port " + str(self.ser.port), 0)
        except Exception as e:
            self.logSignal.emit('Connection problem: ' + str(e), -1)
            self.comMovieSignal.emit('', '')
            self.sendMsg('c', 'Connection problem', 'Connection to\n'
                                                    'port: ' + port + '\n'
                                                    'baud: ' + baud + '\n'
                                                    'Fail: ' + str(e), 1)
