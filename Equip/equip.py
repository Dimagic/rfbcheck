import numpy as np
import binascii
import time
import struct
import re


def setAmplTo(conn, cmd, gen, ampl, parent):
    parent.useCorrection = False
    parent.logSignal.emit("Set ampl to: " + str(ampl) + " dBm", 0)
    setAlc(conn, cmd.setAlcInDl, 255, cmd.shiftDlIn)
    setAlc(conn, cmd.setAlcInUl, 255, cmd.shiftUlIn)
    gen.write(":OUTP:STAT ON")
    time.sleep(1)
    genPow = float(gen.query("POW:AMPL?"))
    ampl = int(ampl)
    try:
        gain = getAvgGain(parent)
        while abs(abs(gain) - abs(ampl)) > 0.03:
            gen.write("POW:AMPL " + str(genPow) + " dBm")
            gain = getAvgGain(parent)
            if genPow >= -20:
                parent.sendMsg('c', 'Error', 'Gain problem', 1)
                gen.write(":OUTP:STAT OFF")
                parent.sendLog("Gain problem", 2)
                parent.stopTestFlag = True
                return
            # steep = 0
            delta = abs(abs(gain) - abs(ampl))
            # print(delta)
            if delta <= 0.5:
                steep = 0.01
            elif delta <= 2:
                steep = 0.5
            else:
                steep = 1
            if gain < ampl:
                genPow += steep
            else:
                genPow -= steep

            parent.progressBarSignal.emit('Set ampl. to ' + str(ampl) + ' dB', 0, 0)  # if err/////

    except Exception as e:
        parent.msgSignal.emit('c', 'Set amlitude error', str(e), 1)
        return
    parent.logSignal.emit('Current ampl: ' + str(round(gain, 2)) + ' dBm', 0)
    parent.useCorrection = True
    return (round(gain, 2))


def setAlc(conn, alc, n, shift):
    s = str(hex(n)).replace('0x', '')
    sd = getHexStr(str(hex(n - shift)).replace('0x', ''))
    toSend = (alc + getHexStr(s) + sd).upper()
    conn.write(binascii.unhexlify(toSend))
    time.sleep(0.1)


def getHexStr(s):
    if len(str(s)) < 2:
        return '0' + s
    else:
        return s


def sumHexFloat(n):
    k = hex(struct.unpack('<I', struct.pack('<f', toFloat(n)))[0])
    m1 = int(k[2:4], 16)
    if toFloat(n) == 0.0:
        m2 = 0
    else:
        m2 = int(k[4:6], 16)
    return m1 + m2


def floatToHex(n):
    if n == 0:
        return ('0x00000000')
    try:
        return (hex(struct.unpack('<I', struct.pack('<f', toFloat(n)))[0]))
    except:
        parent.sendLog('ERR: converting float to HEX fail', 2)


def toFloat(n):
    try:
        return float(n)
    except:
        print('ERR: converting string ' + n + ' to float fail')


def getAvgGain(parent):
    testController = parent
    parent = testController.getParrent()
    testController.instr.sa.write("CALC:MARK:CPS 1")
    gain = float(testController.instr.gen.query("POW:AMPL?"))
    if gain > -20:
        parent.stopTestFlag = True
        testController.instr.gen.write(":OUTP:STAT OFF")
        testController.msgSignal.emit('c', 'Generator warning', 'Output power too high', 1)
        return

    freq = float(testController.instr.gen.query("FREQ:CW?")) / 1000000
    saToGen = parent.calibrSaToGen.get(freq)
    genToSa = parent.calibrGenToSa.get(freq)
    time.sleep(0.1)
    gainArr = []
    for n in range(1, 11, 1):
        gainArr.append(float(testController.instr.sa.query("CALC:MARK:Y?")))
    if testController.useCorrection:
        return sum(gainArr) / len(gainArr) - saToGen - genToSa
    else:
        return sum(gainArr) / len(gainArr)


def strToFreq(curRange):
    r = re.findall('[0-9]+', curRange)
    start = toFloat(r[0])
    stop = toFloat(r[1])
    return start, stop


