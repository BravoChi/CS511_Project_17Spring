import json
import np
import scipy
from sklearn import feature_extraction
import nltk

# read cascades, perform operation to get dictionary words and their counts from the cascades
# we will treat this cascades as documents and cluster them using EM algorithm to infer
# the relations between edges

vocab = {}

# load stop words from nltk library
# this will be excluded from cascades vocabularies
stopwords = nltk.corpus.stopwords.words('english')


# read cascade file
with open('cascade-file.txt','r') as casFile:
	for cas in casFile:
		casJson = json.loads(cas)

