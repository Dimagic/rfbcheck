import sqlite3
from sqlite3 import Error

class Dbconnection():
    def __init__(self):
        try:
            self.conn = sqlite3.connect("rfb.db")
            self.cur = self.conn.cursor()
        except Error as e:
            print(e)

    def sendQuery(self,query):
        cur = self.conn.cursor()
        cur.execute(query)
        cur.fetchall()

    def writeQuery(self, qwery):
        cur = self.conn.cursor()
        cur.execute(query)
        cur.commit()
