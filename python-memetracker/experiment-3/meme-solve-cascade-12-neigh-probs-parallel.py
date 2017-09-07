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
import random

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
followes = {}

with open('edges.txt','r') as edgesFile:
    for edge in edgesFile:
        edgeJson = edge.replace('\n','').split(',')
        possible_edges.add((edgeJson[0],edgeJson[1]))
        if int(edgeJson[0]) not in edges.keys():
            edges[int(edgeJson[0])] = []
        if int(edgeJson[1]) not in followes.keys():
            followes[int(edgeJson[1])] = []
        edges[int(edgeJson[0])].append(int(edgeJson[1]))
        followes[int(edgeJson[1])].append(int(edgeJson[0]))

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
infected_nodes = {}
tedges = {}
tfollowes = {}
with open('cascade-file-parent-probs.txt','r') as casFile:
    for casRead in casFile:
        # prepare cascade
        # load cascade from the file
        obsNode = json.loads(casRead)
        #print(obsNode)
        parent_node = obsNode['node']
        if parent_node not in tfollowes:
            tfollowes[parent_node] = []        
        for obsCascades in obsNode['cascades']:
            if obsCascades['url'] not in cascade_checker:
                cascade_checker[obsCascades['url']] = 1
            else:
                continue
            cascade_id = cascade_count
            cascades[cascade_id] = {'probs': obsCascades['probs'],'cas': [],'infected_nodes':[]}
            for obsCas in obsCascades['cas']:
                dst = int(obsCas['node'])

                if dst not in tfollowes[parent_node] and dst !=parent_node:
                    tfollowes[parent_node].append(dst)
                if dst not in tedges:
                    tedges[dst] = []
                if parent_node not in tedges[dst] and dst!=parent_node:
                    tedges[dst].append(parent_node)

                at = float(obsCas['time'])/2505600
                cascades[cascade_id]['cas'].append((at, dst))

                if dst != parent_node:
                    cascades[cascade_id]['infected_nodes'].append(dst)

                # append cascadeid to nodes
                if dst not in nodeCascades.keys():
                    nodeCascades[dst] = []
                nodeCascades[dst].append(cascade_id)
            # add new cascade id
            cascade_count+=1


# This observation matrix will consume N X N memory depending on
# the total nodes, avoid using this for observing large network
"""
# Formulating the problem for each row of influence matrix A
A = np.zeros((num_nodes, num_nodes), dtype=float)
"""

#probs = []
results = []

def logSurvival(t_i, t_j, alpha_ji):
    # survival function for the transmission
    #print('log alpha: {}'.format(alpha_ji))
    return -alpha_ji * (t_i - t_j)

def hazard(t_i, t_j, alpha_ji):
    # hazard function when one node succesfully infected
    #print('haz alpha: {}'.format(alpha_ji))
    #return alpha_ji
    return alpha_ji


#def solveParallel(exprArr,Ai,i):
"""
def solveParallel(myobj):
    #print(solveObj[0])
    resArray = np.zeros(num_nodes)
    try:
        if proceed:
            prob = CVX.Problem(CVX.Maximize(myobj[1]), constraints)
            res = prob.solve(verbose=False,max_iters=500)
            #print(convexNodes[target_node_loc])
            if prob.status in [CVX.OPTIMAL, CVX.OPTIMAL_INACCURATE]:
                resArray = np.asarray(myobj[0].value).squeeze()
            else:
                resArray = -1
        else:
            resArray = 0
    except BaseException as e:
        print(e)
        resArray = -1
    return resArray
"""
def solveParallel(exprArr,Ai,constraints,i,proceed,num_nodes,output):
    #print(exprArr)
    resArray = np.zeros(num_nodes)
    try:
        if proceed:
            #print('expr {}: {}'.format(i,exprArr))
            prob = CVX.Problem(CVX.Maximize(exprArr), constraints)
            res = prob.solve(verbose=False,max_iters=500)
            #print(convexNodes[target_node_loc])
            if prob.status in [CVX.OPTIMAL, CVX.OPTIMAL_INACCURATE]:
                resArray = np.asarray(Ai.value).squeeze()
            else:
                resArray[:] = -1
        else:
            resArray[:] = 0
    except BaseException as e:
        print(e)
        resArray[:] = -1
    output.put((i,resArray))


