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
	c.execute("CREATE TABLE observation_nodes_2 (id integer,node text)")
except BaseException as e:
	print(e)
	# read url


def insertObservationNodes(node):
	params = []
	params.append(node['id'])
	params.append(node['node'])
	c = conn.cursor()
	c.execute("INSERT INTO observation_nodes_2 VALUES (?,?)",params)

# get nodes that has more than 3 hops
rowsCas = c.execute("SELECT cascade from edge_three_hops")

nodes = {}
edges = {}

for row in rowsCas:
	cascades = json.loads(row[0])
	for cascade in cascades:
		if len(cascade['cascades'])>1:
			for mycas in cascade['cascades']:
				if mycas[0] not in nodes.keys():
					nodes[mycas[0]] = 1
				if mycas[1] not in nodes.keys():
					nodes[mycas[1]] = 1
				# last cascades is potential edge
				# since first cascade just referral page
				# 1 is follower, 0 is parent
				if mycas[1] not in edges.keys():
					edges[mycas[1]] = {}
				if mycas[0] not in edges[mycas[1]]:
					edges[mycas[1]][mycas[0]] = 1
print(nodes)

#insert into observation_nodes table
"""
j = 0
for node in nodes.keys():
	j+=1
	insertObservationNodes({'id': j,'node': node})
	#with open('nodes.txt','a') as nodesFile:
	#	nodesFile.write('{},{}\n'.format(node,j))
"""

nodes = {}
nodeRows = c.execute("SELECT id,node from observation_nodes_2")
for noderow in nodeRows:
	nodes[noderow[1]] = noderow[0]
	with open('nodes.txt','a') as nodesFile:
		nodesFile.write('{},{}\n'.format(noderow[1],noderow[0]))

for edge in edges.keys():
	for parent in edges[edge].keys():
		with open('edges.txt','a') as edgesFile:
			edgesFile.write('{},{}\n'.format(nodes[edge],nodes[parent]))

#conn.commit()
#print('total observation: {}'.format(j))