def calibrationCheck(parent):
    if parent.atrSettings == None:
        parent.sendMsg('c', 'Warning', 'ATR settings not found', 1)
        haveCalibr = False
        return
    parent.calibrSaToGen = {}
    parent.calibrGenToSa = {}
    freqArrStr = []
    freqArrBand = []

    for i in ['freq_band_dl_1', 'freq_band_ul_1', 'freq_band_dl_2', 'freq_band_ul_2']:
        if (parent.atrSettings.get(i) == None) or (parent.atrSettings.get(i) == ''): continue
        freqArrStr.append(parent.atrSettings.get(i))
    haveCalibrArr = []
    minDate = None

    haveCalibrArr, minDate = getCalibrDict(parent, freqArrStr, 'calSaToGen', minDate, haveCalibrArr)
    haveCalibrArr, minDate = getCalibrDict(parent, freqArrStr, 'calGenToSa', minDate, haveCalibrArr)
    parent.dateCalibrLbl.setText(minDate)


def getCalibrDict(parent, freqArrStr, table, minDate, haveCalibrArr):
    conn, cursor = parent.getConnDb()
    for n in freqArrStr:
        try:
            # start, stop = strToFreq(parent, n)
            r = re.findall('[0-9]+', n)
            start = toFloat(r[0])
            stop = toFloat(r[1])
        except Exception:
            parent.sendMsg('c', 'Error', 'Can`t convert str to freq: ' + str(n), 1)
            return
        freqArrBand = np.arange(start, stop + 0.5, 0.5)
        rows = cursor.execute("select * from " + table + " where freq >= :s and freq <= :e",
                              {'s': start, 'e': stop}).fetchall()
        for row in rows:
            dateCalibr = str(row[3])[0:8]
            if minDate is None:
                minDate = dateCalibr
            if int(minDate) >= int(dateCalibr):
                minDate = dateCalibr
            if table == 'calSaToGen':
                parent.calibrSaToGen.update({row[1]: row[2]})
            else:
                parent.calibrGenToSa.update({row[1]: row[2]})
        for k in freqArrBand:
            k = toFloat(k)
            if table == 'calSaToGen':
                if k not in list(parent.calibrSaToGen.keys()):
                    haveCalibrArr.append(False)
                    break
            else:
                if k not in list(parent.calibrGenToSa.keys()):
                    haveCalibrArr.append(False)
                    break
    if all(haveCalibrArr):
        parent.calibrLbl.setText('True')
    else:
        parent.calibrLbl.setText('False')
        minDate = None
    conn.close()
    return haveCalibrArr, minDate


def setDSA(conn, cmd, whatConn, dsa1, dsa2, dsa3):
    if whatConn == 'Dl':
        toSend = cmd.setDSADl
        d = 31
    elif whatConn == 'Ul':
        toSend = cmd.setDSAUl
        d = 29
    else:
        parent.sendLog('ERR: set DSA fail', 2)
        return
    sum = sumHexFloat(dsa1) + sumHexFloat(dsa2) + sumHexFloat(dsa3)
    toSend = toSend + str(floatToHex(dsa1).replace('0x', '')) + str(floatToHex(dsa2).replace('0x', '')) + str(
        floatToHex(dsa3).replace('0x', ''))
    if sum % 256 < d:
        sumHex = hex(sum % 256 - d + 256)
    else:
        sumHex = hex(sum % 256 - d)

    if len(str(sumHex.replace('0x', ''))) < 2:
        sumHex = '0' + str(sumHex.replace('0x', ''))
    else:
        sumHex = sumHex.replace('0x', '')

    toSend = (toSend + '0000' + str(sumHex)).upper()
    conn.write(binascii.unhexlify(toSend))
    ##    print('Tx: ' + toSend)
    ##    print('Rx: ' + str(binascii.hexlify(conn.ser.read(conn.ser.inWaiting()))))
    time.sleep(0.3)


def getCrc(line):
    line = line.upper()
    prefix = 'AAAA54'
    line = line.replace(prefix, '').replace('0x', '')
    sum = 0
    l = len(line)
    n = 0

    while n <= l - 2:
        msg = line[n:n + 2]
        sum += int(msg[0:2], 16)
        n += 2
    ##    print('Line = ' + line)
    ##    print("Sum = " + str(sum))
    ##    print("CRC = " + str(hex(sum%256)))
    crc = str(hex(sum % 256).replace('0x', ''))
    if len(crc) < 2:
        crc = '0' + crc
    return (crc)
