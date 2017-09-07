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


cascades_string = "SELECT urlb,urla,domaina,domainb,date,memetext,casid from cascades where urlb=? order by casid asc,date asc"

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

def recurCascades(urlb,domainb,resArr,myBag,urlParent,level,history,casid):
	#print(casid)
	c = conn.cursor()
	rows = c.execute('SELECT distinct urlb,urla,domainb,domaina,date,memetext from cascades where domainb=? and casid = ? order by date asc',[domainb,casid])
	i = 0
	for row in rows:
		print(level)
		if row[3] not in history:
			# don't turn back
			history = history.copy();
			history.append(domainb)
			if cascades[row[0]][row[1]] == 0:
				i+=1
				resArrCopy = resArr.copy()
				resArrCopy.append(row)
				cascades[row[0]][row[1]] = 1
				recurCascades(row[1],row[3],resArrCopy,myBag,urlParent,level+1,history,casid)
	if i == 0:
		#print(json.dumps(resArr))
		myBag[casid].append({ 'count': level - 1, 'cascades': resArr})
		if level - 1 > 2:
			print(resArr)
		#print(json.dumps(myBag))


cascadeRows = c.execute("SELECT distinct a.casid,b.text from cascades a,cluster b where a.casid=b.cid order by casid asc")
j = 0
for cascadeRow in cascadeRows:
	c1 = conn.cursor()
	rowsCas = c1.execute("SELECT urlb,urla,domainb,domaina,date,casid from cascades where casid = ? order by date asc",[cascadeRow[0]])
	for row in rowsCas:
		j+=1
		print(j)
		if cascades[row[0]][row[1]] == 0:
			myBag = {}
			print(row[0])
			myBag[row[5]] = []
			recurCascades(row[0],row[2],[],myBag,row[0],1,[],cascadeRow[0])
			#print(json.dumps(myBag))
			with open('cascades-cluster.txt','a') as casfile:
				casfile.writelines(json.dumps(myBag)+'\n')
		#params.append(row[1])
		#recurC = conn.cursor()
		#recurs = recurC.execute(recursive_edges,params)
		#for recur in recurs:
		#	print(recur)


