import subprocess
import json
import os
import sys
import re
import sqlite

arg = sys.argv
# read twitter file
totalLine = 3
nodes = {}
edges = {}
cascades = {}
cascadestag = {}

nodesfile = open('nodes.txt','a')
edgesfile = open('edges.txt','a')
cascadeidfile = open('cascadeid.txt','a')
cascadehashfile = open('cascadehashid.txt','a')

userRegex = re.compile('@[a-zA-Z_0-9]*')
hashtagRegex = re.compile('#[a-zA-Z_0-9]*')
urlRegex = re.compile('http://[^ ]*')

cascadeid = 0
cascadehashid = 0

def uniqfy(seq):
   # not order preserving
   set = {}
   map(set.__setitem__, seq, [])
   return set.keys()


with open('tweets2009-06.tweet','r') as tweets:
	# write log for tweets
	readLog = open('read.log','a')
	# first line is number of tweets
	tweets.readline()
	line =0
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
				nodesfile.writelines(json.dumps(nodes[usernameNoCase])+'\n')

			# get edges
			myedges = userRegex.findall(text)
			myedgeArr = []
			for edge in myedges:
				# exclude @ from the first char
				edge = edge[1:len(edge)]
				#print(edge)
				edgeNoCase = edge.lower()
				if edge not in edges.keys():
					if edgeNoCase not in nodes.keys():
						nodes[edgeNoCase] = {'username': edgeNoCase, 'usernameo': edge}
						nodesfile.writelines(json.dumps(nodes[edgeNoCase])+'\n')
					if usernameNoCase not in edges.keys():
						edges[usernameNoCase] = {}
						if edgeNoCase not in edges[usernameNoCase]:
							edgeDoc = {}
							edgeDoc['domain'] = { 'username': usernameNoCase, 'usernameo': username}
							edgeDoc['range'] = { 'username': edgeNoCase, 'usernameo': edge}
							edges[usernameNoCase][edgeNoCase] = edgeDoc
							myedgeArr.append(edgeDoc)
							edgesfile.writelines(json.dumps(edges[usernameNoCase][edgeNoCase])+'\n')

			# get cascade url
			urls = uniqfy(urlRegex.findall(text))
			for url in urls:
				if url not in cascades.keys():
					cascadeid+=1
					cascades[url] = cascadeid
					cascadeidfile.writelines('{} {}\n'.format(cascadeid,url))
				with open('cas-'+str(cascades[url])+'.txt','a') as casfile:
					cas = {'username': usernameNoCase,'text': text,'time':date,'edges':myedgeArr}
					casfile.writelines(json.dumps(cas)+'\n')

			hashtags = uniqfy(hashtagRegex.findall(text))
			for hashtag in hashtags:
				#print(hashtag)
				hashtago = hashtag
				hashtag = hashtag[1:len(hashtag)]
				if hashtag not in cascadestag.keys():
					cascadehashid+=1
					cascadestag[hashtag] = cascadehashid
					cascadehashfile.writelines('{} {}\n'.format(cascadehashid,hashtago))
				with open('hash-'+str(cascadestag[hashtag])+'.txt','a') as casfile:
					cas = {'username': usernameNoCase,'text': text,'time':date,'url': urls,'edges':myedgeArr}
					casfile.writelines(json.dumps(cas)+'\n')						


			# reset line
			line =-1
			tweetArr = []			
		line+=1
