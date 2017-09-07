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
with open('nodes.txt','r') as nodesFile:
	for node in nodesFile:
		nodeArr = node.replace('\n','').split(',')
		nodes.append(nodeArr[1])

# load edges from 3 hops
# for this edges we load the parent as index to capture followers
edges = {}
with open('edges.txt','r') as edgesFile:
	for edge in edgesFile:
		edgeJson = edge.replace('\n','').split(',')
		if edgeJson[1] not in edges.keys():
			edges[edgeJson[1]] = []
		edges[edgeJson[1]].append(edgeJson[0])


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

cascadeBag = {}
# fetch all node
for node in nodes:	
	# make bag for this node
	cascadeCount = 0
	cascades={}
	# fetch the cascade from node
	cascadeRows = c.execute("SELECT urlb,casid,date from observation_cascades_2 where ida=?",[node])
	# fetch all cascade
	for cascadeRow in cascadeRows:
		# second cursor to trace next cascade
		c1 = conn.cursor()	
		myArr = []
		# to track recurrence, don't look back
		domainHist = []
		i = 0
		length = 0
		print('{},{},{}'.format(cascadeRow[0],node,cascadeRow[1]))
		c2 = conn.cursor()
		urlVocabs = c2.execute("SELECT a.domain,a.date,a.url from clusterurl a where a.url=? order by date asc",[cascadeRow[0]])
		vocabRow = urlVocabs.fetchone();
		print('vocab: {}'.format(vocabRow))
		observationCasRows = c1.execute('SELECT ida, date, memetext from observation_cascades_2 a where urlb=? and date<=?  order by date asc',[cascadeRow[0],cascadeRow[2]])
		myCasTime = datetime.strptime(cascadeRow[2],'%Y-%m-%d %H:%M:%S').timestamp();
		if node in edges:
			#print('edges: {}'.format(edges[node]))
			for cascade in observationCasRows:
			#check if the cascade is the edge of x
			#print('{},{}'.format(cascade[0],cascade[1]))
				if node in edges:
					if cascade[0] in edges[node]:
						# lines read
						myDate = datetime.strptime(cascade[1],'%Y-%m-%d %H:%M:%S').timestamp()
						if myCasTime - myDate > meanTime:
							# if the time difference is more than observation time than go to next cascade
							continue
						startDate = myDate
						cascadeTime = myDate - startDate
						# break early if the time reach its meantime
						if cascadeTime > meanTime:	
							break
						# check reccurence
						# we don't handle reccurence right now
						# so if there is a reccurence simply skip the cascade
						if cascade[0] not in domainHist:
							myArr.append({'node': cascade[0],'time': cascadeTime,'date': cascade[1],'text': cascade[2]})
							print('{} {} {}'.format(urlb[0],i,cascadeTime))
							# tracking reccurence, don't look back
							domainHist.append(cascade[0])
							i+=1
			#finishTrace = True
		if i>1 :
			#if maxTime < myArr[len(myArr)-1]['time']:
			#	maxTime = myArr[len(myArr)-1]['time']
			#meanTime+=myArr[len(myArr)-1]['time']
			arrTime.append(myArr[len(myArr)-1]['time'])
			cascades[cascadeCount] = {'casid': cascadeCount,'url': urlb[0],'cas': myArr,'cascount': i}
	#		with open('cascade-file.txt','a') as casfile:
	#			casfile.write(json.dumps({'casid': cascadeCount,'url': urlb[0],'cas': myArr,'cascount': i})+'\n')	
			cascadeCount+=1

	for i in range(cascadeCount):
		for mycas in cascades[i]['cas']:
			# divide by meanTime
			mycas['timescale'] = mycas['time'] / meanTime
	with open('cascade-file-observation.txt','a') as casfile:
		casfile.write(json.dumps({'node':node,'cascades':cascades})+'\n')