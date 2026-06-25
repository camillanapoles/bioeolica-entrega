#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 22:56:40 2021

@author: Sarat Moka

Python code for generating 3d-plots of 
a convex function with a (unique) global minimum 
and a non-convex function with several local extrema.

"""

import numpy as np
import matplotlib.pyplot as plt

textsize = 20

#mycmap = plt.get_cmap('gist_earth')
#mycmap = plt.get_cmap('magma')

# =============================================================================
# Covex and non-convex functions
# =============================================================================
f_non_convex = lambda t: 3*((1 - t[0])**2)*np.exp(-t[0]**2 - (t[1] + 1)**2) - 10*(t[0]/5 - t[0]**3 - t[1]**5)*np.exp(-t[0]**2 - t[1]**2) - (1/3)*np.exp(-(t[0]+1)**2 - t[1]**2)
f_convex = lambda t: t[0]**2 + t[1]**2


#%%
# =============================================================================
# This cell plots a convex function
# =============================================================================

t1_range = np.arange(-2.5, 2.5, 0.01)
t2_range = np.arange(-2.5, 2.5, 0.01)

A = np.meshgrid(t1_range, t2_range)
Z = f_convex(A)
X, Y = np.meshgrid(t1_range, t2_range)

fig = plt.figure()
ax = plt.axes(projection='3d')
ax.plot_surface(X, Y, Z, rstride=1, cstride=1, linewidth=5,  antialiased=False, edgecolor='none', vmin =np.min(Z), vmax =2*np.max(Z))
#ax.plot_surface(X, Y, Z, linewidth=2, rcount=50, ccount=50, antialiased=False, edgecolor='none', vmin =np.min(Z), vmax =1.5*np.max(Z))

ax.view_init(22, -56)
ax.set_xlabel(r'$\theta_1$', fontsize=textsize)
ax.set_ylabel(r'$\theta_2$', fontsize=textsize)
#plt.xticks(size=textsize)
#plt.yticks(size=textsize)
plt.show()

#%%
# =============================================================================
# This cell plots a non-convex function
# =============================================================================

t1_range = np.arange(-2.5, 2.5, 0.01)
t2_range = np.arange(-2.5, 2.5, 0.01)

A = np.meshgrid(t1_range, t2_range)
Z = f_non_convex(A)
X, Y = np.meshgrid(t1_range, t2_range)

fig = plt.figure()
ax = plt.axes(projection='3d')
ax.plot_surface(X, Y, Z, rstride=1, cstride=1, linewidth=5, antialiased=False, edgecolor='none', vmin =np.min(Z), vmax =2*np.max(Z), alpha=1)
ax.view_init(22, -56)
ax.set_xlabel(r'$\theta_1$', fontsize=textsize)
ax.set_ylabel(r'$\theta_2$', fontsize=textsize)
plt.show()