import sqlite3

conn = sqlite3.connect('extract-text.sqlite');
conn.text_factory = str

c = conn.cursor()
#define cursor

# create related table
# nodes

rows = c.execute("select * from (SELECT docid,sum(total) as total_feature FROM exfeature group by docid) where total_feature < 250 order by total_feature desc")

words = {}
wordsArr = []
cascades = {}
cascadesArr = []

wordCount = 0
cascadeCount = 0

extracted = 0
prevRow = 'aha'
prevTotal = 0
featFile = open('feat-obs.txt','a')
wordFile = open('words-obs.txt','a')
docFile = open('docs-obs.txt','a')
for row in rows:
	print(row[0])
	c2 = conn.cursor()
	rows2 = c2.execute("SELECT b.word,c.doc,a.total from exfeature a,words b,docs c where a.docid=c.docid and b.wordid=a.wordid and a.docid=? order by a.total desc",[row[0]])
	firstRow = True
	for row2 in rows2:
		if firstRow:
			if row[1]==prevTotal and prevRow == row2[0]:
				# break because it contains same content (based on cluster)
				break;
			prevTotal = row[1]
			prevRow = row2[0]
			firstRow = False
		if row2[0] not in words.keys():
			words[row2[0]] = wordCount
			wordsArr.append(row2[0])
			wordFile.write('{}\n'.format(row2[0]))
			wordCount+=1
		if row2[1] not in cascades.keys():
			cascades[row2[1]] = cascadeCount
			cascadesArr.append(row2[1])
			docFile.write('{}\n'.format(row2[1]))
			cascadeCount+=1
		print('{},{},{}'.format(cascades[row2[1]],words[row2[0]],row2[2]))
		featFile.write('{},{},{}\n'.format(cascades[row2[1]],words[row2[0]],row2[2]))
	if cascadeCount>20000:
		break;