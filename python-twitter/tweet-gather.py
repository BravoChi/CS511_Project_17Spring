import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import subprocess
import json
import os
import sys

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

# search
#twitterapi = api.search('twitter')
#tweet = api.user_timeline(screen_name='JustinMcElroy',count=200)
#print(tweet)
#tweets = api.statuses_lookup(id_=['76635000'])
#print(tweets)
#print(twitterapi)
#print(len(twitterapi))

fileStream = {}
cascades = {}
edges = {}
nodes = {}
global cascadeid
cascadeid = 0
global counter
counter = 0

# load nodes
if os.path.isfile('nodes.txt'):
	with open('nodes.txt','r') as nodesfile:
		for line in nodesfile:
			if(line!=''):
				my_line = line.split(" ");
				nodes[my_line[0]] = my_line[1]
#print(nodes)

# load edges
if os.path.isfile('edges.txt'):
	with open('edges.txt','r') as nodesfile:
		for line in nodesfile:
			if(line!=''):
				my_json = json.loads(line);
				if(my_json['domain']['user_id_str'] not in edges.keys()):
					edges[my_json['domain']['user_id_str']] = {}
					if my_json['range']['user_id_str'] not in edges[my_json['domain']['user_id_str']].keys():
						edges[my_json['domain']['user_id_str']][my_json['range']['user_id_str']] = my_json
#print(edges)

# load cascades
if os.path.isfile('cascade-id.txt'):
	with open('cascade-id.txt','r') as nodesfile:
		lineExist = False
		for line in nodesfile:
			if(line!=''):
				lineExist = True
				my_line = line.split(" ");
				cascades[my_line[1]] = my_line[0]
		if lineExist:
			cascadeid = int(my_line[0])

cascadefile = open('cascade-id.txt','a')
edgesfile = open('edges.txt','a')
nodesfile = open('nodes.txt','a')

class MyListener(StreamListener):
	def on_data(self,data):
		try:
			data = json.loads(data)
			if data['lang'] == 'en':
				if(len(data['entities']['urls'])>0):			
					urls = data['entities']['urls']
					for i in range(len(urls)):					
						url = urls[i]
						if(url['expanded_url']!=None):
							#print(url)
							global cascadeid
							if(url['expanded_url'] not in cascades.keys()):
								#print('make cascade id: {}'.format(cascadeid))
								cascadeid+=1
								cascades[url['expanded_url']] = cascadeid
								cascadefile.writelines('{} {}\n'.format(cascades[url['expanded_url']],url['expanded_url']))	
							# save to file							
							with open('cas-'+str(cascades[url['expanded_url']])+'.txt','a') as fileStream:
								newJson = {}
								newJson['created_at'] = data['created_at']
								newJson['text_id_str'] = data['id_str']
								newJson['text'] = data['text']
								newJson['user_id_str'] = data['user']['id_str']
								newJson['user_screen_name'] = data['user']['screen_name']
								# add nodes
								if(newJson['user_id_str'] not in nodes):
									nodes[newJson['user_id_str']] = newJson['user_screen_name']
									nodesfile.writelines('{} {}\n'.format(newJson['user_id_str'],newJson['user_screen_name']))
								newJson['user_followers_count'] = data['user']['followers_count']
								newJson['user_friends_count'] = data['user']['friends_count']
								newJson['retweet_count'] = data['retweet_count']
								newJson['entities'] = data['entities']
								newJson['timestamp_ms'] = data['timestamp_ms']
								# build edge based on user mentions
								if(len(data['entities']['user_mentions'])>0):
									for j in range(len(data['entities']['user_mentions'])):
										userRange = data['entities']['user_mentions'][j]
										if(userRange['id_str'] not in edges.keys()):
											edges[userRange['id_str']] = {}
										if newJson['user_id_str'] not in edges[userRange['id_str']].keys():
											edges[userRange['id_str']][newJson['user_id_str']] = {}
										edge = {}
										edge['range'] = { 'user_id_str': newJson['user_id_str'], 'user_screen_name': newJson['user_screen_name']}
										edge['domain'] = { 'user_id_str': userRange['id_str'], 'user_screen_name': userRange['screen_name']}
										edges[userRange['id_str']][newJson['user_id_str']] = edge
										edgesfile.writelines(json.dumps(edge)+'\n')
										if(edge['domain']['user_id_str'] not in nodes):
											nodes[edge['domain']['user_id_str']] = edge['domain']['user_screen_name']
											nodesfile.writelines('{} {}\n'.format(edge['domain']['user_id_str'],edge['domain']['user_screen_name']))

								if('retweeted_status' in data.keys()):
									newJson['parent_tweet_id'] = data['retweeted_status']['id_str']
									newJson['parent_tweet_user_id'] = data['retweeted_status']['user']['id_str']
								fileStream.writelines(json.dumps(newJson)+'\n')
					global counter
					counter+=1
					if(counter>1000):
						cascadefile.flush()
						nodesfile.flush()
						edgesfile.flush()
						counter = 0
						print('flush cascade')
					#print(data)
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

