import subprocess
import json
import os
import sys
import re
import sqlite3

sys.setrecursionlimit(100000)

arg = sys.argv
# read twitter file
totalLine = 3
linecounter=0

conn = sqlite3.connect('meme.sqlite');
conn.text_factory = str

c = conn.cursor()

try:
	c.execute("CREATE TABLE observation_nodes (id integer,node text)")
except BaseException as e:
	print(e)
	# read url


def insertObservationNodes(node):
	params = []
	params.append(node['id'])
	params.append(node['node'])
	c = conn.cursor()
	c.execute("INSERT INTO observation_nodes VALUES (?,?)",params)

# get nodes that has more than 3 hops
rowsCas = c.execute("SELECT cascade from edge_hops where count >= 3 ")

nodes = {}

for row in rowsCas:
	cascades = json.loads(row[0])
	for cascade in cascades:
		for mycas in cascade['cascades']:
			if mycas[0] not in nodes.keys():
				nodes[mycas[0]] = 1
			if mycas[1] not in nodes.keys():
				nodes[mycas[1]] = 1
print(nodes)
#insert into observation_nodes table
j = 0
for node in nodes.keys():
	j+=1
	insertObservationNodes({'id': j,'node': node})
conn.commit()
print('total observation: {}'.format(j))
