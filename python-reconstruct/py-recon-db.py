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
edges = {}
cascades = {} 
cascadestag = {}

conn = sqlite3.connect('reconstruct.sqlite');
conn.text_factory = str

c = conn.cursor()
#define cursor

# create related table
# nodes
c.execute("CREATE TABLE nodes (username,usernameo,userlink,object)")
c.execute("CREATE TABLE edges (domainname,rangename,object)")
c.execute("CREATE TABLE cascadeid (casid INTEGER,url)")
c.execute("CREATE TABLE cascadehashid (casid INTEGER,hashtag)")
#c.execute("CREATE TABLE cascades (casid INTEGER,username,neighborname,url,tweettime,tweettext,object)")
#c.execute("CREATE TABLE cascadeshash (casid INTEGER,username,neighborname,tag,tweettime,tweettext,object)")
c.execute("CREATE TABLE cascades (casid INTEGER,username,neighborname,url,tweettime,tweettext)")
c.execute("CREATE TABLE cascadeshash (casid INTEGER,username,neighborname,tag,tweettime,tweettext)")
c.execute('CREATE  INDEX "main"."cascades_casid" ON "cascades" ("casid" ASC)')
c.execute('CREATE  INDEX "main"."cascadeid_casid" ON "cascadeid" ("casid" ASC)')
c.execute('CREATE  INDEX "main"."cascadeshash_casid" ON "cascadeshash" ("casid" ASC)')
c.execute('CREATE  INDEX "main"."cascadehashid_casid" ON "cascadehashid" ("casid" ASC)')

def insertNodes(node):
	params = []
	params.append(node['username'])
	params.append(node['usernameo'])
	params.append(node['userlink'])
	params.append(json.dumps(node))
	c = conn.cursor()
	c.execute("INSERT INTO nodes VALUES (?,?,?,?)",params)

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

userRegex = re.compile('@[a-zA-Z_0-9]+')
hashtagRegex = re.compile('#[a-zA-Z_0-9]+')
urlRegex = re.compile('http://[^ ]*')

cascadeid = 0
cascadehashid = 0

def uniqfy(seq):
   # not order preserving   
   return list(set(seq))


with open('tweets2009-06.tweet','r') as tweets:
	# write log for tweets
	#readLog = open('read.log','a')
	# first line is number of tweets
	tweets.readline()
	line =0
	counter = 0
	tweetArr = []
	for tweet in tweets:
		tweetArr.append(tweet)
		if line >= totalLine:
			date = tweetArr[0].replace('T\t','').replace('\n','')
			node = tweetArr[1].replace('U\t','').replace('\n','')
			text = tweetArr[2].replace('W\t','').replace('\n','')
			#print(date)
			#print(node)
			#print(text)
			# get username
			splitNode = node.split('/');
			username = splitNode[len(splitNode)-1]
			usernameNoCase = username.lower()
			if usernameNoCase not in nodes.keys():
				#print(usernameNoCase)
				nodes[usernameNoCase] = {'username': usernameNoCase, 'usernameo': username, 'userlink': node}
				#nodesfile.writelines(json.dumps(nodes[usernameNoCase])+'\n')
				insertNodes(nodes[usernameNoCase])

			# get edges
			myedges = userRegex.findall(text)
			myedgeArr = []
			for edge in myedges:
				# exclude @ from the first char
				edge = edge[1:len(edge)]
				#print(edge)
				edgeNoCase = edge.lower()
#				if edge not in edges.keys():
				if edgeNoCase not in nodes.keys():
					nodes[edgeNoCase] = {'username': edgeNoCase, 'usernameo': edge, 'userlink': ''}
					#nodesfile.writelines(json.dumps(nodes[edgeNoCase])+'\n')
					insertNodes(nodes[edgeNoCase])
				if usernameNoCase not in edges.keys():
					edges[usernameNoCase] = {}
				if usernameNoCase!=edgeNoCase:
					if edgeNoCase not in edges[usernameNoCase]:
						edgeDoc = {}
						edgeDoc['domain'] = { 'username': usernameNoCase, 'usernameo': username}
						edgeDoc['range'] = { 'username': edgeNoCase, 'usernameo': edge}						
						edges[usernameNoCase][edgeNoCase] = edgeDoc
						#edgesfile.writelines(json.dumps(edges[usernameNoCase][edgeNoCase])+'\n')
						insertEdges(edges[usernameNoCase][edgeNoCase])
						#print(edges[usernameNoCase][edgeNoCase])
#				print(text)
#				print('d : '+usernameNoCase)
#				print('r : '+edgeNoCase)
				if usernameNoCase!=edgeNoCase:
					myedgeArr.append(edges[usernameNoCase][edgeNoCase])

			# get cascade url
			#print(urlRegex.findall(text))
			urls = uniqfy(urlRegex.findall(text))
			for url in urls:
				if url not in cascades.keys():
					cascadeid+=1
					cascades[url] = cascadeid
					#cascadeidfile.writelines('{} {}\n'.format(cascadeid,url))
					insertCascadeId(cascadeid,url)

				#with open('cas-'+str(cascades[url])+'.txt','a') as casfile:
				cas = {'casid': cascades[url],'username': usernameNoCase,'url': url,'text': text,'time':date,'edges':myedgeArr}
				#	casfile.writelines(json.dumps(cas)+'\n')
				insertCascade(cas)	
				#print(json.dumps(cas))

			hashtags = uniqfy(hashtagRegex.findall(text))
			#print(hashtags)
			for hashtag in hashtags:
				#print(hashtag)
				hashtago = hashtag
				hashtag = hashtag[1:len(hashtag)]
				if hashtag not in cascadestag.keys():
					cascadehashid+=1
					cascadestag[hashtag] = cascadehashid
					#cascadehashfile.writelines('{} {}\n'.format(cascadehashid,hashtago))
					insertCascadeHashId(cascadehashid,hashtag)
				#with open('hash-'+str(cascadestag[hashtag])+'.txt','a') as casfile:
				cas = {'casid': cascadestag[hashtag],'username': usernameNoCase,'tag': hashtag,'text': text,'time':date,'url': urls,'edges':myedgeArr}
				#	casfile.writelines(json.dumps(cas)+'\n')						
				insertCascadeHash(cas)


			# reset line
			line =-1
			tweetArr = []			
		line+=1
		if (counter >= 1000000):
			conn.commit();
			#counterfile.flush()
			#print('commit ')
			print(linecounter)
			counter = 0
		counter+=1
		linecounter+=1
		#counterfile.writelines(str(linecounter)+'\n')
