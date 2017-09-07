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
	# read url
	rows = c.execute('SELECT * from url')
	for row in rows:
		urls[row[0]] = True

try:
	c.execute("CREATE TABLE edges (domaina,domainb)")
	c.execute("CREATE TABLE cascades (urla,urlb,domaina,domainb,date,memetext)")
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
	params.append(edge['domaina'])
	params.append(edge['domainb'])
	c = conn.cursor()
	c.execute("INSERT INTO edges VALUES (?,?)",params)

def insertCascade(cascade):
	params=[]
	params.append(cascade['urla'])
	params.append(cascade['urlb'])
	params.append(cascade['domaina'])
	params.append(cascade['domainb'])
	params.append(cascade['date'])
	params.append(cascade['text'])
	c = conn.cursor()
	c.execute("INSERT INTO cascades VALUES (?,?,?,?,?,?)",params)

cascadeid = 0
cascadehashid = 0

def uniqfy(seq):
   # not order preserving   
   return list(set(seq))


counter = 0

with open('quotes_2009-04.txt','r') as memes:
	comments = []
	links = []
	page = ''
	time = ''
	oneMeme=False
	for meme in memes:
		#split by tab
		memeSplit = meme.split('\t')
		#print(memeSplit)
		if(len(memeSplit)>1):
			label = memeSplit[0]
			text = memeSplit[1].replace('\n','')

			if(label=='P'):
				page = text
			if(label=='Q'):
				comments.append(text)
			if(label=='L'):
				if(text in urls.keys()):
					links.append(text)
			if(label=='T'):
				time=text
		else:
			oneMeme=True

		if oneMeme:
			doc = {}
			doc['urla'] = page
			doc['domaina'] = page.split('/')[2]
			doc['date'] = time
			doc['text'] = ' '.join(comments)
			if len(comments) > 0:
				for link in links:
					doc['urlb'] = link
					doc['domainb'] = link.split('/')[2]
					if doc['domaina'] != doc['domainb']:
						print(doc)
						insertCascade(doc)

			comments = []
			links = []
			page = ''
			time = ''
			oneMeme=False

		if(counter>100000):
			conn.commit();
			print('commit')
			counter=0
		counter+=1
