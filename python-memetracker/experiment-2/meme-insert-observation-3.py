import subprocess
import json
import os
import sys
import re
import sqlite3

sys.setrecursionlimit(100000)

arg = sys.argv
# read twitter file
totalLine = 3
linecounter=0

conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()

try:
	c.execute("CREATE TABLE observation_cascades_2 (ida integer,idb integer,domaina text,domainb text,urla text,urlb text,date,memetext,casid integer)")
except BaseException as e:
	print(e)
	# read url

# load nodes id
nodesId = {}
nodeVocab = c.execute("SELECT id, node from observation_nodes_2")
for myNode in nodeVocab:
	if myNode[1] not in nodesId:
		nodesId[myNode[1]] = myNode[0]


def insertObservationCas(cas):
	params = []
	params.append(cas['ida'])
	params.append(cas['idb'])
	params.append(cas['domaina'])
	params.append(cas['domainb'])
	params.append(cas['urla'])
	params.append(cas['urlb'])
	params.append(cas['date'])
	params.append(cas['memetext'])
	params.append(cas['casid'])
	c = conn.cursor()
	c.execute("INSERT INTO observation_cascades_2 VALUES (?,?,?,?,?,?,?,?,?)",params)

# get nodes that has more than 3 hops

j = 0
for node in nodesId.keys():
	"""
	print(j)	
	if j <  44588:
		j+=1
		continue
	"""
	rowsCas = c.execute("SELECT DOMAINA,DOMAINB,URLA,URLB,DATE,MEMETEXT,CASID FROM CASCADES A WHERE DOMAINB = ?",[node])
	for myRowCas in rowsCas:
		# check if it is in observation cascades
		if myRowCas[0] in nodesId.keys():
			insertObservationCas({'ida': nodesId[myRowCas[0]],'idb': nodesId[myRowCas[1]],'domaina':myRowCas[0],'domainb':myRowCas[1],'urla':myRowCas[2],'urlb':myRowCas[3],'date':myRowCas[4],'memetext':myRowCas[5],'casid':myRowCas[6]})
	j+=1
	if j>500:
		conn.commit();
		j=0


conn.commit();