from Equip.equip import *
import sqlite3
import functools
import binascii
import struct
import time
import csv
import os

def applySetFile(setFile, parent):
    pref = 'aaaa54'
    addrTx = '556677'
    addrToSend = range(12333,12336,1)# 12320 12336
    namePar = '# 0 1182685875'
    sizeData = {'CHAR8':8,'FLOAT32':32,'INT16':16,'RawData':8,'STRING_ARRAY':16,'UCHAR8':8,'UINT16':16,'ULONG32':32}
    conn,cursor = parent.getConnDb()

    try:
        file = os.path.join(os.path.dirname(__file__),'..','setFiles',setFile + '.CSV')
        f = open(file,'r')
        f.close()
    except Exception as e:
        parent.sendMsg('w','Can`t open file settings',str(e),1)
        return
    with open(file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            arr = row.get(None)
            if type(arr) != list: continue
            addrPar = arr[0].replace('0x','')
            arrData = arr[4:len(arr)-1]
            strData = ''
##            if int(arr[3]) != 12: continue
##            if row[namePar] != 'SCHEDULER_TIMEOUTS': continue
            print(row[namePar],arrData)
            for i in arrData:
                if arr[2] == 'FLOAT32':
                    tmp = floatToHex(i).replace('0x','')
                elif arr[2] == 'STRING_ARRAY':
                    if i == arrData[0]:
                        k = int(i)
                        continue
                    tmp = strToHex(i,k)
                else:
                    tmp = tohex(int(i),sizeData.get(arr[2])).replace('0x','')
                while len(tmp) < sizeData.get(arr[2])/4:
                    tmp = '0' + tmp
##                    print(tmp)
                strData += tmp
            print(strData)

            res = cursor.execute("select * from setFileSettings where namePar = :n",{'n':row[namePar]}).fetchone()
            if res == None:
                qerySend = False
                for n in addrToSend:
                    nHex = hex(n).replace('0x','')
                    for c in range(1,len(arrData)+1,1):
                        toSend = pref + str(nHex) + addrTx + addrPar +strData
                        crc = getCrc(toSend)
                        while len(crc) < c*2:
                            crc = '0' + crc
                        print('CRC: ' + crc)
                        print('LEN: ' + str(len(crc)/2))
                        toSend = toSend + crc
                        print(row[namePar],toSend)
                        send = sendParametr(parent,row[namePar],addrPar,toSend)
                        if send == True:
                            try:
                                cursor.execute('insert into setFileSettings(namePar,addrToSend,lenCrc) values(:namePar,:addrToSend,:lenCrc)',{'namePar':row[namePar],'addrToSend':str(hex(n).replace('0x','')),'lenCrc':len(crc)})
                                conn.commit()
                                qerySend = True
                                break
                            except sqlite3.DatabaseError as err:
                                parent.sendMsg('c','Querry error', str(err),1)
                                conn.close()
                    if qerySend == True: break

            else:
                addrToSendFromDb = res[2]
                lenCrc = res[3]
                toSend = pref + str(addrToSendFromDb) + addrTx + addrPar +strData
                crc = getCrc(toSend)
                while len(crc) < lenCrc:
                    crc = '0' + crc
                toSend += crc
                print('TO SEND: ' + toSend)
                sendParametr(parent,row[namePar],addrPar,toSend)
    print('FINISHED')
    conn.close()





def sendParametr(parent,namePar,addr,toSend):
    parent.ser.ser.flushInput()
    parent.ser.ser.flushOutput()

    try:

        writingBytes = parent.ser.ser.write(binascii.unhexlify(toSend))
        time.sleep(writingBytes/100 + .5)
        outWait = int(parent.ser.ser.outWaiting())
        inWait = int(parent.ser.ser.inWaiting())

        k = 0
        while outWait != 0:
            if k > 15:
                print('outWait ERROR')
                print('--------------------------')
                return(False)
            else:
                time.sleep(0.5)
                outWait = int(parent.ser.ser.outWaiting())
                k += 1
        k = 0
        while inWait == 0:
            if k > 5:
                print('inWait ERROR')
                print('--------------------------')
                return(False)
            else:
                time.sleep(0.5)
                inWait = int(parent.ser.ser.inWaiting())
                k += 1


        rx = str(binascii.hexlify(parent.ser.ser.read(parent.ser.ser.inWaiting())))
        if addr in rx:
            print(namePar)
            print('Tx = ' + str(toSend))
            print(namePar +': writen '+ str(writingBytes) + ' bytes')
            print('Rx = ' + str(rx))
            print('--------------------------')
            return(True)
        else:
            return(False)

    except Exception as e:
        parent.sendMsg('w',toSend,str(e),1)
        return(False)

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
##        print('Len = ' + str(len(line)) + ' Line = ' + line)
##    print('tohex = ' + line)
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
    if s == '': s = '0'
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    hexStr = functools.reduce(lambda x,y:x+y, lst)
    while len(hexStr) < k*2:
        hexStr = hexStr + '0'


    return hexStr


