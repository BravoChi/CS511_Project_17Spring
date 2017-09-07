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

# get cascades from observation cascades
urlbRows = c.execute("SELECT distinct urlb from observation_cascades_2")

cascades = {}

cascadeCount = 0
# maximum time for scaling to 1
maxTime = 0
arrTime = []
# use mean time for define recuring cascades 5751721
# about 3 month, otherwise we treat it as recurring matrix
# meanTime = 5751721
# using recurring cascades is hard, we can't infer anything
# therefore we used fixed time window 1 month (30 days)
# after that time window we infer that there is no cascade
meanTime = 2505600
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
	cascadeRows = c1.execute('SELECT distinct ida, date,memetext from observation_cascades_2 a where urlb=? order by date asc',[urlb[0]])
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
		# divide by meanTime
		mycas['timescale'] = mycas['time'] / meanTime
	with open('cascade-file.txt','a') as casfile:
		casfile.write(json.dumps(cascades[i])+'\n')	


#		with open('cascade-file.txt','a') as casfile:
#			casfile.write(json.dumps({'casid': cascadeCount,'url': urlb[0],'cas': myArr,'cascount': i})+'\n')	
