#!/usr/bin/env python
from __future__ import print_function
import csv
import numpy as np
import cvxpy as CVX
from collections import defaultdict
import simplejson as json

nodes = []
edges = {}


def calc_score(A_pred, A_soln, eps=0):
	"""Calculates the F1 score for a given activation against the ground
	truth."""
	# The A_pred may have some very small negative numbers as well.
	# So < eps == zero, and >= eps == non-zero
	# eps = 1e-6 gives the same results for CVX+SCS solver as the LBFGS solution

	num_edges = np.sum(A_soln > 0)
	#True Positive
	print('test {}'.format(np.sum(A_pred>eps)))
	TP = np.sum(A_soln[A_pred > eps] > 0)
	#False Positive
	FP = np.sum(A_soln[A_pred > eps] <= 0)
	#False Negative
	FN = np.sum(A_pred[A_soln > eps] < eps)
	print('shape: {} {}'.format(A_pred.shape,A_soln.shape))
	print('{} {} {} {}'.format(num_edges,TP,FP,FN))
	precision = TP * 1.0 / (TP + FP)
	recall = TP * 1.0/ num_edges

	F1 = 2 * TP / (2 * TP + FN + FP)

	# TODO: Add metrics for comparing the actual numbers.

	return {'F1'        : F1,
		'precision' : precision,
		'recall'    : recall}


with open('nodes-file.txt','r') as nodesFile:
    for node in nodesFile:
        nodes.append(node)

num_nodes = len(nodes)
# we have scale the timescale into 0 to 1.0
#time_period = 1.0
# using real milisecond about 3 months
time_period = 5751721/2505600

cascades = defaultdict(lambda : [])

# get cascade id for every nodes:
nodeCascades = {}
nodeCascadesHash = {}

ASol = np.zeros((num_nodes, num_nodes), dtype=float)

with open('cascade-file.txt','r') as cascadesFile:
    # Reading cascades
    for cascadesRow in cascadesFile:
        #print(cascadesRow)
        casjson = json.loads(cascadesRow)
        cascade_id = casjson['casid']
        for cascade in casjson['cas']:            
            dst        = int(cascade['node']-1)
            at         = float(cascade['time']/2505600)
            # keys = 'cascade_id', 'dst', 'at'
            assert at <= time_period, "Infection after observation period."
            cascades[cascade_id].append((at, dst))
            # append cascadeid to nodes
            if dst not in nodeCascades.keys():
                nodeCascades[dst] = []
                nodeCascadesHash[dst] = {}
            if cascade_id not in nodeCascadesHash[dst].keys():
                nodeCascadesHash[dst][cascade_id] = {}
                nodeCascades[dst].append(cascade_id)


#print(json.dumps(nodeCascades))

# Convex problem
# Start definition of the problem

# Sort according to time
for cascade_id in cascades.keys():
    cascades[cascade_id] = sorted(cascades[cascade_id])

# Possible edges: if we have never seen any infection travel down an edge, the
# best estimate for alpha for that edge is 0, i.e. it does not exist.
possible_edges = set()
edges = {}
with open('edges-file.txt','r') as edgesFile:
    for edge in edgesFile:
        edgeJson = json.loads(edge)
        possible_edges.add((edgeJson[0],edgeJson[1]))
        if edgeJson[0] not in edges.keys():
            edges[edgeJson[0]] = []
        edges[edgeJson[0]].append(edgeJson[1])
        # build Asol
        ASol[edgeJson[1]-1][edgeJson[0]-1] = 1

#for c in cascades.values():
#    for i in range(len(c)):
#       for j in range(i):
#           possible_edges.add((c[j][1], c[i][1]))

# Formulating the problem for each row of influence matrix A
A = np.zeros((num_nodes, num_nodes), dtype=float)
probs = []
results = []


def logSurvival(t_i, t_j, alpha_ji):
    # TODO
    #raise NotImplementedError('logSurvival not implemented.')
    #print('log alpha: {}'.format(alpha_ji))
    return -alpha_ji * (t_i - t_j)

def hazard(t_i, t_j, alpha_ji):
    # TODO
    #raise NotImplementedError('hazard not implemented.')
    #print('haz alpha: {}'.format(alpha_ji))
    #return alpha_ji
    return alpha_ji

