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

# read cascade
# prepare cascade object
cascades = {}
cascade_count = 0

# to indexing cascades between node id
# this will infer which cascade is 
# having a node id
nodeCascades = {}
cascade_checker = {}
cascade_probs = {}
with open('cascade-file-parent-probs.txt','r') as casFile:
    for casRead in casFile:
        # prepare cascade
        # load cascade from the file
        obsNode = json.loads(casRead)
        #print(obsNode)
        parent_node = obsNode['node']
        for obsCascades in obsNode['cascades']:
            if obsCascades['url'] not in cascade_checker:
                cascade_checker[obsCascades['url']] = 1
            else:
                continue
            cascade_id = cascade_count
            cascades[cascade_id] = {'probs': obsCascades['probs'],'cas': []}
            for obsCas in obsCascades['cas']:
                dst = int(obsCas['node'])
                at = float(obsCas['time'])/2505600
                cascades[cascade_id]['cas'].append((at, dst))                

                # append cascadeid to nodes
                if dst not in nodeCascades.keys():
                    nodeCascades[dst] = []
                nodeCascades[dst].append(cascade_id)
            # add new cascade id
            cascade_count+=1


holaFile = open('prediction-child-parents-p-stat.txt','w')
holaFile.write('{},{},{},{}\n'.format('TargetNode','TotalNode','TotalCascade','Accuracy'))
# open the output file
with open('prediction-child-parents-p.20170417.txt','r') as predFile:
    for pred in predFile:
        predJson = json.loads(pred)
        targetNode = predJson['target_node']
        # get the parent's target node and cascade
        parentNodes = edges[targetNode]
        nodesNum = len(parentNodes)+1

        observationCascadesId = copy.copy(nodeCascades[targetNode])

        # check neighborhood cascade
        for parent in edges[targetNode]:
            if parent in nodeCascades:
                [observationCascadesId.append(x) for x in nodeCascades[parent]]

        #uniqfy cascadeid
        observationCascades = list(set(observationCascadesId))
        cascadeNum = len(observationCascades)

        # accuracy:
        output = predJson['alpha']

        tn = 0
        tp = 0
        count = 0
        accuracy = 0
        #print('\n{}'.format(targetNode))
        for idx in output.keys():
            alpha = predJson['alpha'][idx]
            p_value = [ x for x in alpha if x > 1e-6]
            if int(idx) != int(targetNode):
                #print(idx)
                if len(alpha)==0 or len(p_value) == 0:
                    tn+=1
                else:
                    tp+=1
                count+=1

        if count > 0:
            accuracy = tp / count

        holaFile.write('{},{},{},{}\n'.format(targetNode,nodesNum,cascadeNum,accuracy))

holaFile.close()


holaFile = open('prediction-child-parents-stat.txt','w')
holaFile.write('{},{},{},{}\n'.format('TargetNode','TotalNode','TotalCascade','Accuracy'))
# open the output file
with open('prediction-child-parents.20170330.txt','r') as predFile:
    for pred in predFile:
        predJson = json.loads(pred)
        targetNode = predJson['target_node']
        # get the parent's target node and cascade
        parentNodes = edges[targetNode]
        nodesNum = len(parentNodes)+1

        observationCascadesId = copy.copy(nodeCascades[targetNode])

        # check neighborhood cascade
        for parent in edges[targetNode]:
            if parent in nodeCascades:
                [observationCascadesId.append(x) for x in nodeCascades[parent]]

        #uniqfy cascadeid
        observationCascades = list(set(observationCascadesId))
        cascadeNum = len(observationCascades)

        # accuracy:
        output = predJson['alpha']

        tn = 0
        tp = 0
        count = 0
        accuracy = 0
        for idx in output.keys():
            alpha = predJson['alpha'][idx]
            if int(idx) != int(targetNode):
                if alpha <= 1e-6:
                    tn+=1
                else:
                    tp+=1
                count+=1

        if count > 0:
            accuracy = tp / count

        holaFile.write('{},{},{},{}\n'.format(targetNode,nodesNum,cascadeNum,accuracy))

holaFile.close()