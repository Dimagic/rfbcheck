import sqlite3
import os
import re
import Equip.template as tml


from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

class report():
    def __init__(self,parent,sn,date):
        #print('report')
        #print(sn,date)
        #self.getReportData(parent,sn,date)
        #self.generateReport(parent,sn,date)
        self.ranges = []
        self.test()
        print(self.ranges)
        return

##        for r in self.ranges:
##            reg0 = re.findall('[0-9]+', r[0])
##            reg1 = re.findall('[0-9]+', r[1])
##            cBeg = int(reg0[0])
##            rBeg = int(reg0[1])
##            cEnd = int(reg1[0])
##            rEnd = int(reg1[1])

##            for n in self.spanRanges:
##                span = re.findall('[0-9]+', n)
##                if (c >= n[0] and c <= n[2]) and (r >= n[1] and r <= n[3]):
##                    return
##            self.spanRanges.append(str(cBeg)+'@'+str(rBeg)+'@'+str(cEnd)+'@'+str(rEnd))
##            if (c >= cBeg and c <= cEnd) and (r >= rBeg and r <= rEnd):
##                return
        cD = rD = None
        for indexI, i in enumerate(template):
            if c >= indexI: continue
            if i != n:
                cD = indexI - 1
                print('cD = '+str(cD))
                break

##        for indexJ, j in enumerate(i):
##            print(j[cD])
##            if j[cD] != n:
##                rD = indexJ - 1
##                break
        if cD != None and rD != None:
            self.ranges.append([arrd,str(cD)+'@'+str(rD)])

    def findRange(self,n,cBeg,rBeg):
        template = tml.template
        #reg = re.findall('[0-9]+', addr)
        cEnd = rEnd = None
        for col, i in enumerate(template):
            if col < cBeg:
                continue
            if rEnd == None:
                for row, j in enumerate(i):
                    if row < rBeg:
                        continue
                    if j != n:
                        rEnd = row-1
                        break
            if i != n:
                cEnd = col-1
                self.ranges.append(str(cBeg) + '@' + str(rBeg) + '@' + str(cEnd) + '@' + str(rEnd))
                break

    def test(self):
        self.ranges = []
        template = tml.template
        currSpan = None
        rEnd = None

        for col, i in enumerate(template):
            for row, j in enumerate(i):
                if j > 1:
                    if currSpan == None:
                        find = False
                        if len(self.ranges) != 0:
                            for k in self.ranges:
                                reg = re.findall('[0-9]+', k)
                                if col >= int(reg[0]) and col <= int(reg[2]):
                                    if row >= int(reg[1]) and row >= int(reg[3]):
                                        find = True
                                        break
                            if not find:
                                continue
                        currSpan = j
                        cBeg = col
                        rBeg = row
                        print(j)
                        self.findRange(j,cBeg,rBeg)
                        currSpan = None
                        break








##                    if currSpan == 0:
##                        currSpan = j
##                        #adrBeg = str(c)+'@'+str(r)
##                    if j != currSpan:
##                        r = r-1
##                        break
##            if i[r] != currSpan:
##                addr = str(c-1)+'@'+str(r)
##                currSpan = 0
##                break
##        print(j,addr)
##        self.findRange(j,addr)
##
##        print(self.ranges)
        return#RETURN

        doc = SimpleDocTemplate("test_report_lab.pdf",pagesize=A4, rightMargin=15,leftMargin=15, topMargin=15,bottomMargin=18)
        data     = []
        row      = []
        currStyle= []
        elements = []
        tWeight  = [28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,28]
        print(sum(tWeight))

        c = 0
        r = 0



        for i in template:
            for j in i:
                if 'RD' in str(j):
                    reg = re.findall('[0-9]+',str(j))
                    right = int(reg[0])
                    down  = int(reg[1])
                    currStyle.append(('SPAN',(c,r),(c+right-1,r+down-1)),)
                    continue
                if j == 1:
                    currStyle.append(('BOX', (c,r), (c,r), 0.25, colors.black),)
                    currStyle.append(('INNERGRID',(c,r), (c,r), 0.25, colors.black),)
                if j > 1:
                    currStyle.append(('SPAN',(c,r),(c+j-1,r)),)
                if j == 0:
                    currStyle.append(('INNERGRID',(c,r), (c,r), 0.25, colors.white),)
                row.append(str(r) + str(c))
                c +=1
            data.append(row)
            row = []
            c = 0
            r += 1



        print(currStyle)

        t=Table(data,colWidths=tWeight,style=currStyle)
        elements.append(t)
        doc.build(elements)

    def createTemplate(self):
        rows     = 40
        columns  = 20
        template = []
        tmp      = []

        for r in range(0,rows+1,1):
            for c in range(0,columns+1,1):
                if r == 21:
                    if c == 0:
                        tmp.append('RD1@2')
                        c += 1
                        tmp.append('RD5@2')
                        c += 5
                        tmp.append('RD1@2')
                        c += 1

                if r <= 20:
                    tmp.append(0)
                else:
                    tmp.append(1)
            template.append(tmp)
            tmp = []
        return(template)


    def generateReport(self,parent,sn,date):
        doc = SimpleDocTemplate("test_report_lab.pdf",pagesize=A4, rightMargin=15,leftMargin=15, topMargin=15,bottomMargin=18)
