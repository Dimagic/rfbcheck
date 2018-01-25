from Equip.equip import *
import Equip.commands as cmd
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore

class IModTest(QtCore.QThread):
    def __init__(self, testController, mainParent, freq, parent = None):
        super(IModTest, self).__init__(parent)
        testController.logSignal.emit("***** Start IMod test *****", 3)

        self.instrument = mainParent.instr
        self.listLog = mainParent.listLog
        self.sa = mainParent.instr.sa
        self.gen = mainParent.instr.gen
        self.parent = mainParent
        self.testController = testController

        #setAmplTo(self,parent.ser, cmd, self.instrument, self.sa, self.gen, 0,parent)
        if self.parent.whatConn == 'Dl':
            pow = self.parent.listSettings[3]
        elif self.parent.whatConn == 'Ul':
            pow = self.parent.listSettings[4]
        else:
            pass

        try:
            self.mToneTest(self.gen,self.sa,freq,pow)
        except Exception as e:
            self.parent.sendMsg('w','mToneTest error',str(e),1)
            return


    def mToneTest(self, gen, sa, freq,pow):
        setAmplTo(self,self.parent.ser, cmd, self.instrument, self.sa, self.gen, pow,self.parent)
        self.testController.progressBarSignal.emit('Intermodulation',0,0)

        haveFail = False
        sa.write(":SENSE:FREQ:span 3 MHz")
        sa.write(":SENSE:FREQ:center "+str(freq)+" MHz")
        sa.write(":CALC:MARK1:STAT 0")
        sa.write("CALC:MARK:CPS 1")
        gen.write(":FREQ:FIX "+str(freq)+" MHz")
        gen.write(":OUTP:MOD:STAT OFF")
   #     gen.write(":OUTP:STAT ON")
        time.sleep(1)
        self.parent.useCorrection = False
        n1 = getAvgGain(self.parent)

        gen.write(":OUTP:MOD:STAT ON")
        time.sleep(2)
        n2 = getAvgGain(self.parent)
        print(n1,n2)
        self.parent.useCorrection = True

        freq, ampl = self.instrument.getPeakTable()
        delta = abs(abs(ampl[0])-abs(ampl[len(ampl)-1]))


        print(ampl)

        if len(freq) > 3:
            self.parent.sendMsg('Intermodulation FAIL: to many peaks',2)
            haveFail = True
        if delta > 0.7:
            self.testController.logSignal.emit('Delta between peaks FAIL: ' + str(round(delta,3)) +" dBm",3)
            self.testController.logSignal.emit(str(freq[0]/1000) + " MHz "+ str(ampl[0]) + " dBm",3)
            self.testController.logSignal.emit(str(freq[len(freq)-1]/1000) + " MHz "+ str(round(ampl[len(ampl)-1],3)) + " dBm",3)
            haveFail = True
        gen.write(":OUTP:MOD:STAT OFF")
        time.sleep(1)
        d = n1 - n2



        if abs(abs(d) - 3) > 0.6:
            self.testController.logSignal.emit('Falling per tone(dBc) FAIL: '+str(round(d,3)),2)
            haveFail = True
        else:
            self.testController.logSignal.emit('Delta between peaks PASS: ' + str(round(delta,3)) +" dBm",1)
            self.testController.logSignal.emit('Falling per tone(dBc) PASS: '+str(round(d,3)),1)

        if haveFail == False:
            self.testController.resSignal.emit('Intermodulation',self.parent.whatConn,'','Pass','',1)
            if self.parent.whatConn == 'Dl':
                self.parent.testLogDl.update({'IMod':'Pass'})
            else:
                self.parent.testLogUl.update({'IMod':'Pass'})
        else:
            q = self.parent.sendMsg('w','Warning','IMod test fail',3)
            if  q == QMessageBox.Retry:
                self.mToneTest(gen, sa, freq,pow)
                return
            elif q == QMessageBox.Cancel:
                self.parent.stopTestFlag = True
            self.testController.resSignal.emit('Intermodulation',self.parent.whatConn,'','Fail','',0)
            if self.parent.whatConn == 'Dl':
                self.parent.testLogDl.update({'IMod':'Fail'})
            else:
                self.parent.testLogUl.update({'IMod':'Fail'})

        sa.write(":CALC:MARK1:STAT 1")
        sa.write("CALC:MARK:CPS 0")
##        gen.write(":OUTP:STAT OFF")
##        self.parent.TestPrBar.setValue(1)

##def getAmpl(sa):
##    return float(sa.query("CALC:MARK:Y?"))