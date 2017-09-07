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

# read all edges
rows = c.execute("SELECT DISTINCT urla,urlb from cascades")
cascades = {}
for row in rows:
	if row[1] not in cascades:
		cascades[row[1]] = {}
	if row[0] not in cascades[row[1]]:
		cascades[row[1]][row[0]] = 0

# read recursive cascades
recursive_string = "WITH RECURSIVE \
descendants as \
  ( select urlb,urla as descendant,date,memetext, 1 as level \
    from cascades \
    where urlb = ? \
  union all \
    select d.urlb, s.urla,s.date,s.memetext, d.level + 1 \
    from descendants as d \
      join cascades s \
        on d.descendant = s.urlb \
  ) \
select * \
from descendants \
order by urlb, level, descendant"


recursive_edges = "WITH RECURSIVE \
descendants as \
  ( select domainb,domaina as descendant, 1 as level \
    from edges \
    where domainb = ? \
  union all \
    select d.domainb, s.domaina, d.level + 1 \
    from descendants as d \
      join edges s \
        on d.descendant = s.domainb \
  ) \
select * \
from descendants \
order by domainb, level, descendant"


cascades_string = "SELECT urlb,urla,domaina,domainb,date,memetext from cascades where urlb=? order by date asc"

"""
with recursive group_tree as (
  select id_group, 
         id_parent, 
         sequence
  from groups
  where id_parent = 0 -- marks the start of your tree
  union all
  select c.id_group, 
         c.id_parent,
         c.sequence
  from groups p
    join group_tree c on p.id_group = c.id_parent
) 
"""

print('cascade ok')

#rowsCas = c.execute("SELECT distinct domaina,domainb from edges")
rowsCas = c.execute("SELECT urlb,urla,date from cascades order by date asc")

def recurCascades(urlb,resArr,myBag,urlParent,level):
	c = conn.cursor()
	rows = c.execute('SELECT distinct urlb,urla,domainb,domaina,date,memetext from cascades where urlb = ? order by date asc',[urlb])
	i = 0
	for row in rows:
		print(level)
		if cascades[row[0]][row[1]] == 0:
			i+=1
			resArrCopy = resArr.copy()
			resArrCopy.append(row)
			cascades[row[0]][row[1]] = 1
			recurCascades(row[1],resArrCopy,myBag,urlParent,level+1)
	if i == 0:
		#print(json.dumps(resArr))
		myBag[urlParent].append({ 'count': level - 1, 'cascades': resArr})
		#print(json.dumps(myBag))

j = 0
for row in rowsCas:
	j+=1
	print(j)
	if cascades[row[0]][row[1]] == 0:
		myBag = {}
		print(row[0])
		myBag[row[0]] = []
		recurCascades(row[0],[],myBag,row[0],1)
		print(json.dumps(myBag))
		with open('cascades-file.txt','a') as casfile:
			casfile.writelines(json.dumps(myBag)+'\n')
	#params.append(row[1])
	#recurC = conn.cursor()
	#recurs = recurC.execute(recursive_edges,params)
	#for recur in recurs:
	#	print(recur)


