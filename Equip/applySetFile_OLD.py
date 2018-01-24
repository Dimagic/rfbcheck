import functools
import binascii
import struct
import time
import csv
import os

def applySetFile(setFile, parent):

    try:
        file = os.path.join(os.path.dirname(__file__),'..','setFiles',setFile + '.CSV')
        f = open(file,'r')
        f.close()
    except Exception as e:
        parent.sendMsg('w','Cont open file settings',str(e),1)
        return
    with open(file) as csvfile:
        reader = csv.DictReader(csvfile)
##        stopper = 0
        for row in reader:
##            if stopper > 4:
##                return
##            else:
##                stopper += 1

            arr = row.get(None)
            if type(arr) != list: continue
            print(row['# 0 1182685875'])
            print(arr[2])

            if arr[2] == 'INT16': continue
            if row['# 0 1182685875'] == 'DW_RSSI_CALIBRATION': continue
            if row['# 0 1182685875'] == 'DW_FWR_POWER_CALIBRATION': continue

            addr = arr[0].replace('0x','')
            arrData = arr[4:]
            dataStr = ''
            for i in arrData:
                if i == '':
                    print(dataStr)
                    break
                else:
                    if arr[2] == 'ULONG32':
                        sendKey = 'aaaa543026556677'
                        ihex = tohex(int(i),32)
                        print("ULONG32 = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'RawData':
                        sendKey = 'aaaa543029556677'
                        ihex = tohex(int(i),8)
                        print("RAW = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'UINT16':
                        if row['# 0 1182685875'] == 'DW_PATH_VVA_CPU_DETECTOR_TH' or row['# 0 1182685875'] == 'DW_PATH_VVA_EXT_DETECTOR_TH' or row['# 0 1182685875'] == 'UP_PATH_VVA_CPU_DETECTOR_TH' or row['# 0 1182685875'] == 'UP_PATH_VVA_EXT_DETECTOR_TH':
                            sendKey = 'aaaa543026556677'
                        else:
                            sendKey = 'aaaa543024556677'
                        ihex = tohex(int(i),16)
                        print("UINT16 = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'INT16':
                        if row['# 0 1182685875'] == 'DW_RVS_POWER_CALIBRATION':
                            sendKey = 'aaaa54302d556677'
                        else:
                            sendKey = 'aaaa543024556677'
                        ihex = tohex(int(i),16)
                        print("INT16 = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'FLOAT32':
                        sendKey = 'aaaa543029556677'
                        ihex = floatToHex(i)
                        print("FLOAT32 = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'UCHAR8':
                        if row['# 0 1182685875'] == 'ATTEN_VALUE_PER_GAIN':
                            sendKey = 'aaaa543028556677'
                        elif row['# 0 1182685875'] == 'POWER_LIMIT':
                            sendKey = 'aaaa543026556677'
                        else:
                            sendKey = 'aaaa543023556677'
                        ihex = tohex(int(i),8)
                        print("UCHAR8 = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'CHAR8':
                        sendKey = 'aaaa543023556677'
                        ihex = tohex(int(i),4)
                        print("CHAR8 = " + i)
                        dataStr += str(ihex).replace('0x','')
                    elif arr[2] == 'STRING_ARRAY':
                        if i == arr[4]:
                            k = int(i)
                            continue
                        sendKey = 'aaaa54302d556677'
                        ihex = strToHex(i, k)
                        print("STRING_ARRAY = " + i)
                        dataStr += str(ihex).replace('0x','')

                    else:
                        continue
            if arr[2] == 'RawData':
                n = int(arr[3])*2/8 - 1
                while n > 0:
                    dataStr += '00'
                    n -= 1
##            if arr[2] == 'UINT16':
##                n = int(arr[3]) - 1
##                while n > 0:
##                    dataStr += '00'
##                    n -= 1
            if arr[2] == 'INT16':
##                dataStr += '0000'
                for n in range(1,256):
                    dataStr += '00'
                    crc = getSumLine((sendKey + addr + dataStr).replace('aaaa54','')).replace('0x','')
                    toSend = sendKey + addr + dataStr + crc
                    print(n)
                    print (toSend)
                    parent.ser.ser.flushInput()
                    parent.ser.ser.flushOutput()
                    try:
                        writingBytes = parent.ser.ser.write(binascii.unhexlify(toSend))
##                        print(row['# 0 1182685875'] +': writen '+ str(writingBytes) + ' bytes')
                        inWait = int(parent.ser.ser.inWaiting())
                        outWait = int(parent.ser.ser.outWaiting())
                        k = 0
                        while outWait != 0:
                            time.sleep(0.5)
                            outWait = int(parent.ser.ser.outWaiting())
                            print('wait OUT = '+ str(outWait))
                        time.sleep(0.5)
                        if inWait != 0:
                            rx = str(binascii.hexlify(parent.ser.ser.read(parent.ser.ser.inWaiting())))
                            print('Rx: '+rx)
                            if addr not in rx:
                                print("err")
                                continue
                            else:
                                print('!!!Rx: '+rx)
                                break

                        while inWait == 0:
                            time.sleep(0.5)
                            inWait = int(parent.ser.ser.inWaiting())
                            print('wait IN = '+ str(inWait))
                            k += 1
                            if k > 3:
                                print("err")
                                break
                    except Exception as e:
                        parent.sendMsg('w',toSend,str(e),1)
                        return

            if arr[2] == 'FLOAT32':
                pref = ''
                i = 1
                while i < int(arr[3]):
                    pref = pref + '00'
                    i += 1
                print(pref)
                crc = pref + getSumLine((sendKey + addr + dataStr).replace('aaaa54','')).replace('0x','')
            else:
                crc = getSumLine((sendKey + addr + dataStr).replace('aaaa54','')).replace('0x','')


            toSend = sendKey + addr + dataStr + crc
            print (toSend)
            #print(binascii.unhexlify(toSend))

            parent.ser.ser.flushInput()
            parent.ser.ser.flushOutput()
            try:
                writingBytes = parent.ser.ser.write(binascii.unhexlify(toSend))
                print(row['# 0 1182685875'] +': writen '+ str(writingBytes) + ' bytes')
                inWait = int(parent.ser.ser.inWaiting())
                outWait = int(parent.ser.ser.outWaiting())
                k = 0
                while outWait != 0:
                    time.sleep(0.5)
                    outWait = int(parent.ser.ser.outWaiting())
                    print('wait OUT = '+ str(outWait))

                while inWait == 0:
                    time.sleep(0.5)
                    inWait = int(parent.ser.ser.inWaiting())
                    print('wait IN = '+ str(inWait))
                    k += 1
                    if k > 15:
                        print("err")
##                        parent.ser.ser.close()
##                        parent.startBtnEnabled()
##                        print(str(binascii.hexlify(parent.ser.ser.read(parent.ser.ser.inWaiting()))))
                        break



                rx = str(binascii.hexlify(parent.ser.ser.read(parent.ser.ser.inWaiting())))
                if addr not in rx:
                    print("err")
                    break

                print('IN = '+ str(parent.ser.ser.inWaiting()))
                print('OUT = '+ str(parent.ser.ser.outWaiting()))
                print('Tx = ' + str(toSend))
                print('Rx = ' + str(rx))
                print('--------------------------')



            except Exception as e:
                parent.sendMsg('w',toSend,str(e),1)
                return





def getSumLine(line):
    sum = 0
    l = len(line)
    n = 0

    while n <= l-2:
        msg = line[n:n+2]
        sum += int(msg[0:2], 16)
        n += 2
    print("Sum = " + str(sum))
    print("CRC = " + str(hex(sum%256)))
    crc = str(hex(sum%256).replace('0x',''))
    if len(crc) < 2:
        crc = '0' + crc
    return(crc)

def getcorrectHex(line,k):
    line = line.replace('0x','')
    if len(line)%2 != 0:
        line = '0' + line
    while len(line) < k:
        line = '0' + line
        print('Len = ' + str(len(line)) + ' Line = ' + line)
    print('tohex = ' + line)
    return line

def tohex(val, nbits):
    return getcorrectHex(hex((val + (1 << nbits)) % (1 << nbits)),nbits/4)

def sumHexFloat(n, k):
    k = hex(struct.unpack('<I', struct.pack('<f', toFloat(n)))[0])
    m1 = int(k[2:4], k)
    if toFloat(n) == 0.0:
        m2 = 0
    else:
        m2 = int(k[4:6], k)
    return m1+m2

def floatToHex(n):
    if '0.0' in n:
        return('0x00000000')
    try:
        return(hex(struct.unpack('<I', struct.pack('<f', toFloat(n)))[0]))
    except Exception as e:
        print(e)

def toFloat(n):
    try:
        return float(n)
    except ValueError:
        self.addListLog('ERR: converting string to float fail')
        return

def strToHex(s, k):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    hexStr = functools.reduce(lambda x,y:x+y, lst)
    while len(hexStr) < k*2:
        hexStr = hexStr + '0'


    return hexStr


