import numpy as np;
import scipy as sp;
import cvxpy as cvx;

# A: numpy object
# C: numpy object
# num_nodes = integer
def estimate_network(A,C,num_nodes,horizon,type_diffusion):
	# make a zero matrix with size num_nodes * num_nodes
	num_cascades = np.zeros((num_nodes,num_nodes))
	A_potential = sp.sparse(np.zeros(A.shape))
	A_bad = sp.sparse(np.zeros(A.shape))
	A_hat = sp.sparse(np.zeros(A.shape))
	total_obj = 0

	for c in range(1,C.shape[1]):
		# get cascades that is  not equal -1
		# active cascades
		idx = C[c,:]!=-1
		# sort the matrix based on the value		
		(val, order)  = np.sort(C[c,idx])
		for i in range(2:length(val)):
			num_cascades[idx[i]] = num_cascades[idx[order[i]]] + 1
			for j in range(1,i-1):
				if type_diffusion == 'exp':
					A_potential[idx[j],idx[i]] = A_potential[idx[j],idx[i]] + val[i] - val[j]
				elif type_diffusion == 'pl' and (val[i] - val[j]) > 1:
					A_potential[idx[j],idc[i]] = A_potential[idx[j],idx[i]] + log (val[i] - val[j])
				elif type_diffusion == 'rayleigh':
					A_potential[idx[j],idx[i]] = A_potential[idx[j],idx[i]] + 0.5 * (val[i]-val[j]) ^ 2


		for j in range(1,num_nodes):
			if length(idx==j) > 0:
				for i in range(1,length(val)):
					if type_diffusion == 'exp':
						A_bad[idx[i],j] = A_bad[idx[i],j] + (horizon-val[i])
					elif type_diffusion == 'pl' and (horizon - val[i]) > 1 :
						A_bad[idx[i],j] = A_bad[idx[i],j] + log(horizon-val[i])
					elif type_diffusion =='rayleigh':
						A_bad[idx[i],j] = A_bad[idx[i].j] + 0.5 * (horizon-val[i])^2


	# convex program per column
	for i in range(1,num_nodes):
		if(num_cascades[i]==0):
			A_hat(:,i) = 0
			continue

		#cvx_begin
		constraints = []
		a_hat = cvx.Variable(num_nodes)
		t_hat = cvx.Variable(num_cascades[i])
		obj = 0
		a_hat[A_potential[:,i]==0] == 0

		for j in range(1,num_nodes):
			if A_potential[j,i] > 0 :
				obj = -a_hat[j] * (A_potential[j,i] +A_bad[j,i]) + obj

		c_act = 1
		for c in range(1,C.shape[1]):
			idx = C[c,:]!=-1
			(val, order) = np.sort[C[c.idx]]
			idx_ord = idx[order]
			cidx = (idx_ord == i)

			if (length(cidx)>0 and cidx > 1):
				if type_diffusion=='exp':
					constraints.append(t_hat[c_act] == sum(a_hat[idx_ord[1:cidx-1]]))
				elif type_diffusion=='pl':
					tdifs = 1./ (val[cidx] -val(1:cidx-1))
					indv = tdifs<1
					tdifs = tdifs[indv]
					constraints.append(t_hat[c_act] <= (tdifs * a_hat[idx_ord[indv]]))
				elif type_diffusion=='rayleigh':
					tdifs = (val[cidx]-val[1:cidx-1])
					constraints.append(t_hat[c_act] <= (tdifs*a_hat[idx_ord[1:cidx-1]]))

				obj = obj + log(t_hat[c_act])

				c_act = c_act + 1

		objective = cvx.Maximize(obj)
		constraints.append(a_hat >= 0)
		prob = cvx.Problem(objective,constraints)
		result = prob.solve();
		A_hat[:,i] = a_hat.value;