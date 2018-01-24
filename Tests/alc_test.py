from Equip.equip import *
import Equip.commands as cmd
import time
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtCore



class AlcTest(QtCore.QThread):
    def __init__(self, testController, mainParent, parent = None):
        super(AlcTest, self).__init__(parent)

        if mainParent.stopTestFlag == True:
            return

        self.testController = testController
        self.mainParent = mainParent
        self.conn = mainParent.ser
        self.sa = mainParent.instr.sa
        self.gen = mainParent.instr.gen



        self.whatConn = mainParent.whatConn
        self.parent = mainParent
        self.sa.write(":SENSE:FREQ:span 3 MHz")



        self.alcInMin = self.parent.atrSettings.get('alc_in_min')
        self.alcInMax = self.parent.atrSettings.get('alc_in_max')
        self.alcOutMin = self.parent.atrSettings.get('alc_out_min')
        self.alcOutMax = self.parent.atrSettings.get('alc_out_max')

        if self.parent.listSettings[12] != 0:
            self.parent.instr.gen.write("POW:AMPL "+str(self.parent.listSettings[12])+" dBm")
##            self.gen.write(":OUTP:STAT ON")
            time.sleep(1)
        else:
            setAmplTo(self,self.parent.ser,cmd,self.parent.instr,self.parent.instr.sa, self.parent.instr.gen, self.parent.listSettings[12], self.parent)

        self.parent.useCorrection = False
        if self.whatConn == 'Dl':
##            self.sa.write(":SENSE:FREQ:center "+str(parent.listSettings[1])+" MHz")
            alcInTest(self,self.parent.ser,cmd.setAlcInDl,self.whatConn, cmd.shiftDlIn)
            alcOutTest(self,self.parent.ser,cmd.setAlcOutDl,self.whatConn, cmd.shiftDlOut)
        elif self.whatConn == 'Ul':
##            self.sa.write(":SENSE:FREQ:center "+str(parent.listSettings[2])+" MHz")
            alcInTest(self,self.parent.ser,cmd.setAlcInUl,self.whatConn, cmd.shiftUlIn)
            alcOutTest(self,self.parent.ser,cmd.setAlcOutUl,self.whatConn, cmd.shiftUlOut)
        else:
            print('ALC ERROR')
        self.parent.useCorrection = True
        self.gen.write(":OUTP:STAT OFF")

def alcInTest(self, conn, alc, whatConn, shift):
    self.testController.logSignal.emit("***** Start ALC in test *****",3)
    setAlc(conn, alc, 255, shift)
    ampl = getAvgGain(self.parent)
    table = {}

    for j,i in enumerate(range(50,161,1)):
        setAlc(conn, alc, i, shift)
        time.sleep(0.3)
        ampl = getAvgGain(self.parent)
        self.testController.progressBarSignal.emit('ALC IN = '+str(i)+'; meas = '+ str(ampl)[:5]+' dBm',161 - 50 - 1,j)
        if ampl > -10 and len(table) != 0:
            break
        if ampl > -10 and len(table) == 0:
            n = -1
            while n <=10:
                setAlc(conn, alc, i - n, shift)
                time.sleep(1)
                ampl = getAvgGain(self.parent)
                self.testController.logSignal.emit('ALC IN = '+str(i - n)+'; meas = ' +str(ampl)[:7]+' dBm' ,1)
                if ampl >= -20.0 and ampl <= -10.0:
                    table[i+1] = ampl
                n += 1
            break
        self.testController.logSignal.emit('ALC IN = '+str(i)+'; meas = ' +str(ampl)[:7]+' dBm' ,1)
        if ampl >= -20.0 and ampl <= -10.0:
            table[i] = ampl
    self.parent.TestPrBar.setValue(161)


    if len(table) == 0:
        q = self.mainParent.sendMsg('w','Warning','ALC In test fail',3)
        if  q == QMessageBox.Retry:
            alcInTest(self, conn, alc, whatConn, shift)
        elif q == QMessageBox.Cancel:
            setAlc(conn, alc, 255, shift)
            self.parent.stopTestFlag = True
        elif q == QMessageBox.Ignore:
            setAlc(conn, alc, 255, shift)
        self.testController.logSignal.emit('ALC '+whatConn+' IN: FAIL',2)
        self.testController.resSignal.emit('ALC test',self.parent.whatConn,str(self.alcInMin),'fail',str(self.alcInMax),0)
        fillTestLog(self.parent,'ALC in','Fail')
        return
    else:
        for n in range(1,255,1):
            if table.get(n) != None:
                minVal = table[n]
                minKey = n
                break
        for i in (10, 15, 20):
            for k in table:
                if abs(i-abs(table[k])) < abs(i - abs(minVal)):
                    minVal = round(table[k],1)
                    minKey = k


            self.testController.logSignal.emit('ALC '+whatConn+' IN (-'+str(i)+'): '+str(minKey)+' <-- '+str(minVal)[:6]+' dBm',1)
            if i == 15:
                if 100 <= minKey <= 130:
                    self.testController.resSignal.emit('ALC IN',self.parent.whatConn,str(self.alcInMin),str(round(minVal,1)) + ' ( in = '+str(minKey)+' )',str(self.alcInMax),1)
                elif 85 <= minKey <= 145:
                    self.testController.resSignal.emit('ALC IN',self.parent.whatConn,str(self.alcInMin),str(round(minVal,1)) + ' ( in = '+str(minKey)+' )',str(self.alcInMax),2)
                else:
                    self.testController.resSignal.emit('ALC IN',self.parent.whatConn,str(self.alcInMin),str(round(minVal,1)) + ' ( in = '+str(minKey)+' )',str(self.alcInMax),0)


                fillTestLog(self.parent,'ALC in',minKey)

    setAlc(conn, alc, 255, shift)

def alcOutTest(self, conn, alc, whatConn, shift):
    setAlc(conn, alc, 4, shift)# when 0 -> setAlc not work
    self.testController.logSignal.emit("***** Start ALC out test *****",3)
    time.sleep(1)
    ampl = round(getAvgGain(self.parent),1)
    setAlc(conn, alc, 255, shift)
    if ampl <= self.alcOutMin:
        self.testController.logSignal.emit('ALC '+whatConn+' OUT: PASS '+str(ampl)+' dBm',1)
        self.testController.resSignal.emit('ALC OUT',self.parent.whatConn,str(self.alcOutMin),str(ampl),str(self.alcOutMax),1)
        fillTestLog(self.parent,'ALC out',ampl)
    else:
        self.testController.logSignal.emit('ALC '+whatConn+' OUT: FAIL '+str(ampl)+' dBm',2)
        q = self.mainParent.sendMsg('w','Warning','ALC Out test. Gain: '+str(ampl)+' dBm' ,3)
        if  q == QMessageBox.Retry:
            alcOutTest(self.parent,conn, alc, whatConn, shift)
            return
        elif q == QMessageBox.Cancel:
            self.parent.stopTestFlag = True
            setAlc(conn, alc, 255, shift)
        elif q == QMessageBox.Ignore:
            setAlc(conn, alc, 255, shift)
        self.testControllertestController.resSignal.emit('ALC OUT',self.parent.whatConn,str(self.alcOutMin),str(ampl),str(self.alcOutMax),0)
        fillTestLog(self.parent,'ALC out',ampl)
        return

def fillTestLog(parent,alcType,status):
    if parent.whatConn == 'Dl':
        parent.testLogDl.update({alcType:status})
    else:
        parent.testLogUl.update({alcType:status})

