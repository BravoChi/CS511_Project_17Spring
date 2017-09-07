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

# create related table
# nodes
try:
	c.execute("CREATE TABLE cluster_new (cid INTEGER,text)")
	c.execute("CREATE TABLE clusterurl_new (cid INTEGER,date,type,domain,url TEXT)")
	#c.execute("CREATE INDEX clusterurl_url ON clusterurl(url)")
	#c.execute("CREATE INDEX cluster_cid ON cluster(cid)")
except BaseException as e:
	print(e)

def insertCluster(cluster):
	params = []
	params.append(cluster['cid'])
	params.append(cluster['text'])
	c = conn.cursor()
	c.execute("INSERT INTO cluster_new VALUES (?,?)",params)

def insertClusterUrl(url):
	params = []
	params.append(url['cid'])	
	params.append(url['date'])
	params.append(url['type'])
	params.append(url['domain'])
	params.append(url['url'])
	c = conn.cursor()
	c.execute("INSERT INTO clusterurl_new VALUES (?,?,?,?,?)",params)


#counterfile = open('counter.txt','a')


"""
nodesfile = open('nodes.txt','a')
edgesfile = open('edges.txt','a')
cascadeidfile = open('cascadeid.txt','a')
cascadehashfile = open('cascadehashid.txt','a')
"""

cascadeid = 0
cascadehashid = 0

def uniqfy(seq):
   # not order preserving   
   return list(set(seq))


counter = 0
cid = 1

with open('clust-qt08080902w3mfq5.txt','r') as memes:
	for meme in memes:
		#split by tab
		memeSplit = meme.split('\t')
		if(len(memeSplit)==5):
			insertCluster({'cid': cid,'text': memeSplit[3]})
			cid+=1

		if(len(memeSplit)==6):
			date = memeSplit[2]
			domainType = memeSplit[4]
			#print(memeSplit[5])
			domain = memeSplit[5].split('/')
			url = memeSplit[5].replace('\n','')
			if(len(domain)>2):
				domain = memeSplit[5].split('/')[2]
				insertClusterUrl({'cid': cid,'date': memeSplit[2],'type': memeSplit[4], 'domain': domain,'url': url})
				"""
				if domain not in nodes:
					nodes[domain] = {'domain': domain,'type': domainType}
					insertNodes(nodes[domain])
				if url not in urls:
					urls[url] = {'url': url,'date': date}
					insertUrl(urls[url])
				"""
		if(counter>100000):
			conn.commit();
			print('commit')
			counter=0
		counter+=1
