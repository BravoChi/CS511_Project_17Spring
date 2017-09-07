from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import sqlite3

vectorizer = CountVectorizer(stop_words='english')

"""
# test words
train_set = ("The sky is blue.", "The sun is bright.")
test_set = ("The sun in the sky is bright.", "We can see the shining sun, the bright sun.")
vectorizer.fit_transform(train_set)
print(vectorizer)
corpus = ['This is the first document.',
		'This is the second second document.',
		'And the third one.',
		'Is this the first document?',
		]
corpus = ['This is the first document.']		
x = vectorizer.fit_transform(corpus)
print(x)
print(vectorizer.get_feature_names())
"""

# initialize corpus, get all text data from cluster_url
conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()
#define cursor

try:
	c.execute("CREATE TABLE cluster_new (cid INTEGER,text)")
	c.execute("CREATE TABLE clusterurl_new (cid INTEGER,date,type,domain,url TEXT)")
	#c.execute("CREATE INDEX clusterurl_url ON clusterurl(url)")
	#c.execute("CREATE INDEX cluster_cid ON cluster(cid)")
except BaseException as e:
	print(e)

# query the url as cascade
url_rows = c.execute('SELECT distinct url from clusterurl_new')
corpus = []
url = []
for url_row in url_rows:
	#print(url_row[0])
	c2 = conn.cursor()
	text_rows = c2.execute('SELECT a.text from cluster_new a,clusterurl_new b where b.url=? and b.cid=a.cid',[url_row[0]])
	url.append(url_row[0])
	temp_str = []
	for text_row in text_rows:
		temp_str.append(text_row[0])
	#print(' '.join(temp_str))
	corpus.append(' '.join(temp_str))

x = vectorizer.fit_transform(corpus)
x = x.tocoo()
#print(type(x))
#print(dir(x))
#print(x)
i = 0
with open('cas_id.txt','w') as casidFile:
	for myurl in url:
		casidFile.writelines('{},{}\n'.format(i,myurl))
		i+=1

i = 0
with open('feature.txt','w') as featureFile:
	for myfeature in vectorizer.get_feature_names():
		featureFile.writelines('{},{}\n'.format(i,myfeature))
		i+=1

with open('ex-feature.txt','w') as efFile:
	#np.apply_along_axis(lambda val: print(val),axis=0,arr=x)
	#for i in x.keys():
	#for i in x.rint():
#		print(i)
	for i,j,v in zip(x.row, x.col, x.data):
		#print("row = %d, row = %d, value = %s" % (i,j,v))
		efFile.writelines('{},{},{}\n'.format(i,j,v))
	"""
	for i in range(len(url)):
		for j in range(len(vectorizer.get_feature_names())):
			if x[i,j] > 0:
				efFile.writelines('{},{},{}\n'.format(i,j,x[i,j]))
	"""

#print(x)
#print(vectorizer.get_feature_names())


