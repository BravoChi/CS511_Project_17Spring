from __future__ import print_function
import csv
import numpy as np
import simplejson as json
import time
import sqlite3	
import string
import re as re
import pickle


# load vocabulary
vocabulary = {}
vocCount = 0
with open('words-obs.txt','r') as vocfile:    
    for voc in vocfile:
        voc = voc.replace('\n','')
        vocabulary[voc] = vocCount
        vocCount+=1
#vocabulary = np.array(vocabulary)

conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()

#trans_table = string.maketrans(string.punctuation, " "*len(string.punctuation))
regex = re.compile('[%s]' % re.escape(string.punctuation))

em_results = pickle.load( open( "em_results_15b.p", "rb" ) )
print(em_results['p_jk'].shape)

casWrite = open('cascade-file-parent-probs2.txt','a')

with open('cascade-file-parent.txt','r') as casFile:
	for casRead in casFile:
		# prepare cascade
		# load cascade from the file
		obsNode = json.loads(casRead)
		#print(obsNode)
		parent_node = obsNode['node']
		for obsCascades in obsNode['cascades']:
			rows = c.execute("SELECT a.text from cluster_new a,clusterurl_new b where b.url=? and b.cid=a.cid",[obsCascades['url']])
			casTextArr = []
			for row in rows:
				casTextArr.append(row[0])
			casText = " ".join(casTextArr)
			#print(casText)
			#new_string = some_string.translate(trans_table)
			#print(new_string)
			#tokenized_reports = word_tokenize(casText)
			#print(tokenized_reports)

			new_token = regex.sub(u'', casText).split(' ')
			vocabArr = []
			def checkVocab(x):
				if x in vocabulary.keys(): 
					vocabArr.append(vocabulary[x])
				return
			([checkVocab(x) for x in new_token])			
			if len(vocabArr)>0:
				probs = (em_results['p_jk'][:,vocabArr]).sum(axis=1)
				obsCascades['text'] = casText
				obsCascades['probs'] = probs.tolist()
			else:
				obsCascades['probs'] = []
		casWrite.write('{}\n'.format(json.dumps(obsNode)))
		


