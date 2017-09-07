import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import subprocess
import json
import os
import sys
import sqlite3

configjson = {}
arg = sys.argv
# read config file
with open(arg[1],'r') as configfile:
	for line in configfile:
		configjson = json.loads(line)

# setup api
auth = OAuthHandler(configjson['consumer_key'],configjson['consumer_secret'])
auth.set_access_token(configjson['access_token'],configjson['access_secret'])

api = tweepy.API(auth)
keywords = arg[3].split(',')
topic = arg[2]
# check if topic folder exist
if not os.path.exists(topic):
	os.makedirs(topic)
# change active directory to topic directory
os.chdir(topic)

# make database
conn = sqlite3.connect(topic+'.sqlite');
conn.text_factory = str

c = conn.cursor()
#define cursor

fileStream = {}
cascades = {}
edges = {}
nodes = {}
global cascadeid
cascadeid = 0
global counter
counter = 0

# create related table
# nodes
try:
	c.execute("CREATE TABLE nodes (userid TEXT,username TEXT)")
	c.execute("CREATE TABLE edges (userida TEXT,useridb TEXT)")
	c.execute("CREATE TABLE cascadeurlid (casid INTEGER,url TEXT)")
	# c.execute("CREATE TABLE cascadeid (casid INTEGER,hashtag)")
	#c.execute("CREATE TABLE cascades (casid INTEGER,username,neighborname,url,tweettime,tweettext,object)")
	#c.execute("CREATE TABLE cascadeshash (casid INTEGER,username,neighborname,tag,tweettime,tweettext,object)")
	c.execute("CREATE TABLE cascades (casid INTEGER,userida TEXT,useridb TEXT,tweettime TEXT,timestamp_ms INTEGER,tweettext TEXT)")
	#c.execute("CREATE TABLE cascadeshash (casid INTEGER,username,neighborname,tag,tweettime,tweettext)")
	c.execute('CREATE  INDEX "main"."nodes_id" ON "nodes" ("userid" ASC)')
	c.execute('CREATE  INDEX "main"."cascades_casid" ON "cascades" ("casid" ASC)')
	c.execute('CREATE  INDEX "main"."cascades_edge" ON "cascades" ("userida","useridb" ASC)')
	c.execute('CREATE  INDEX "main"."cascadeid_casid" ON "cascadeurlid" ("casid" ASC)')
	#c.execute('CREATE  INDEX "main"."cascadeshash_casid" ON "cascadeshash" ("casid" ASC)')
	#c.execute('CREATE  INDEX "main"."cascadehashid_casid" ON "cascadehashid" ("casid" ASC)')
except BaseException as e:
	# load all variables from database
	rowexec = c.execute('SELECT * FROM NODES');
	for row in rowexec:
		nodes[row[0]] = {'userid': row[0], 'username': row[1]}

	rowexec = c.execute('SELECT * FROM EDGES');
	for row in rowexec:
		if row[0] not in edges.keys():
			edges[row[0]] = {}
		if row[1] not in edges[row[0]]:
			edges[row[0]][row[1]] = {'userida': row[0], 'useridb': row[1]}

	rowexec = c.execute('SELECT * FROM CASCADEURLID');
	for row in rowexec:
		cascadeid+=1
		cascades[row[1]] = {'cascadeid': row[0],'url': row[1]}
	print(cascadeid)


# search
#twitterapi = api.search('twitter')
#tweet = api.user_timeline(screen_name='JustinMcElroy',count=200)
#print(tweet)
#tweets = api.statuses_lookup(id_=['76635000'])
#print(tweets)
#print(twitterapi)
#print(len(twitterapi))


def insertNodes(node):
	params = []
	params.append(node['userid'])
	params.append(node['username'])
	c = conn.cursor()
	c.execute("INSERT INTO nodes VALUES (?,?)",params)

def insertEdges(edge):
	params = []
	params.append(edge['userida'])
	params.append(edge['useridb'])
	c = conn.cursor()
	c.execute("INSERT INTO edges VALUES (?,?)",params)

def insertCascadeId(cascade):
	params=[]
	params.append(cascade['cascadeid'])
	params.append(cascade['url'])
	c = conn.cursor()	
	c.execute("INSERT INTO cascadeurlid VALUES (?,?)",params)

def insertCascade(cascade):
	for neighbor in cascade['edges']:
		params=[]
		params.append(cascade['casid'])
		params.append(cascade['userida'])
		params.append(neighbor['useridb'])
		params.append(cascade['time'])
		params.append(cascade['timestamp_ms'])
		params.append(cascade['text'])
		#params.append(json.dumps(cascade))
		c = conn.cursor()
		c.execute("INSERT INTO cascades VALUES (?,?,?,?,?,?)",params)


