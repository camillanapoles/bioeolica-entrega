#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 19:02:58 2024

@author: z3538568
"""

import numpy as np
import matplotlib.pyplot as plt

X = np.array([-3,-2,-1,1,2,3])
y = np.array([1, 0, 0, 1, 1, 0])

def sigmoid(x, w, b):    
    return 1/(1 + np.exp(b + w*x))

def celoss(w, b):
    n = y.shape[0]
    s = 0.0
    
    for i in range(n):
        y_hat = sigmoid(X[i], w, b)
        s += y[i]*np.log(y_hat) + (1 - y[i])*np.log(1 - y_hat)
    
    return -s/n

def loss2(w, b):
    n = y.shape[0]
    s = 0.0
    for i in range(n):
        s += (y[i] - sigmoid(X[i], w, b))**2
    
    return s

w_min = -5
w_max = 5
b_min = -10
b_max = 10

w_range = np.arange(w_min, w_max, 0.01)
b_range = np.arange(b_min, b_max, 0.01)

w_grid, b_grid = np.meshgrid(w_range, b_range)
loss_grid = loss2(w_grid, b_grid)
#loss_grid = celoss(w_grid, b_grid)

#%%
fig = plt.figure()
ax = plt.axes(projection='3d')

#ax.plot_wireframe(t1_arr, t2_arr, cost_arr,  color='black')
ax.plot_surface(w_grid, b_grid, loss_grid, cmap='Blues_r', rstride=1, cstride=1, linewidth=0, antialiased=False, edgecolor='none', vmin =np.min(loss_grid), vmax =2*np.max(loss_grid))
ax.set_xlabel(r'$w$', fontsize=20)
ax.set_ylabel(r'$b$', fontsize=20)
ax.set_zlabel(r'$C(\theta)$', fontsize=20)  
ax.view_init(25, -120)

