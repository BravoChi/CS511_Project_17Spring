import sqlite3

conn = sqlite3.connect('extract-text.sqlite');
conn.text_factory = str

c = conn.cursor()
#define cursor

# create related table
# nodes
try:
	c.execute("CREATE TABLE exfeature(docid,wordid,total)")
	c.execute("CREATE TABLE words (wordid,word)")
	c.execute("CREATE TABLE docs (docid,doc)")
except BaseException as e:
	print(e)

def insertDocs(doc):
	params = []
	params.append(doc['docid'])
	params.append(doc['doc'])
	c = conn.cursor()
	c.execute("INSERT INTO docs VALUES (?,?)",params)

def insertWords(word):
	params = []
	params.append(word['wordid'])
	params.append(word['word'])
	c = conn.cursor()
	c.execute("INSERT INTO words VALUES (?,?)",params)

def insertExFeature(feat):
	params = []
	params.append(feat['docid'])
	params.append(feat['wordid'])
	params.append(feat['total'])
	c = conn.cursor()
	c.execute("INSERT INTO exfeature VALUES (?,?,?)",params)

with open('cas_id.txt','r') as casfile:
	for cas in casfile:
		cas = cas.replace('\n','')
		rows = cas.split(',')
		insertDocs({'docid': rows[0],'doc': rows[1]})

conn.commit()

with open('feature.txt','r') as casfile:
	for cas in casfile:
		cas = cas.replace('\n','')
		rows = cas.split(',')
		insertWords({'wordid': rows[0],'word': rows[1]})		

conn.commit()

with open('ex-feature.txt','r') as casfile:
	for cas in casfile:
		cas = cas.replace('\n','')
		rows = cas.split(',')
		insertExFeature({'docid': rows[0],'wordid': rows[1],'total': rows[2]})				

conn.commit()
