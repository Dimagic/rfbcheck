from threading import Thread
from Tests.gainFlatness_test import *
from Tests.dsa_test import *
from Tests.intermod_test import *
from Tests.bitAlarm_test import *
from Tests.alc_test import *
from Equip.writeTestResult import *
import threading



class testContoller(threading.Thread):
    def __init__(self,parent):
        self.haveTest = False
        if parent.rfbTypeCombo.currentText() not in parent.atrSettings  :
            parent.sendMsg('w','Warning','ATR record for '+parent.rfbTypeCombo.currentText()+' not found',1)
            parent.startTestBtn.setText('Start')
            return
        if parent.testLogDl.get('SN') != parent.rfbSN.text() :
            parent.testLogDl = {}
        if parent.testLogUl.get('SN') != parent.rfbSN.text():
            parent.testLogUl = {}
        self.runTests(parent)



    def runTests(self,parent):
        parent.sendLog('START TEST',0)
        parent.instr.gen.write(":OUTP:STAT ON")

        if parent.checkGainTest.isChecked() == True:
            parent.currTestLbl.setText('RG test')
            if self.stopFlagCheck(parent) == True: return
            self.haveTest = True
            gainFlatness_test(parent)


        if parent.checkDsaTest.isChecked() == True:
            parent.currTestLbl.setText('DSA test')
            if self.stopFlagCheck(parent) == True: return
            self.haveTest = True
            dsa_test(parent)


        if parent.checkImTest.isChecked() == True:
            parent.currTestLbl.setText('IM test')
            if self.stopFlagCheck(parent) == True: return
            self.haveTest = True

            if parent.whatConn == 'Dl':
                intermod_test(parent,parent.listSettings[1])
            elif parent.whatConn == 'Ul':
                intermod_test(parent,parent.listSettings[2])
            else:
                parent.sendMsg('w','Warning','Check UL/DL fail',1)



        if parent.checkBitAlarmTest.isChecked() == True:
            parent.currTestLbl.setText('Alarm test')
            if self.stopFlagCheck(parent) == True: return
            self.haveTest = True
            bitAlarm_test(parent)

        if parent.checkAlcTest.isChecked() == True:
            parent.currTestLbl.setText('ALC test')
            if self.stopFlagCheck(parent) == True: return
            self.haveTest = True
            alc_test(parent)




        parent.startTestBtn.setText('Start')
        if self.haveTest == False:
            parent.sendMsg('w',"Warning","You have to choice minimum one test",1)
        parent.sendLog('TEST COMPLITE',0)
        parent.instr.gen.write(":OUTP:STAT OFF")
        if len(parent.testLogDl) > 0 and len(parent.testLogUl) > 0 and parent.rfbSN.text().upper() != 'XXX':
            writeResult(parent)

    def stopFlagCheck(self,parent):
        if parent.stopTestFlag == True:
            parent.instr.gen.write(":OUTP:STAT OFF")
            parent.sendLog('Test is stoped',0)
            parent.startTestBtn.setText('Start')
            parent.stopTestFlag = False
            return True
        else:
            return False


