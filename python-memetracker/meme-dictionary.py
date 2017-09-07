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
	c.execute("CREATE TABLE nodes (domain,type)")
	c.execute("CREATE TABLE url (url,date)")
except BaseException as e:
	print(e)

def insertNodes(node):
	params = []
	params.append(node['domain'])
	params.append(node['type'])
	c = conn.cursor()
	c.execute("INSERT INTO nodes VALUES (?,?)",params)

def insertUrl(url):
	params = []
	params.append(url['url'])
	params.append(url['date'])
	c = conn.cursor()
	c.execute("INSERT INTO url VALUES (?,?)",params)

def insertEdges(edge):
	params = []
	params.append(edge['domain']['username'])
	params.append(edge['range']['username'])
	params.append(json.dumps(edge))
	c = conn.cursor()
	c.execute("INSERT INTO edges VALUES (?,?,?)",params)

def insertCascadeId(cascadeid,url):
	params=[]
	params.append(cascadeid)
	params.append(url)
	c = conn.cursor()	
	c.execute("INSERT INTO cascadeid VALUES (?,?)",params)

def insertCascadeHashId(cascadeid,hash):
	params=[]
	params.append(cascadeid)
	params.append(hash)
	c = conn.cursor()	
	c.execute("INSERT INTO cascadehashid VALUES (?,?)",params)

def insertCascade(cascade):
	for neighbor in cascade['edges']:
		params=[]
		params.append(cascade['casid'])
		params.append(cascade['username'])
		params.append(neighbor['range']['username'])
		params.append(cascade['url'])
		params.append(cascade['time'])
		params.append(cascade['text'])
		#params.append(json.dumps(cascade))
		c = conn.cursor()
		c.execute("INSERT INTO cascades VALUES (?,?,?,?,?,?)",params)

def insertCascadeHash(cascade):
	for neighbor in cascade['edges']:
		params=[]
		params.append(cascade['casid'])
		params.append(cascade['username'])
		params.append(neighbor['range']['username'])
		params.append(cascade['tag'])
		params.append(cascade['time'])
		params.append(cascade['text'])
		#print(cascade)
		#params.append(json.dumps(cascade))
		c = conn.cursor()
		c.execute("INSERT INTO cascadeshash VALUES (?,?,?,?,?,?)",params)


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

with open('clust-qt08080902w3mfq5.txt','r') as memes:
	for meme in memes:
		#split by tab
		memeSplit = meme.split('\t')
		if(len(memeSplit)==6):
			date = memeSplit[2]
			domainType = memeSplit[4]
			#print(memeSplit[5])
			domain = memeSplit[5].split('/')
			url = memeSplit[5].replace('\n','')
			if(len(domain)>2):
				domain = memeSplit[5].split('/')[2]
				if domain not in nodes:
					nodes[domain] = {'domain': domain,'type': domainType}
					insertNodes(nodes[domain])
				if url not in urls:
					urls[url] = {'url': url,'date': date}
					insertUrl(urls[url])
		if(counter>100000):
			conn.commit();
			print('commit')
			counter=0
		counter+=1