#nodeCasSort = sorted(list(nodeCascades.keys()))
# select observed cascade only
nodeCasSort = []
with open('sample-node.txt','r') as sampleFile:
    for sample in sampleFile:
        sampleJson = json.loads(sample)
        [nodeCasSort.append(x) for x in sampleJson['sample']]

with open('prediction-neighbors-probs.txt','w') as writer:
    None


# explore the nodes that appear in cascades only
#for target_node in nodeCascades.keys():
myCount = 0
for target_node in nodeCasSort:
    print(target_node)
    myCount+=1

    # we want to infer transmission rate between child
    # and their parents, whose parent giving faster transmission
    # rate than the others therefore we need to use
    # all the cascades that are pass through the parent edge
    # in our cascade observation

    # reconstruct the nodes id for convex optimization problem
    # we will use our nodes of interest following child and
    # and parent relationship while child is the target node
    convexNodes = {}
    convexNodesArr = []
    convexNodes[target_node] = 0
    convexNodesArr.append(target_node)
    convexNodesCount = 1

    # construct the cascade for following 
    #observationCascadesId = nodeCascades[target_node].copy()
    observationCascadesId = copy.copy(nodeCascades[target_node])

    #print(edges[str(target_node)])

    if target_node not in tedges.keys():
        continue


    parentCascades = []
    parentArr = []
    for parent in tedges[target_node]:
        #if parent in nodeCascades:
        #    [observationCascadesId.append(x) for x in nodeCascades[parent]]
        # add the convex nodes
        convexNodes[parent] = convexNodesCount
        convexNodesArr.append(parent)
        parentArr.append(parent)                                
        convexNodesCount+=1
        if parent in nodeCascades:
            [parentCascades.append(x) for x in  nodeCascades[parent]]
        else:
            # skip this parent since it has no cascades
            continue

    # draw neighbor from same cascades
    k_neighbor = 5
    
    # prepare neighbor derived from    
    derivedFrom = {}
    # prepare neighborhood array
    neighborArr = []
    for casnode in nodeCascades[target_node]:        
        # add 5 random neighbor from the parents
        nFollowers = len(cascades[casnode]['infected_nodes'])
        #print(cascades[casnode]['infected_nodes'])
        k = k_neighbor
        k = k if nFollowers > k else nFollowers
        neighbors = random.sample(cascades[casnode]['infected_nodes'],k)
        
        for neighbor in neighbors:
            myneighbor = neighbor
            #print(myneighbor)
            if myneighbor not in convexNodes:
                if myneighbor in nodeCascades:
                    # [observationCascadesId.append(x) for x in nodeCascades[myneighbor]]
                    # check intersection with parent cascades
                    convexNodes[myneighbor] = convexNodesCount
                    convexNodesArr.append(myneighbor)
                    neighborArr.append(myneighbor)
                    convexNodesCount+=1

                    for x in nodeCascades[myneighbor]:
                        observationCascadesId.append(x)                        
                else:
                    print('neighbor {} not found in cascade'.format(myneighbor))



    # if no neighbor, skip this node
    if len(neighborArr) == 0:
        continue

    #print(convexNodes)
    #time.sleep(1)
    
    # reconstruct the observation cascades for this node
    observationCascades = {}
    for casid in observationCascadesId:
        if casid not in observationCascades:
            observationCascades[casid] = cascades[casid]

    #print(len(observationCascades.keys()))
    #time.sleep(1)

    num_nodes = len(convexNodesArr)

    # prepare the observation matrix
    A = np.zeros((num_nodes, num_nodes), dtype=float)

    # This is one column of the alpha matrix
    Ai = CVX.Variable(num_nodes, name='A[:,{}]'.format(convexNodes[target_node]))
    #Ai = [CVX.Variable(num_nodes, name='A[:,{}]'.format(convexNodes[target_node])) for i in range(15)]

    constraints=[]
    # define constraints
    """
    for j in range(num_nodes):
        if j == convexNodes[target_node]:
            constraints.append(Ai[j] == 0)
        else:
            constraints.append(Ai[j] >= 0)
    """
    """
    if j == convexNodes[target_node]:
        for i in range(15):
                constraints.append(Ai[i][j] == 0)
        else:
            for i in range(15):
                constraints.append(Ai[i][j] >= 0)
    """
    #constraints.append(Ai[j] >> 0)

    # this line is used if we are interested in the neighborhood
    # cascade as well, but to do this we need to load all the cascades
    """
    # nothing in cascades related to this node, just skip this value
    if target_node not in nodeCascades.keys():
        continue
    #myCascades = [cascades[x] for x in nodeCascades[target_node]]    
    observationCascades = nodeCascades[target_node].copy()
    # check neighborhood cascade
    if target_node in edges:
        for neighbor in edges[target_node]:
            if neighbor in nodeCascades:
                print('got something from {}'.format(neighbor))
                [observationCascades.append(x) for x in nodeCascades[neighbor]]
    print(observationCascades)
    # uniqfy the observationCascades
    observationCascades = list(set(observationCascades))
    """

    bad_infection = 0
    #expr = 0
    exprArr = [0 for i in range(15)]
    good_infection = np.zeros(num_nodes)    
    proceed = False
    for c_idx, citem in observationCascades.items():
        # normalize probability
        cprob = np.array(citem['probs'])
        if len(cprob) > 0:
            cprob = cprob/cprob.sum()        
        else:
            cprob = np.ones(15)
        c = citem['cas']
    #for nodecas in nodeCascades[target_node]:
    #for nodecas in observationCascades:
        #c_idx = nodecas
        #c = cascades[c_idx]
        #print(myCount)
        #print(c)
        #myCount+=1

        infection_time_arr = [x[0] for x in c if x[1] == target_node]
        #print('infection time: {}'.format(infection_time_arr))
        #time.sleep(1)

        #print('cascade: {}'.format(c))
        #print('total cascade: {}'.format(len(c)))
        assert len(infection_time_arr) <= 1
        proceedLog = False

        # computing the survival function of
        # the node i given cascade from j
        # this is unlikely to happen except if we are interested in
        # relation with other cascades on the edges
        if len(infection_time_arr) == 0:
            # Node 'i' was not infected in this cascade
            
            for j in range(len(c)):
                # check if the cascade transmission is in our observation nodes or not
                if c[j][1] in convexNodes.keys():
                    alpha_ji = Ai[convexNodes[c[j][1]]]
                    #print('alpha_ji surv: {}'.format(alpha_ji))
                    t_j = c[j][0]
                    T = time_period
                    #print('log sur1: {}'.format(logSurvival(T, t_j, alpha_ji)))
                    for i in range(len(cprob)):
                        #exprArr[i] += logSurvival(T, t_j, alpha_ji * cprob[i])
                        #alpha_ji = Ai[i][convexNodes[c[j][1]]]    
                        exprArr[i] += logSurvival(T, t_j, alpha_ji)
                    #print('log expr: {}\n'.format(expr))            
            
            # Instead of making so many parameter for uninteresting
            # cascade better to add counter for bad_infection
            # and multiply it with the survival function
            # in the end. Therefore we can save memory for
            # making a convex function

            """
            # because we are interested in parent and child relation only
            # then the logsurvival is the maximum ammount of the observation time
            T = time_period
            alpha_ji = Ai[target_node]
            expr+=logSurvival(T,0,alpha_ji)
            """

            # bad_infection+=1
        else:
            # Node 'i' was infected in this cascade
            infection_time = infection_time_arr[0]
            t_i = infection_time

            if c[0][0] != infection_time:
                # build the logSurvival and hazard function for
                # the infection
                # as a result this function will build an expression
                # that will be solved by convex problem            
                #log_sum = 0
                log_sum = [0 for x in range(15)]
                
                # check if the infection from the observation nodes
                # for child and parent relation
                for j in range(len(c)):
                    if c[j][1] in convexNodes.keys():
                        t_j = c[j][0]
                        alpha_ji = Ai[convexNodes[c[j][1]]]
                        #print('alpha_ji haz: {}'.format(alpha_ji))

                        if t_j < t_i:
                            for i in range(len(cprob)):
                                #alpha_ji = Ai[i][convexNodes[c[j][1]]]
                                #exprArr[i]+=logSurvival(t_i,t_j,alpha_ji * cprob[i])
                                exprArr[i]+=logSurvival(t_i,t_j,alpha_ji)
                                #print('log sur2: {}'.format(logSurvival(t_i,t_j,alpha_ji)))
                                log_sum[i]+=hazard(t_i,t_j,alpha_ji * cprob[i])
                            proceedLog = True
                            proceed = True
                            good_infection[convexNodes[c[j][1]]]+=1                            

                            #pass
                        #print('expr: {}'.format(expr))
                        #time.sleep(1)
                if proceedLog:
                    for i in range(len(cprob)):
                        exprArr[i] += CVX.log(log_sum[i])
                #print('expr: {}'.format(expr))
                #time.sleep(5)

                # for parent child relation only
                """
                t_j = 0
                alpha_ji = Ai[target_node]
                expr+=logSurvival(t_i,0,alpha_ji)
                log_sum+=hazard(t_i,0,alpha_ji)
                expr += CVX.log(log_sum)
                """
    
    # calculate bad infection for parent and child relation
    """
    T = time_period
    alpha_ji = Ai[target_node]                       
    expr += bad_infection * logSurvival(T,0,alpha_ji)
    """
    #print('expr: {}'.format(expr))
    #time.sleep(2)

    Aarray = np.zeros((len(cprob),num_nodes))
    # reshape constraints
    for j in range(num_nodes):
        if good_infection[j]==0:
            constraints.append(Ai[j] == 0)
        else:
            constraints.append(Ai[j] >= 0)



    # using parallel
    # buggy
    
    output = mp.Queue()

    argArr = []
    for i in range(15):
        argArr.append((exprArr[i],Ai,constraints,i))

    # Setup a list of processes that we want to run
    processes = [mp.Process(target=solveParallel, args=(x[0], x[1], x[2],x[3],proceed,num_nodes,output)) for x in argArr]


    # Run processes
    for p in processes:
        p.start()

    # Exit the completed processes
    for p in processes:
        p.join()

    # Get process results from the output queue
    results = [output.get() for p in processes]

    results.sort()
    results = [r[1] for r in results]
    Aarray = np.array(results)
    #print(Aarray.shape)
    
    

    """
    for i in range(len(cprob)):
        try:
            #print(exprArr[i])
            prob = CVX.Problem(CVX.Maximize(exprArr[i]), constraints)
            #res = prob.solve(verbose=True,max_iters=500)
            #res = prob.solve(verbose=True)
            res = prob.solve(verbose=True, max_iters=500)
            # source of the bug
            #if prob.status in [CVX.OPTIMAL, CVX.OPTIMAL_INACCURATE]:
            tempA = np.asarray(Ai.value).squeeze().tolist()
            Aarray[i] = np.asarray(Ai.value).squeeze()
            #print(tempA)
            A[:,convexNodes[target_node]] = tempA
            #print(len(tempA))
        except BaseException as e:
            print(e)
            A[:,convexNodes[target_node]] = -1
    """

    if num_nodes > 0:
        """
        Atwo = {}
        print(convexNodes.keys())
        for x in range(num_nodes):
            Atwo[convexNodesArr[x]] = Aarray[:,x].tolist()
        """
    
        with open('prediction-neighbors-probs.txt','a') as writer:
            writer.write(json.dumps({'target_node': target_node,'alpha': Aarray.T.tolist(), 'parents': parentArr,'neighbors': neighborArr,'trans':convexNodesArr, 'total_nodes':len(convexNodesArr), 'totalcas': len(observationCascades.keys())})+'\n')
        #with open('results.txt','a') as writer:
        #    writer.write(res)
    
    print(myCount)
    if myCount>10:
        # cleanup memory, otherwise it will be killed
        gc.collect()
        #print(mem_top())
        myCount=0

