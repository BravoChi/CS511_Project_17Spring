import subprocess
import json
import os
import sys
import re
import sqlite3

arg = sys.argv
# read twitter file
totalLine = 3
linecounter=0
nodes = {}
urls = {}
edges = {}
cascades = {} 
cascadestag = {}

conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()
#define cursor


cascadeid = 0
cascadehashid = 0

def uniqfy(seq):
   # not order preserving   
   return list(set(seq))


counter = 0
cid = 1

#rowsCas = c.execute("SELECT distinct domaina,domainb from edges")
rowsCas = c.execute("SELECT distinct urlb,urla from cascades order by date asc")

j = 0
k = 0
for row in rowsCas:
	j+=1
	k+=1
	print(j)
	c1 = conn.cursor()
	print(row[0])
	print(row[1])
	rows = c1.execute('SELECT cid from clusterurl where url = ? or url = ?',[row[0],row[1]])

	for row2 in rows:
		print(row2[0])
		c1.execute('UPDATE cascades set casid=? where urla=? and urlb=?',[row2[0],row[1],row[0]])
		break

	if k < 5000:
		conn.commit()
		k = 0


