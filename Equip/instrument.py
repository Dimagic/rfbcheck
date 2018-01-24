# :CALC:MARK:AOFF
# :CALC:MARK1:STAT 1
# CALC:MARK1:X 760 MHz
# CALC:MARK1:Y?
# pyvisa.errors.VisaIOError: VI_ERROR_RSRC_LOCKED (StatusCode.error_resource_locked): Specified type of lock cannot be obtained, or specified operation cannot be performed, because the resource is locked.
#
import visa
import time

class Instrument():
    def __init__(self, freq,parent):
        if freq == 0: return None
        self.rm = visa.ResourceManager()
        self.rm.timeout = 25000
        try:
            self.sa = self.rm.open_resource(parent.currSaLbl.text(),send_end=False)
            self.sa.chunk_size = 102400
        except Exception as e:
            parent.logSignal.emit("SA - "+str(e),2)
            return
        else:
            self.initAnalyser(int(freq))

        try:
            self.gen = self.rm.open_resource(parent.currGenLbl.text(),send_end=False)
            self.gen.chunk_size = 102400
        except Exception as e:
            parent.logSignal.emit("Gen - "+str(e),2)
            return
        else:
            self.initGenerator(int(freq))

        try:
            self.na = self.rm.open_resource(parent.currNaLbl.text())
        except Exception as e:
            parent.logSignal.emit("NA - "+str(e),2)
            return
        else:
            self.initNetwork(int(freq))

    def sendQerySa(self, q):
        return self.sa.query(q)

    def sendQeryGen(self, q):
        return self.gen.query(q)

    def sendQeryNa(self, q):
        return self.na.query(q)


    def initAnalyser(self, freq):
        self.sa.write(":SYST:PRES")
        self.sa.write(":SENSE:FREQ:center "+str(freq)+" MHz")
        self.sa.write(":SENSE:FREQ:span 3 MHz")
        self.sa.write("DISP:WIND:TRAC:Y:RLEV:OFFS 30")
        self.sa.write("DISP:WIND:TRAC:Y:DLIN -50 dBm")
        self.sa.write("DISP:WIND:TRAC:Y:DLIN:STAT 1")
        self.sa.write("CALC:MARK:CPS 1")
        self.sa.write(":CALC:MARK1:STAT 0")
        self.sa.write("BAND:VID 5 KHZ")
        self.sa.write(":CAL:AUTO ON")
        #time.sleep(1)

    def initGenerator(self, freq):
        self.gen.write("*RST")
        self.gen.write(":OUTP:STAT OFF")
        self.gen.write(":OUTP:MOD:STAT OFF")
        self.gen.write("POW:AMPL -50 dBm")
        self.gen.write(":FREQ:FIX "+str(freq)+" MHz")
        self.gen.write(":RAD:MTON:ARB:SET:TABL 1000000 , 2")
        self.gen.write(":RAD:MTON:ARB:SET:TABL:PHAS:INIT RAND")
        self.gen.write(":RAD:MTON:ARB:STAT 1")
        #time.sleep(1)

    def initNetwork(self, freq):
        pass
##        self.na.write(":SYST:PRES")
##        self.na.write(":SENS1:FREQ:CENT 806E6")
##        self.na.write(":SENS1:FREQ:SPAN 36E6")
##        self.na.write(":CALC1:PAR1:DEF S12")
##        self.na.write(":CALC1:MARK1 ON")
##        time.sleep(3)
##        arr = []
##        for i in range(788,824):
##            self.na.write(":CALC1:MARK1:X " + str(i)+'E6')
##            gain = self.na.query(":CALC1:MARK1:Y?")
##            arr.append(gain)
##        print(max(arr))
##        print(min(arr))
##        print(min(arr)+max(arr))




    def getPeakTable(self):
        self.sa.write(":CALC:MARK:PEAK:SORT FREQ")
        self.sa.write(":CALC:MARK:PEAK:TABL:READ GTDL")
        self.sa.write(":CALC:MARK:PEAK:TABL:STAT ON")
        time.sleep(1)
        rx = self.sendQerySa("TRAC:MATH:PEAK?")
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
            ampl.append(arr[k+1])
            k = k + 2
        return(freq, ampl)

def getInstrName(addr):
        rm = visa.ResourceManager()
        rm.timeout = 5000
        try:
            currInstr = rm.open_resource(addr)
            return(currInstr.query('*IDN?'))
        except Exception as e:
            return None



