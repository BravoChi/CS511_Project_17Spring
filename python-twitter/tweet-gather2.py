import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener


auth = OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token,access_secret)

api = tweepy.API(auth)

# search
#twitterapi = api.search('twitter')
#tweet = api.user_timeline(screen_name='JustinMcElroy',count=200)
#print(tweet)
tweets = api.statuses_lookup(id_=['840276072671383554'])
#print(tweets)
retweets = api.retweets('840276072671383554')
print(retweets)
#print(twitterapi)
#print(len(twitterapi))




class MyListener(StreamListener):
	def on_data(self,data):
		try:
			print(data)
		except BaseException as e:
			print('Error on data {}'.format(str(e)))
		return True
	def on_error(self,status):
		print(status)
		return True

"""
# stream
twitter_stream = Stream(auth,MyListener())
# follow user stream
# twitter_stream.filter(follow = ['292432955'])
# tracking hashtag
twitter_stream.filter(track = ['#food','#restaurant','#delicious','#sport','#football','#soccer','#EPL','#barcelona','#realmadrid','#mu','#ggmu'])
"""
