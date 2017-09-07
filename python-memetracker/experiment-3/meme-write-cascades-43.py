import subprocess
import json
import os
import sys
import re
import sqlite3
import numpy as np
from datetime import datetime

sys.setrecursionlimit(100000)

conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()

arg = sys.argv
# read twitter file
totalLine = 3
linecounter=0

# load nodes
nodes = []
nodesHash = {}
with open('nodes.txt','r') as nodesFile:
	for node in nodesFile:
		nodeArr = node.replace('\n','').split(',')
		nodes.append(nodeArr[1])
		nodesHash[nodeArr[0]] = nodeArr[1]

# load edges from 3 hops
# for this edges we load the parent as index to capture followers
edges = {}
with open('edges.txt','r') as edgesFile:
	for edge in edgesFile:
		edgeJson = edge.replace('\n','').split(',')
		if edgeJson[1] not in edges.keys():
			edges[edgeJson[1]] = []
		edges[edgeJson[1]].append(edgeJson[0])

observNodes = []
observRow = c.execute("SELECT ida from temp_observ order by ida asc")
for observ in observRow:
	observNodes.append(observ[0])


# we will write cascades based on three hopes nodes to minimize the workload on
# predicting transmission rates
# because we interested in the predicting transmission between edges
# we follow the cascade as
# - first, select cascade from child = x
# - get the same cascade from other child nodes that are neighbor of x and have time
#	span mode than x
# - we use 30 days as the time observation window
# - put it in cascade bag
meanTime = 2505600
arrTime = []

# fetch all node
myCount = 0
for node in observNodes:	
	# make bag for this node
	myCount+=1
	cascadeCount = 0
	cascades=[]
	# fetch the cascade from node
	cascadeRows = c.execute("SELECT urlb,casid,date,memetext from observation_cascades_2 where ida=?",[node])
	print('{},{}'.format(myCount,node))
	# fetch all cascade
	for cascadeRow in cascadeRows:
		# second cursor to trace next cascade
		c1 = conn.cursor()	
		myArr = []
		# to track recurrence, don't look back
		domainHist = []
		i = 0
		length = 0
		#print('{},{},{}'.format(cascadeRow[0],node,cascadeRow[1]))
		c2 = conn.cursor()
		urlVocabs = c2.execute("SELECT a.domain,a.date,a.url from clusterurl a where a.url=? order by date asc",[cascadeRow[0]])
		vocabRow = urlVocabs.fetchone();
		#print('vocab: {}'.format(vocabRow))
		startDate = datetime.strptime(vocabRow[1],'%Y-%m-%d %H:%M:%S').timestamp()
		myArr.append({'node': nodesHash[vocabRow[0]],'time': 0,'date': vocabRow[1],'text': ''})
		i+=1
		myDate = datetime.strptime(cascadeRow[2],'%Y-%m-%d %H:%M:%S').timestamp()
		cascadeTime = myDate - startDate
		if cascadeTime > 0 and cascadeTime < meanTime :
			myArr.append({'node': node,'time': cascadeTime,'date': cascadeRow[2],'text': cascadeRow[3]})
			i+=1
			if i>1 :
				arrTime.append(myArr[len(myArr)-1]['time'])
				cascades.append({'casid': cascadeCount,'url': cascadeRow[0],'cas': myArr,'cascount': i})
				cascadeCount+=1

	for i in range(cascadeCount):
		for mycas in cascades[i]['cas']:
			# divide by meanTime
			mycas['timescale'] = mycas['time'] / meanTime
	with open('cascade-file-observation.txt','a') as casfile:
		casfile.write(json.dumps({'node':node,'cascades':cascades})+'\n')