##        doc.pagesize = landscape(A4)
        nameColumn = ('#','Test','','Min','Max','D/L','U/L','Remarks')
        elements = []
        data = []
        tmp = []
        fillData = {'03':'S/N:','13':sn,'14':'Freq. band U/L:','24':'ul','15':'Freq. band D/L:','25':'dl','118':"DSA's",'218':'DSA1 (dB)','219':'DSA2 (dB)','220':'DSA3 (dB)'}
        fillData.update({'112':'RFB Current at 6.5VDC (A)','113':'RF to IF Gain (dB), PIN -10dBm','114':'RF to IF Flatness (dBp-p)','115':'RF to RF Gain (dB)'})
        fillData.update({'116':'RF to RF Flatness (dBp-p)','117':'Return Loss RF In UL J9, DL J8 (dB)','121':'Intermodulation\nat POUT = 0dBm comp.\n-3dBm per tone (dBc)'})
        fillData.update({'122':'BIT Alarm ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“ Set the IF\nvalue to 1.2GHz','123':'ALC IN Validation (dBm)','124':'ALC OUT Validation (dBm)'})
        for i in range(0,26,1):
            for j in range(0,8,1):
                currCell = str(j)+str(i)
                if currCell in fillData.keys():
                    tmp.append(fillData.get(currCell))
                elif int(currCell) in range(12,26,1):
                    tmp.append(int(currCell)-11)
                else:
                    tmp.append(currCell)
            if i == 11:
                data.append(nameColumn)
            else:
                data.append(tmp)
            tmp = []
        #TODO: Get this line right instead of just copying it from the docs

        tWeight = [25,75,65,65,65,65,65,135]

        print(sum(tWeight))

        t=Table(data,colWidths=tWeight,style=[('SIZE', (0,0), (-1,-1), 8),
                            ('ALIGN',(0,11),(-1,-1),'CENTER'),
                            ('VALIGN',(0,11),(-1,-1),'MIDDLE'),
                            ('SPAN',(2,0),(6,0)),
                            ('SPAN',(2,1),(6,1)),
                            ('SPAN',(2,2),(6,2)),
                            ('SPAN',(1,11),(2,11)),
                            ('SPAN',(1,12),(2,12)),
                            ('SPAN',(1,13),(2,13)),
                            ('SPAN',(1,14),(2,14)),
                            ('SPAN',(1,15),(2,15)),
                            ('SPAN',(1,16),(2,16)),
                            ('SPAN',(1,17),(2,17)),

                            ('SPAN',(0,18),(0,20)),
                            ('SPAN',(1,18),(1,20)),

                            ('SPAN',(1,21),(2,21)),
                            ('SPAN',(1,22),(2,22)),
                            ('SPAN',(1,23),(2,23)),
                            ('SPAN',(1,24),(2,24)),
                            ('SPAN',(1,25),(2,25)),
                            ('SPAN',(1,26),(2,26)),

                            ('ALIGN',(1,12),(2,25),'LEFT'),


                            ('BOX', (2,0), (6,2), 0.25, colors.black),
                            ('INNERGRID', (2,0), (6,2), 0.25, colors.black),
                            ('BOX', (0,11), (-1,-1), 0.25, colors.black),
                            ('INNERGRID', (0,11), (-1,-1), 0.25, colors.black),
                            ])

        print(t)
##        style = TableStyle([('ALIGN',(1,1),(0,0),'CENTER'),
##                            ('SIZE', (1,1), (0,0), 8),
##                            ('TEXTCOLOR',(1,1),(-2,-2),colors.red),
##                            ('VALIGN',(0,0),(0,-1),'CENTER'),
##                            ('TEXTCOLOR',(0,0),(0,-1),colors.blue),
##                            ('ALIGN',(0,-1),(-1,-1),'CENTER'),
##                            ('VALIGN',(0,-1),(-1,-1),'MIDDLE'),
##                            ('TEXTCOLOR',(0,-1),(-1,-1),colors.green),
##                            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
##                            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
##                            ])

##        #Configure style and word wrap
##        s = getSampleStyleSheet()
##        s = s["BodyText"]
##        s.wordWrap = 'CJK'
##        data2 = [[Paragraph(cell, s) for cell in row] for row in data]
##        t=Table(data2)


        #Send the data and build the file
        elements.append(t)
        doc.build(elements)
##        os.startfile(doc)