# These problems can be solved in parallel
for target_node in range(num_nodes):
    print(target_node)

    # This is one column of the alpha matrix
    Ai = CVX.Variable(num_nodes, name='A[:, {}]'.format(target_node))

    # Which edges are constrained to be zero
    constraints = []
    for j in range(num_nodes):
        if (j, target_node) not in possible_edges:
            constraints.append(Ai[j] == 0)
        else:
            #constraints.append(Ai[j] >= 0)
            constraints.append(Ai[j] >> 0)

    #print(constraints)

    # Constructing the log-likelihood for the target_node
    expr = 0
    myCount = 0

    # nothing in cascades related to this node, just skip this value
    if target_node not in nodeCascades.keys():
        continue

    #myCascades = [cascades[x] for x in nodeCascades[target_node]]

    observationCascades = nodeCascades[target_node].copy()
    # check neighborhood cascade
    """
    if target_node in edges:
        for neighbor in edges[target_node]:
            if neighbor in nodeCascades:
                print('got something from {}'.format(neighbor))
                [observationCascades.append(x) for x in nodeCascades[neighbor]]
  	"""

    print(observationCascades)
    # uniqfy the observationCascades
    observationCascades = list(set(observationCascades))

    #for c_idx, c in cascades.items():
    #for nodecas in nodeCascades[target_node]:
    for nodecas in observationCascades:
        c_idx = nodecas
        c = cascades[c_idx]
        print(myCount)
        print(c)
        myCount+=1
        infection_time_arr = [x[0] for x in c if x[1] == target_node]

        #print('cascade: {}'.format(c))
        assert len(infection_time_arr) <= 1

        if len(infection_time_arr) == 0:
            # Node 'i' was not infected in this cascade
            for j in range(len(c)):
                alpha_ji = Ai[c[j][1]]
                #print('alpha_ji surv: {}'.format(alpha_ji))
                t_j = c[j][0]
                T = time_period
                #print('log sur1: {}'.format(logSurvival(T, t_j, alpha_ji)))
                expr += logSurvival(T, t_j, alpha_ji)
      #          print('log expr: {}\n'.format(expr))
        else:
            # Node 'i' was infected in this cascade
            infection_time = infection_time_arr[0]
            t_i = infection_time

            if c[0][0] != infection_time:
                # Do this only if the target_node wasn't the first node
                # infected in the cascade.
                # If it was the first node (else branch), then we cannot deduce
                # anything about the incoming edges.
                log_sum = 0
                """
                for j in range(len(c)):
                    t_j = c[j][0]
                    alpha_ji = Ai[c[j][1]]
                    #print('alpha_ji haz: {}'.format(alpha_ji))

                    if t_j < t_i:
                        # TODO
                        expr+=logSurvival(t_i,t_j,alpha_ji)
                        #print('log sur2: {}'.format(logSurvival(t_i,t_j,alpha_ji)))
                        log_sum+=hazard(t_i,t_j,alpha_ji)
                        #pass
                """
                # we are only interested in relation between parent and child
                alpha_ji = Ai[c[0][1]]
                t_j = c[0][0]
                expr+=logSurvival(t_i,t_j,alpha_ji)
                #print('log sur2: {}'.format(logSurvival(t_i,t_j,alpha_ji)))
                log_sum+=hazard(t_i,t_j,alpha_ji)
                expr += CVX.log(log_sum)
     #           print('haz expr: {}\n'.format(expr))
    print('log expr: {}\n'.format(expr))
    try:
        prob = CVX.Problem(CVX.Maximize(expr), constraints)
        res = prob.solve(verbose=True,max_iters=500)
        probs.append(prob)
        results.append(res)
        #if prob.status in [CVX.OPTIMAL, CVX.OPTIMAL_INACCURATE]:
        A[:, target_node] = np.asarray(Ai.value).squeeze()
        # compare the accuracy
        #print(calc_score(A[:,0:target_node+1],ASol[:,0:target_node+1]))
        #else:
        #    A[:, target_node] = -1
        #print('result: {}'.format(res))
    except BaseException as e:
        print(e)
        A[:, target_node] = -1
    with open('prediction-nodefinite.txt','a') as writer:
        writer.write(json.dumps({'target_node': target_node,'res':res,'alpha': A[:,target_node].tolist()})+'\n')
    #with open('results.txt','a') as writer:
    #    writer.write(res)



#A_soln = np.loadtxt('solution.csv', delimiter=',')
#with open('prediction.txt','w') as writer:
    #writer.write(json.dumps(A.tolist()))
#print(U.calc_score(A, A_soln))
