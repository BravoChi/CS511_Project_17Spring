#!/usr/bin/env python
from __future__ import print_function
import csv
import numpy as np
import cvxpy as CVX
from collections import defaultdict
import simplejson as json
import time
import gc
from mem_top import mem_top
import copy
import multiprocessing as mp
from functools import partial 

nodes = []
nodeHash = {}
edges = {}

with open('nodes.txt','r') as nodesFile:
    for node in nodesFile:
        rownode = node.replace('\n','').split(',')
        nodes.append(rownode[1])
        nodeHash[rownode[0]] = int(rownode[1])

num_nodes = len(nodes)

# we have scale the timescale into 0 to 1.0
# while 1 is equal to 30 days for this memetracker problem
time_period = 1.0

cascades = defaultdict(lambda : [])


# Possible edges: if we have never seen any infection travel down an edge, the
# best estimate for alpha for that edge is 0, i.e. it does not exist.
# The possible edges is already maintained in edges.txt file
# so we can easily load the edges from the file
possible_edges = set()
# edges hash, infer following matrix
edges = {}
with open('edges.txt','r') as edgesFile:
    for edge in edgesFile:
        edgeJson = edge.replace('\n','').split(',')
        possible_edges.add((edgeJson[0],edgeJson[1]))
        if int(edgeJson[0]) not in edges.keys():
            edges[int(edgeJson[0])] = []
        edges[int(edgeJson[0])].append(int(edgeJson[1]))

epsilon = 1e-6

holaFile = open('prediction-neighbors-probs-exp-stat.txt','w')
holaFile.write('{},{},{},{},{},{},{},{},{},{}\n'.format('TargetNode','TotalNode','TotalCascade','TP','TN','FP','FN','Precision','Recall','F1','Accuracy'))
# open the output file
with open('prediction-neighbors-probs-exp-20170426.txt','r') as predFile:
    for pred in predFile:
        predJson = json.loads(pred)
        target = predJson['target_node']
        trans = predJson['trans']
        nodesNum = predJson['total_nodes']
        cascadeNum = predJson['totalcas']
        # direct network
        direct = [trans.index(x) for x in predJson['parents']]
        neighbor = [trans.index(x) for x in predJson['neighbors']]
        random_neighbor = [trans.index(x) for x in predJson['rand_neighbors']]

        #direct.append(trans.index(target)) 
        targetidx = trans.index(target)
        alpha = predJson['alpha']        

        fp = 0
        fn = 0
        tn = 0
        tp = 0
        count = 0
        accuracy = 0
        #print('\n{}'.format(targetNode))
        for y in range(len(alpha)):
            if y != targetidx:
                myal = np.array(alpha[y])
                #print(alpha[y])
                if y in direct or y in neighbor:
                    if np.any(myal >= epsilon):
                        tp+=1
                    else:
                        fn+=1
                else:
                    if np.any(myal >= epsilon):
                        fp+=1
                    else:
                        tn+=1                            
                count+=0                

        precision=0

        if (tp+fp!=0):
            precision = tp * 1.0 / (tp + fp)

        recall = tp * 1.0/ nodesNum

        F1 = 2 * tp / (2 * tp + fn + fp)
        holaFile.write('{},{},{},{},{},{},{},{},{},{}\n'.format(target,nodesNum,cascadeNum,tp,tn,fp,fn,precision,recall,F1))

holaFile.close()


holaFile = open('prediction-neighbors-exp-stat.txt','w')
holaFile.write('{},{},{},{},{},{},{},{},{},{}\n'.format('TargetNode','TotalNode','TotalCascade','TP','TN','FP','FN','Precision','Recall','F1','Accuracy'))
# open the output file
with open('prediction-neighbors-experiment-nc.txt','r') as predFile:
    for pred in predFile:
        predJson = json.loads(pred)
        target = predJson['target_node']
        trans = predJson['trans']
        nodesNum = predJson['total_nodes']
        cascadeNum = predJson['totalcas']
        # direct network
        direct = [trans.index(x) for x in predJson['parents']]
        neighbor = [trans.index(x) for x in predJson['neighbors']]
        random_neighbor = [trans.index(x) for x in predJson['rand_neighbors']]

        #direct.append(trans.index(target)) 
        targetidx = trans.index(target)
        alpha = predJson['alpha']        

        fp = 0
        fn = 0
        tn = 0
        tp = 0
        count = 0
        accuracy = 0
        #print('\n{}'.format(targetNode))
        for y in range(len(alpha)):
            if y != targetidx:
                myal = np.array(alpha[y])
                #print(alpha[y])
                if y in direct or y in neighbor:
                    if np.any(myal >= epsilon):
                        tp+=1
                    else:
                        fn+=1
                else:
                    if np.any(myal >= epsilon):
                        fp+=1
                    else:
                        tn+=1                            
                count+=0                

        precision=0

        if (tp+fp!=0):
            precision = tp * 1.0 / (tp + fp)

        recall = tp * 1.0/ nodesNum

        F1 = 2 * tp / (2 * tp + fn + fp)
        holaFile.write('{},{},{},{},{},{},{},{},{},{}\n'.format(target,nodesNum,cascadeNum,tp,tn,fp,fn,precision,recall,F1))

holaFile.close()
