import visa
import time


class Instrument:
    def __init__(self, freq, parent):
        self.parent = parent
        self.sa = None
        self.gen = None
        self.na = None
        if freq == 0:
            return None
        else:
            self.rm = visa.ResourceManager()
            self.rm.timeout = 50000
            self.initAnalyser(freq)
            self.initGenerator(freq)
            self.initNetwork(freq)

    def sendQerySa(self, q):
        return self.sa.query(q)

    def sendQeryGen(self, q):
        return self.gen.query(q)

    def sendQeryNa(self, q):
        return self.na.query(q)

    def initAnalyser(self, freq):
        try:
            self.sa = self.rm.open_resource(self.parent.currSaLbl.text(), send_end=False)
            self.sa.chunk_size = 102400
            self.sa.write(":SYST:PRES")
            self.sa.write(":SENSE:FREQ:center " + str(freq) + " MHz")
            self.sa.write(":SENSE:FREQ:span 3 MHz")
            self.sa.write("DISP:WIND:TRAC:Y:RLEV:OFFS " + str(int(self.parent.saAtten.text())))
            self.sa.write("DISP:WIND:TRAC:Y:DLIN -50 dBm")
            self.sa.write("DISP:WIND:TRAC:Y:DLIN:STAT 1")
            self.sa.write("CALC:MARK:CPS 1")
            self.sa.write(":CALC:MARK1:STAT 0")
            self.sa.write("BAND:VID 5 KHZ")
            self.sa.write(":CAL:AUTO ON")
        except Exception as e:
            self.parent.myThread.logSignal.emit("SA - " + str(e), 2)
            return

    def initGenerator(self, freq):
        try:
            self.gen = self.rm.open_resource(self.parent.currGenLbl.text(), send_end=False)
            self.gen.chunk_size = 102400
            self.gen.write("*RST")
            self.gen.write(":OUTP:STAT OFF")
            self.gen.write(":OUTP:MOD:STAT OFF")
            self.gen.write("POW:AMPL -50 dBm")
            self.gen.write(":FREQ:FIX " + str(freq) + " MHz")
            self.gen.write(":RAD:MTON:ARB:SET:TABL 1000000 , 2")
            self.gen.write(":RAD:MTON:ARB:SET:TABL:PHAS:INIT RAND")
            self.gen.write(":RAD:MTON:ARB:STAT 1")
        except Exception as e:
            self.parent.myThread.logSignal.emit("Gen - " + str(e), 2)
            return

    def initNetwork(self, freq):
        # return
        try:
            self.na = self.rm.open_resource(self.parent.currNaLbl.text())
            self.na.write(":SYST:PRES")
            self.na.write(':MMEM:LOAD "D:/RFBCheck.STA"')
            time.sleep(2)
            self.na.write(":SOUR1:POW:ATT 40")
            self.na.write(":SOUR1:POW:PORT2 -45")

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
            self.parent.myThread.logSignal.emit("NA - "+str(e), 2)
            return
        # else:
        #     self.initNetwork(int(freq))

    def getPeakTable(self):
        self.sa.write(":CALC:MARK:PEAK:SORT FREQ")
        self.sa.write(":CALC:MARK:PEAK:TABL:READ GTDL")
        self.sa.write(":CALC:MARK:PEAK:TABL:STAT ON")
        time.sleep(1)
        rx = self.sa.query("TRAC:MATH:PEAK?")
        tmp = ''
        arr = []
        freq = []
        ampl = []
        for i in rx:
            if i != ",":
                tmp = tmp + i
            else:
                arr.append(float(tmp))
                tmp = ''
        arr.append(float(tmp))
        self.sa.write(":CALC:MARK:PEAK:TABL:STAT OFF")
        k = 0
        while k < len(arr):
            freq.append(arr[k])
            ampl.append(arr[k + 1])
            k = k + 2
        return freq, ampl

    def getInstrName(addr):
        rm = visa.ResourceManager()
        rm.timeout = 5000
        try:
            currInstr = rm.open_resource(addr)
            return currInstr.query('*IDN?')
        except Exception as e:
            print(str(e))
            return None


