import visa
import time
import re
from Equip.config import Config
from Equip.equip import toFloat


class Instrument:
    def __init__(self, freq, parent):
        self.currParent = parent
        self.config = Config()
        self.rm = visa.ResourceManager()
        self.rm.timeout = 50000
        self.sa = None
        self.gen = None
        self.na = None
        if freq == 0:
            return None
        else:

            self.initAnalyser(freq)
            self.initGenerator(freq)
            self.initNetwork(freq)

    def sendQerySa(self, q):
        return self.sa.query(q)

    def sendQeryGen(self, q):
        return self.gen.query(q)

    def sendQeryNa(self, q):
        return self.na.query(q)

    def writeSa(self, w):
        self.sa.write(w)

    def writeGen(self, w):
        self.gen.write(w)

    def writeNa(self, w):
        self.na.write(w)

    def initAnalyser(self, freq):
        try:
            self.sa = self.rm.open_resource(self.currParent.currSaLbl.text(), send_end=False)
            self.sa.chunk_size = 102400
            self.sa.write(":SYST:PRES")
            self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
            self.sa.write(":SENSE:FREQ:span " + str(int(self.config.getConfAttr('instruments', 'sa_span'))) + " MHz")
            self.sa.write("DISP:WIND:TRAC:Y:RLEV:OFFS " + str(int(self.currParent.saAtten.text())))
            self.sa.write("DISP:WIND:TRAC:Y:DLIN -50 dBm")
            self.sa.write("DISP:WIND:TRAC:Y:DLIN:STAT 1")
            self.sa.write("CALC:MARK:CPS 1")
            self.sa.write(":CALC:MARK1:STAT 0")
            self.sa.write("BAND:VID " + str(int(self.config.getConfAttr('instruments', 'sa_videoBw'))) + " KHZ")
            self.sa.write(":CAL:AUTO ON")
        except Exception as e:
            self.currParent.myThread.logSignal.emit(str(self.currParent.currSaNameLbl.text()) + " - not connected", -1)
            # self.currParent.myThread.logSignal.emit(str(e), -1)
            return

    def initGenerator(self, freq):
        try:
            self.gen = self.rm.open_resource(self.currParent.currGenLbl.text(), send_end=False)
            self.gen.chunk_size = 102400
            self.gen.write("*RST")
            self.gen.write(":OUTP:STAT OFF")
            self.gen.write(":OUTP:MOD:STAT OFF")
            self.gen.write("POW:AMPL " + self.config.getConfAttr('instruments', 'gen_gainFlatPow') + " dBm")
            self.gen.write(":FREQ:FIX " + str(freq) + " MHz")
            self.gen.write(":RAD:MTON:ARB:SET:TABL " +
                           str(toFloat(self.config.getConfAttr('instruments', 'gen_IModTone')) * 1000000)
                           + ", " + str(self.config.getConfAttr('instruments', 'gen_IModToneCount')))
            self.gen.write(":RAD:MTON:ARB:SET:TABL:PHAS:INIT RAND")
            self.gen.write(":RAD:MTON:ARB:STAT 1")
        except Exception as e:
            self.currParent.myThread.logSignal.emit(str(self.currParent.currGenNameLbl.text()) + " - not connected", -1)
            # self.currParent.myThread.logSignal.emit(str(e), -1)
            return

    def initNetwork(self, freq):
        try:
            self.na = self.rm.open_resource(self.currParent.currNaLbl.text())
            self.na.write(":SYST:PRES")
            self.na.write(":MMEM:LOAD '" + self.config.getConfAttr('instruments', 'na_fileCalibr') + "'")
            time.sleep(2)
            self.na.write(":SOUR1:POW:ATT 40")
            self.na.write(":SOUR1:POW:PORT2 -45")
            self.na.write(":CALC1:PAR1:DEF " + self.config.getConfAttr('instruments', 'na_ports'))

            # self.na.write(":SENS1:FREQ:CENT 806E6")
            # self.na.write(":SENS1:FREQ:SPAN 36E6")
            # self.na.write(":CALC1:PAR1:DEF S12")
            # self.na.write(":CALC1:MARK1 ON")
            # time.sleep(3)
            # arr = []
            # for i in range(788, 824):
            #     self.na.write(":CALC1:MARK1:X " + str(i) + 'E6')
            #     gain = self.na.query(":CALC1:MARK1:Y?")
            #     arr.append(gain)
            # print(max(arr))
            # print(min(arr))
            # print(min(arr) + max(arr))
        except Exception as e:
            self.currParent.myThread.logSignal.emit(str(self.currParent.currNaNameLbl.text()) + " - not connected", -1)
            # self.currParent.myThread.logSignal.emit(str(e), -1)
            return

    def getPeakTable(self):
        self.sa.write(":CALC:MARK:PEAK:SORT FREQ")
        self.sa.write(":CALC:MARK:PEAK:TABL:READ GTDL")
        self.sa.write(":CALC:MARK:PEAK:TABL:STAT ON")
        time.sleep(1)
        rx = self.sa.query("TRAC:MATH:PEAK?")
        pNum = re.compile(r"[-+.\w]+")
        arr = [float(i) for i in pNum.findall(rx)]
        self.sa.write(":CALC:MARK:PEAK:TABL:STAT OFF")
        freq = [i for i in arr if i % 2 == 0]
        ampl = [i for i in arr if i % 2 != 0]
        return freq, ampl

    def getInstrName(self, addr):
        rm = visa.ResourceManager()
        rm.timeout = 5000
        try:
            currInstr = rm.open_resource(addr)
            return currInstr.query('*IDN?')
        except Exception as e:
            msg = 'getInstrName() in instrument.py error:\n' % str(e)
            self.currParent.sendMsg('w', 'RFBCheck', msg, 1)
            return None
    # ---------- Generator ----------

    def genSetPow(self, pow):
        self.writeGen("POW:AMPL %s dBm") % str(pow)

    def genSetFreq(self, freq):
        self.writeGen(":FREQ:FIX " + str(freq) + " MHz")

    def getPow(self):
        return float(self.sendQeryGen("POW:AMPL?"))


    # ---------- System analyser ----------

    def saGetGainByFreq(self, freq):
        self.writeSa("CALC:MARK1:X " + str(freq) + " MHz")
        time.sleep(.1)
        gainArr = []
        for n in range(1, 11, 1):
            gainArr.append(float(self.sendQerySa("CALC:MARK1:Y?")))
        return round(sum(gainArr) / len(gainArr), 2)

    def saGetGainViaGen(self, freq):
        self.genSetFreq(freq)
        time.sleep(.1)
        return self.saGetGainByFreq(freq)
    # ---------- Network ----------