class MyListener(StreamListener):
	def on_data(self,data):
		try:
			jsondata = json.loads(data)
			ingest = False
			if 'lang' in jsondata.keys() and jsondata['lang']=='en':
				# we are interested in data that have cascade
				# expanded_url, user_mentions, retweeted_status, quoted_status, in_reply_to_status_id
				if len(jsondata['entities']['urls'])>0  \
				and (len(jsondata['entities']['user_mentions']) > 0 \
				or jsondata['in_reply_to_status_id'] is not None  \
				or jsondata['is_quote_status'] \
				or 'retweeted_status' in jsondata.keys()):
					ingest = True

			if ingest:
				userida = jsondata['user']
				# insert nodes
				if userida['id'] not in nodes:
					nodes[userida['id']] = {'userid': userida['id'],'username': userida['screen_name']}
					# insert nodes
					insertNodes(nodes[userida['id']])

				text = jsondata['text']
				urls = jsondata['entities']['urls']
				
				# add edges
				myedgeArr = []

				# from user mentions
				user_mentions = jsondata['entities']['user_mentions']
				for user_mention in user_mentions:
					if user_mention['id'] not in nodes:
						nodes[user_mention['id']] = {'userid': user_mention['id'],'username': user_mention['screen_name']}
						# insert nodes
						insertNodes(nodes[user_mention['id']])
					# add  edges
					if userida['id'] != user_mention['id']:
						edgeDoc = {}
						edgeDoc['userida'] = userida['id']
						edgeDoc['useridb'] = user_mention['id']
						if userida['id'] not in edges.keys():
							edges[userida['id']] = {}
						if user_mention['id'] not in edges[userida['id']]:
							edges[userida['id']][user_mention['id']] = edgeDoc
							insertEdges(edgeDoc)					
						myedgeArr.append(edgeDoc)

				# from retweeted status
				if 'retweeted_status' in jsondata.keys():
					useridb = jsondata['retweeted_status']['user']
					if useridb['id'] not in nodes:
						nodes[useridb['id']] = {'userid': useridb['id'],'username': useridb['screen_name']}
						# insert nodes
						insertNodes(nodes[useridb['id']])
					# add  edges
					if userida['id'] not in edges.keys():
						edges[userida['id']] = {}
					if userida['id'] != useridb['id']:
						edgeDoc = {}
						edgeDoc['userida'] = userida['id']
						edgeDoc['useridb'] = useridb['id']
						if useridb['id'] not in edges[userida['id']]:
							edges[userida['id']][useridb['id']] = edgeDoc
							insertEdges(edgeDoc)
						myedgeArr = [edgeDoc]
				
				# from quoted status
				if jsondata['is_quote_status']:
					if 'quoted_status' in jsondata.keys():
						useridb = jsondata['quoted_status']['user']
						if useridb['id'] not in nodes:
							nodes[useridb['id']] = {'userid': useridb['id'],'username': useridb['screen_name']}
							# insert nodes
							insertNodes(nodes[useridb['id']])
						# add  edges
						if userida['id'] not in edges.keys():
							edges[userida['id']] = {}
						if userida['id'] != useridb['id']:
							edgeDoc = {}
							edgeDoc['userida'] = userida['id']
							edgeDoc['useridb'] = useridb['id']
							if useridb['id'] not in edges[userida['id']]:
								edges[userida['id']][useridb['id']] = edgeDoc
								insertEdges(edgeDoc)
							myedgeArr = [edgeDoc]
				
				# from reply to _status
				if jsondata['in_reply_to_status_id'] is not None:
					useridb = {'id': jsondata['in_reply_to_user_id'], 'username': jsondata['in_reply_to_screen_name']}
					if useridb['id'] not in nodes:
						nodes[useridb['id']] = {'userid': useridb['id'],'username': useridb['screen_name']}
						# insert nodes
						insertNodes(nodes[useridb['id']])
					# add  edges
					if userida['id'] not in edges.keys():
						edges[userida['id']] = {}
					if userida['id'] != useridb['id']:
						edgeDoc = {}
						edgeDoc['userida'] = userida['id']
						edgeDoc['useridb'] = useridb['id']
						if useridb['id'] not in edges[userida['id']]:
							edges[userida['id']][useridb['id']] = edgeDoc
							insertEdges(edgeDoc)
						myedgeArr = [edgeDoc]

				# add cascades
				if(len(urls)>0):			
					for url in urls:
						if(url['expanded_url']!=None):
							#print(url)
							# add cascadeid
							global cascadeid
							if(url['expanded_url'] not in cascades.keys()):
								#print('make cascade id: {}'.format(cascadeid))
								cascadeid+=1
								cascades[url['expanded_url']] = {'cascadeid': cascadeid,'url': url['expanded_url']}
								insertCascadeId(cascades[url['expanded_url']])							

							newJson = {}
							newJson['casid'] = cascades[url['expanded_url']]['cascadeid']
							newJson['userida'] = userida['id']
							newJson['edges'] = myedgeArr
							newJson['time'] = jsondata['created_at']
							newJson['timestamp_ms'] = jsondata['timestamp_ms']
							newJson['text'] = jsondata['text']
							insertCascade(newJson)


				global counter
				if (counter >= 100):
					print('commit')
					conn.commit();
					counter = 0

				counter+=1
		except BaseException as e:
			print('Error on data {}'.format(str(e)))
		return True
	def on_error(self,status):
		print(status)
		return True

# stream
twitter_stream = Stream(auth,MyListener())
# follow user stream
# twitter_stream.filter(follow = ['292432955'])
# tracking hashtag
twitter_stream.filter(track = keywords)

