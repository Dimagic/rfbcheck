from PyQt5 import QtCore
from Equip.writeTestResult import WriteResult
from Tests.gain_test import GainTest
from Tests.flatness_test import FlatnessTest
from Tests.dsa_test import DsaTest
from Tests.intermod_test import IModTest
from Tests.bitAlarm_test import BitAlarmTest
from Tests.alc_test import AlcTest

from Equip.equip import *
from Equip.connCom import *
from Equip.instrument import *

import Equip.commands as cmd

class TestContoller(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(str,int)
    resSignal = QtCore.pyqtSignal(str,str,str,str,str,int)
    conSignal = QtCore.pyqtSignal()
    msgSignal = QtCore.pyqtSignal(str,str,str,int)
    dsaResSignal = QtCore.pyqtSignal(float,float)
    progressBarSignal = QtCore.pyqtSignal(str,float,float)



    def __init__(self, currParent, parent=None):
        QtCore.QThread.__init__(self,parent)

        self.currParent = currParent          #main program
        self.testArr = []                   #checked tests

        self.ser          = None            #Com port connection
        self.instr        = None            #instruments
        self.whatConn     = None            #Ul/Dl
        self.to_DsaUlDl   = {}              #results DSA test from DB
        self.to_DsaResult = {}              #temporary results DSA test
        self.testLogDl    = {}
        self.testLogUl    = {}
        self.stopTestFlag = False

        if currParent.testLogDl.get('SN') != currParent.rfbSN.text() :
            currParent.testLogDl = {}
        if currParent.testLogUl.get('SN') != currParent.rfbSN.text():
            currParent.testLogUl = {}
        self.getTests(currParent)
        if len(self.testArr) == 0:
                self.msgSignal.emit('w',"Warning","You have to choice minimum one test",1)
                return



    def run(self):
        self.ser = self.getComConn()
        print(self.ser)
        self.whatConn = self.checkUlDl(self.ser)
        if self.whatConn == None: return
        self.logSignal.emit('START TEST',0)
        self.instr.gen.write(":OUTP:STAT ON")

        self.currParent.stopTestFlag = False



        self.runTests()

        self.ser.ser.close()
        self.instr.gen.write(":OUTP:STAT OFF")
        self.currParent.startTestBtn.setText("Start")

        self.writeResults()

    def runTests(self):
        if self.currParent.checkGainTest.isChecked() == True:
            if self.currParent.stopTestFlag == True: return
            GainTest(self, self.currParent)

        if self.currParent.checkGainTest.isChecked() == True:
            if self.currParent.stopTestFlag == True: return
            FlatnessTest(self, self.currParent)

        return #!!!!!!! RETURN

        if self.currParent.checkDsaTest.isChecked() == True:
            if self.currParent.stopTestFlag == True: return
            DsaTest(self, self.currParent)

        if self.currParent.checkImTest.isChecked() == True:
            if self.currParent.stopTestFlag == True: return
            if self.currParent.whatConn == 'Dl':
                freq = self.currParent.listSettings[1]
            elif self.currParent.whatConn == 'Ul':
                freq = self.currParent.listSettings[2]
            IModTest(self,self.currParent,freq)

        if self.currParent.checkBitAlarmTest.isChecked() == True:
            if self.currParent.stopTestFlag == True: return
            BitAlarmTest(self, self.currParent)

        if self.currParent.checkAlcTest.isChecked() == True:
            if self.currParent.stopTestFlag == True: return
            AlcTest(self, self.currParent)


    def getTests(self,currParent):
        if currParent.checkGainTest.isChecked() == True:
            self.testArr.append('Gain test')
        if currParent.checkGainTest.isChecked() == True:
            self.testArr.append('Flatness test')
        if currParent.checkDsaTest.isChecked() == True:
            self.testArr.append('DSA test')
        if currParent.checkImTest.isChecked() == True:
            self.testArr.append('IM test')
        if currParent.checkBitAlarmTest.isChecked() == True:
            self.testArr.append('Alarm test')
        if currParent.checkAlcTest.isChecked() == True:
            self.testArr.append('AlcTest')

    def getComConn(self):
        self.ser = connCom()
        if self.ser.ser.isOpen() == True:
            try:
                self.ser.ser.write(binascii.unhexlify('AAAA543022556677403D01'))
                rx = binascii.hexlify(self.ser.ser.readline())
                band = int(rx[26:34],16)/1000
                return(self.ser)
##                self.currParent.portLbl.setText(self.ser.ser.port)
##                self.currParent.baudLbl.setText(str(self.ser.ser.baudrate))
                self.logSignal.emit("Connected to port "+ str(self.ser.ser.port),0)
            except Exception as e:
                self.ser.ser.close()
                self.currParent.sendMsg('w','Warning','Connection problem',1)
                return

    def getParrent(self):
        return(self.currParent)

    def getSqlConn(self):
        pass

    def checkUlDl(self, ser):
        self.ser.ser.write(binascii.unhexlify(cmd.setSalcOpMode))
        self.ser.ser.write(binascii.unhexlify(cmd.reset))
        setAlc(self.ser, cmd.setAlcInDl, 255, cmd.shiftDlIn)
        setAlc(self.ser, cmd.setAlcInUl, 255, cmd.shiftUlIn)
        setAlc(self.ser, cmd.setAlcInDl, 255, cmd.shiftDlOut)
        setAlc(self.ser, cmd.setAlcInUl, 255, cmd.shiftUlOut)

        setDSA(self.ser, cmd, 'Dl', self.currParent.listSettings[5], self.currParent.listSettings[6], self.currParent.listSettings[7])
        setDSA(self.ser, cmd, 'Ul', self.currParent.listSettings[8], self.currParent.listSettings[9], self.currParent.listSettings[10])

        self.whatConn = None
        Dl = self.currParent.listSettings[1]
        Ul = self.currParent.listSettings[2]

        for i in [Dl,Ul]:
            self.progressBarSignal.emit('Check connection',0,0)
            if i == 0: continue
            try:
                self.instr = Instrument(i,self.currParent)#ToDo if return None!!!!!
            except Exception as e:
                self.currParent.sendMsg('c','Instrumet initialization error',str(e),1)
            self.instr.gen.write(":OUTP:STAT ON")
            time.sleep(3)
            if float(getAvgGain(self)) > -50:
                if i == Dl:
                    self.logSignal.emit("Testing DownLink",0)
                    self.testLogDl.update({'SN':self.currParent.rfbSN.text()})
                    self.whatConn = "Dl"
                    break
                elif i == Ul:
                    self.logSignal.emit("Testing UpLink",0)
                    self.testLogUl.update({'SN':self.currParent.rfbSN.text()})
                    self.whatConn = "Ul"
        if self.whatConn == None:
            self.logSignal.emit("No signal",2)
            self.whatConn = None
            return
        self.instr.gen.write(":OUTP:STAT OFF")
        time.sleep(1)
        return(self.whatConn)

    def writeResults(self):
        dlMustToBe = ulMustToBe = dlPresent = ulPresent = False
        if self.currParent.atrSettings.get('freq_band_dl_1').find('@') != -1 or self.currParent.atrSettings.get('freq_band_dl_2').find('@') != -1:
            dlMustToBe = True
        if self.currParent.atrSettings.get('freq_band_ul_1').find('@') != -1 or self.currParent.atrSettings.get('freq_band_ul_2').find('@') != -1:
            ulMustToBe = True
        if dlMustToBe == True and len(self.currParent.testLogDl) > 0:
                dlPresent = True
        if ulMustToBe == True and len(self.currParent.testLogUl) > 0:
                ulPresent = True
        if self.currParent.rfbSN.text().upper() != 'XXXX':
            if dlMustToBe == dlPresent and ulMustToBe == ulPresent:
                WriteResult(self.currParent,self.currParent.testLogDl,self.currParent.testLogUl)
                self.msgSignal.emit('i','RFBcheck','Test comlite',1)








