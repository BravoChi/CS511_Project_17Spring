import subprocess
import json
import os
import sys
import re
import sqlite3
import numpy as np
from datetime import datetime

sys.setrecursionlimit(100000)

arg = sys.argv
# read twitter file
totalLine = 3
linecounter=0

conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()

try:
	c.execute("CREATE TABLE observation_nodes (id integer,node text)")
except BaseException as e:
	print(e)
	# read url

def insertObservationNodes(node):
	params = []
	params.append(node['id'])
	params.append(node['node'])
	c = conn.cursor()
	c.execute("INSERT INTO observation_nodes VALUES (?,?)",params)


# load url vocabulary
urlVocabs = c.execute("SELECT b.id,a.date,a.url from clusterurl a,observation_nodes b where b.node=a.domain")
vocabs = {}
for urlvocab in urlVocabs:
	if urlvocab[2] not in vocabs:
		vocabs[urlvocab[2]] = {'node': urlvocab[0],'date':urlvocab[1]}
	else:
		if urlvocab[1] < vocabs[urlvocab[2]]['date']:
			vocabs[urlvocab[2]] = {'node': urlvocab[0],'date':urlvocab[1]}	

# load nodes id
nodesId = {}
nodeVocab = c.execute("SELECT id, node from observation_nodes")
for myNode in nodeVocab:
	if myNode[1] not in nodesId:
		nodesId[myNode[1]] = myNode[0]
		with open('nodes-file.txt','a') as nodesFile:
			nodesFile.write('{},{}\n'.format(myNode[0],myNode[1]))


# write nodes
# following nodes
# row[0] follow row[1]
"""
edges = c.execute("SELECT distinct (select b.id from observation_nodes b where a.domaina=b.node) as nodea,(select b.id from observation_nodes b where a.domainb=b.node) as nodeb from observation_cascades a")
nodes = {}
for edge in edges:
	with open('nodes-file.txt','a') as nodesFile:
		if edge[0] not in nodes:
			nodes[edge[0]] = 1
			nodesFile.write('{}\n'.format(edge[0]))
		if edge[1] not in nodes:
			nodes[edge[1]] = 1
			nodesFile.write('{}\n'.format(edge[1]))

	with open('edges-file.txt','a') as edgesFile:
		edgesFile.write(json.dumps([edge[0],edge[1]])+'\n')
"""
# make edges from 3hops data
casRows = c.execute("SELECT cascade from edge_hops where count=2")
nodes = {}
for casRow in casRows:
	myCases = json.loads(casRow[0])
	#print(myCas)
	for myCas in myCases:
		edge = [myCas['cascades'][1][1],myCas['cascades'][1][0]]

		"""
		with open('nodes-file.txt','a') as nodesFile:
			if edge[0] not in nodes:
				nodes[edge[0]] = 1
				nodesFile.write('{}\n'.format(edge[0]))
			if edge[1] not in nodes:
				nodes[edge[1]] = 1
				nodesFile.write('{}\n'.format(edge[1]))
		"""			

		with open('edges-file.txt','a') as edgesFile:
			edgesFile.write(json.dumps([nodesId[edge[0]],nodesId[edge[1]]])+'\n')

# get cascades from observation cascades
urlbRows = c.execute("SELECT distinct urlb from observation_cascades")

cascades = {}

cascadeCount = 0
# maximum time for scaling to 1
maxTime = 0
arrTime = []
# use mean time for define recuring cascades 5751721
# about 3 month, otherwise we treat it as recurring matrix
meanTime = 5751721
for urlb in urlbRows:
	c1 = conn.cursor()	
	finishTrace = False
	myArr = []
	# to track recurrence, don't look back
	domainHist = []
	i = 0
	length = 0

	# get vocab
	"""
	if urlb[0] in vocabs:
		myvocab = vocabs[urlb[0]]
		myDate = datetime.strptime(myvocab['date'],'%Y-%m-%d %H:%M:%S').timestamp()
		startDate = myDate
		cascadeTime = myDate - startDate
		myArr.append({'node': myvocab['node'],'time': cascadeTime,'date': myvocab['date'],'text': ''})
		i = 1
	else:
		print('not found {}'.format(urlb))
	"""

	#while not finishTrace:
	#	print('length: {}'.format(length))
	cascadeRows = c1.execute('SELECT distinct (select b.id from observation_nodes b where a.domaina=b.node) as nodeid, date,memetext from observation_cascades a where urlb=? order by date asc',[urlb[0]])	
	#	j = 0
	for cascade in cascadeRows:
		# skip if j < length
		#if j<length:
		#	print('skip')
		#	j+=1
		#	continue
		#else:
		#	j+=1
		length+=1
		# lines read
		myDate = datetime.strptime(cascade[1],'%Y-%m-%d %H:%M:%S').timestamp()
		if i == 0:
			startDate = myDate
		cascadeTime = myDate - startDate
		# break early if the time reach its meantime
		if cascadeTime > meanTime or cascade[0] in domainHist:
			if i>1 :
				#if maxTime < myArr[len(myArr)-1]['time']:
				#	maxTime = myArr[len(myArr)-1]['time']
				arrTime.append(myArr[len(myArr)-1]['time'])
				cascades[cascadeCount] = {'casid': cascadeCount,'url': urlb[0],'cas': myArr,'cascount': i}
				cascadeCount+=1		
			# will the last item eligible to be the first one for reccurence
			firstCas = myArr[len(myArr)-1].copy();
			startDate = datetime.strptime(firstCas['date'],'%Y-%m-%d %H:%M:%S').timestamp()
			# reset count
			myArr = []
			domainHist = []
			i = 0
			# if because of domain reccurence
			if cascade[0] in domainHist or cascade[0]==firstCas['node'] or (myDate-startDate) > meanTime:
				startDate = myDate
				cascadeTime = myDate - startDate
				myArr.append({'node': cascade[0],'time': cascadeTime,'date': cascade[1],'text': cascade[2]})
				domainHist.append(cascade[0])
				i+=1
			else:
			# because of average time
				# add 2 latest cascades
				startDate = datetime.strptime(firstCas['date'],'%Y-%m-%d %H:%M:%S').timestamp()
				firstCas['time']=0
				myArr.append(firstCas)
				domainHist.append(firstCas['node'])
				i+=1
				cascadeTime = myDate - startDate
				myArr.append({'node': cascade[0],'time': cascadeTime,'date': cascade[1],'text': cascade[2]})
				domainHist.append(cascade[0])					
				i+=1

			print('{} {} {}'.format(urlb[0],i,cascadeTime))				
			print('reach meanTime, break {}'.format(length))
			#continue
		else:
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
npTime = np.array(arrTime)
# statistics
# max: 23535667.0, mean: 5751721.358078603, med: 998713.0, sd: 7132129.177352756

# from the mean
#max: 5747131.0, mean: 642810.7051022825, med: 79388.0, sd: 1230498.8523700857


print('max: {}, mean: {}, med: {}, sd: {}'.format(np.max(npTime),np.mean(npTime),np.median(npTime),np.std(npTime)))
maxTime = np.max(npTime)

# scale up time
for i in range(cascadeCount):
	for mycas in cascades[i]['cas']:
		mycas['timescale'] = mycas['time'] / maxTime
	with open('cascade-file.txt','a') as casfile:
		casfile.write(json.dumps(cascades[i])+'\n')	




#		with open('cascade-file.txt','a') as casfile:
#			casfile.write(json.dumps({'casid': cascadeCount,'url': urlb[0],'cas': myArr,'cascount': i})+'\n')	
