# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 23:58:09 2020

@author: owner
"""
# SGD SVRG GD on logistic regression

# %matplotlib inline 
import numpy as np
from matplotlib import pyplot as plt
from sklearn import datasets
from sklearn.preprocessing import normalize
from scipy.special import expit as sigmoid

#%% synthetic data generation

N = 10000
dim = 50
lamda = 1e-4
np.random.seed(1)
w = np.matrix(np.random.multivariate_normal([0.0]*dim, np.eye(dim))).T
X = np.matrix(np.random.multivariate_normal([0.0]*dim, np.eye(dim), size = N))
X = np.matrix(normalize(X, axis=1, norm='l2'))
y = 2 * (np.random.uniform(size = (N, 1)) < sigmoid(X*w)) - 1


#%% Real-World Forrest Covertype Dataset
file = datasets.load_svmlight_file('covtype.libsvm.binary.scale',n_features=54)
y = np.matrix(file[1]).T
X = file[0].todense()
train_idx = np.random.randint(0,X.shape[0], int(0.1*X.shape[0]))
y = y[train_idx,:]
X = np.matrix(normalize(X[train_idx,:], axis=1, norm='l2'))
lamda = 1e-4
N, dim = X.shape
print('dataset of size: {} X {}'.format(N,dim))


#%% parameter
L = lamda + 1/4;
num_pass = 50

#%% GD
## Define the objective and gradient oracles. 
def obj(w):
    return 1/N * np.sum( np.log(1 + np.exp(-np.multiply(y, (X*w)))) ) + 1/2 * lamda * (w.T*w)

def grad(w,X,y):
    return 1/X.shape[0] * X.T * np.multiply( y, sigmoid(np.multiply(y, X*w)) - 1) + lamda*w

## Gradient Descent
w = np.matrix([0.0]*dim).T
obj_GD = []
max_iter = num_pass
for t in range(0, max_iter):
    obj_val = obj(w)
    w = w - 2/(L+lamda) * grad(w, X, y)
    
    obj_GD.append(obj_val.item())
    
print('Objective function value is: {}'.format(obj_GD[-1]))


## Plot objective vs. iteration
t = np.arange(0,num_pass)
# plt.plot(t, np.ones((len(t),1))*opt, 'k', linewidth = 2, label = 'Optimal')
plt.plot(t, np.array(obj_GD), 'b', linewidth = 2, label = 'GD')
plt.legend(prop={'size':12})
plt.xlabel('No. of Passes')
plt.ylabel('Objective')

#%% SGD
## Stochastic Gradient Descent
w = np.matrix([0.0]*dim).T
obj_SGD = []
batch = 50
for s in range(num_pass):
    obj_val = obj(w)
    obj_SGD.append(obj_val.item())   
    max_iter = int(N/batch)
    for t in range(max_iter):
        rand_idx = np.random.randint(0, N-1,batch) 
        yt = y[rand_idx, 0]
        xt = X[rand_idx, :]
        # gamma = 1/(lamda*(t+1))             # theoretical stepsize
        gamma = 0.1/(lamda*(t+100))           # better stepsize
        w = w -  gamma * grad(w,xt,yt)

print('Objective function value is: {}'.format(obj_SGD[-1]))       


## Plot objective vs. iteration
t = np.arange(0, num_pass)
#plt.plot(t, np.ones((len(t),1))*opt, 'k', linewidth = 2, label = 'Optimal')
plt.plot(t, np.array(obj_SGD), 'g', linewidth = 2, label = 'SGD')
plt.legend(prop={'size':12})
plt.xlabel('No. of Passes')
plt.ylabel('Objective')


#%% SVRG
w = np.matrix([0.0]*dim).T
obj_SVRG = []
passes_SVRG = []

Epochs = 15
k = 2
batch = 50
for s in range(Epochs):
    obj_val = obj(w)
    obj_SVRG.append(obj_val.item())
    passes_SVRG.append(s*k+s)
    
    w_prev = w
    gradient = grad(w, X, y)

    obj_SVRG.append(obj_val.item())
    passes_SVRG.append(s*k+s+1)    
    
    max_iter = int(k*N/batch)
    for t in range(max_iter):
        rand_idx = np.random.randint(0, N-1, batch)
        yt = y[rand_idx, 0]
        xt = X[rand_idx, :]
        gamma = 1/L
        w = w - gamma * (grad(w,xt,yt) - grad(w_prev,xt,yt) + gradient)

print('Objective function value is: {}'.format(obj_SVRG[-1]))       


#%% Plot objective vs. iteration
t = passes_SVRG
#plt.plot(t, np.ones((len(t),1))*opt, 'k', linewidth = 2, label = 'Optimal')
plt.plot(t, np.array(obj_SVRG), 'r', linewidth = 2, label = 'SVRG')
plt.legend(prop={'size':12})
plt.xlabel('No. of Passes ')
plt.ylabel('Objective')


#%% 
## Compare GD, SGD, SVRG
passes_GD = range(len(obj_GD))
passes_SGD = range(len(obj_SGD))
fig, ax = plt.subplots(figsize = (9, 6))
ax.semilogy(passes_GD, np.array(obj_GD), color='b', linewidth=2, label='GD')
ax.semilogy(passes_SGD, np.array(obj_SGD), color='g', linewidth=2, label='SGD')
ax.semilogy(passes_SVRG, np.array(obj_SVRG), color='r', linewidth=2, label='SVRG')
plt.legend(prop={'size':12})
plt.xlabel('No. of Passes ')
plt.ylabel('Objective Error')

