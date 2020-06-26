import os
import sys
# import cv2
import numpy as np
import pandas as pd
# import pyabf
import seaborn as sns
import scipy
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.image as mpimg

def p2f(x):
	
	return float(x.strip('%'))/100

def GS_to_df(url):
	csv_export_url = url.replace('/edit#gid=', '/export?format=csv&gid=')
	df = pd.read_csv(csv_export_url)

	return df

def smooth_timeseries(x,y,N=None):
    t, c, k = scipy.interpolate.splrep(x, y, s=0, k=4)
    xmin, xmax = x.min(), x.max()
    smoothed_x = np.linspace(xmin, xmax, N)
    smoothed_y = scipy.interpolate.BSpline(t,c,k,extrapolate=False)

    return smoothed_x, smoothed_y

def binomialCI(successes=None,attempts=None,alpha=0.05):

    from scipy.stats import beta
    import math

    x = successes
    n = attempts    

    # NOTE: the ppf (percent point function) is equivalent to the inverse CDF
    lower = beta.ppf(alpha/2,x,n-x+1)
    if math.isnan(lower):
        lower = 0
    upper = beta.ppf(1-alpha/2,x+1,n-x)
    if math.isnan(upper):
        upper = 1
        
    return lower,upper
    
def CI_plotting(successes,attempts,mean,alpha=0.05):
# For use with ax.errorbar when plotting errors in matplotlib_pyplot. The function ax.error
# useses a y-value as the second input to add or subtract a yerr from. Using the binomialCI
# function above gives only the points where there error bar would end, not the value
# ax.errorbar computes. Why it does this, I have no idea. This function circumvents having to
# add/subtract the mean when plotting
    lower,upper = binomialCI(successes,attempts)

    lower_error = mean - lower
    upper_error = upper - mean

    return lower_error,upper_error

def calculate_ts_derivative(df,ts):
	
	dt = np.gradient(ts)

	df['dt'] = dt

	return df
	
def make_abf_df(abf):
	df = pd.DataFrame()
	df_sweep = []
	df_trigger = []
	df_TTL = []
	for i,sweepNumber in enumerate(abf.sweepList):
		for ii,channel in enumerate(abf.channelList):
			if channel==0:
				abf.setSweep(sweepNumber,channel)
				df_sweep.append(abf.sweepY)
			if channel==1:
				abf.setSweep(sweepNumber,channel)
				df_trigger.append(abf.sweepY)
			if channel==2:
				abf.setSweep(sweepNumber,channel)
				df_TTL.append(abf.sweepY)
	for iii,sweep in enumerate(df_sweep):
		df['sweep'+str(iii)] = df_sweep[iii]
	for iv,trigger in enumerate(df_trigger):
		df['trigger'+str(iv)] = df_trigger[iv]
	for v,TTL in enumerate(df_TTL):
		df['TTL'+str(v)] = df_TTL[v]
	df['time'] = abf.sweepX
	channels = ['sweep','trigger','TTL']
	for u,unit in enumerate(abf.adcUnits):
		df[channels[u]+' units'] = abf.adcUnits[u]
	df['datapath'] = abf.abfFilePath
	df['protocol'] = abf.protocol
	df['NoS'] = abf.sweepNumber

	return df

def add_sweep_avg_to_df(df):

	sweeps = []
	df_sweep_avg = []
	for ii,col in enumerate(df.columns):
		if 'sweep' in col:
			sweeps.append(col)
	dft = df[sweeps]
	for idx,trial in dft.iterrows():
		trial_avg = np.mean(trial)
		df_sweep_avg.append(trial_avg)
	df['sweep_avg'] = df_sweep_avg

	return df
	    
# def add_TTL_avg_to_df:
	# df_TTL = []
	# df_average_TTL = []
# 	for iv,sweep_TTL in enumerate(df_TTL):
# 		df['sweep'+str(iv)+'_TTL'] = df_TTL[iv]
#     TTL_mean = np.mean((trial['sweep0_TTL'],
#                         trial['sweep1_TTL'],
#                         trial['sweep2_TTL'],
#                         trial['sweep3_TTL'],
#                         trial['sweep4_TTL']))
#     df_average_TTL.append(TTL_mean)  
	# for ii,sweepNumber in enumerate(abf.sweepList):
	#     abf.setSweep(sweepNumber,2)
	#     df_TTL.append(abf.sweepY)
# df['average_TTL'] = df_average_TTL

# def load_image(path,dtype=float):
#     image = mpimg.imread(path).astype(dtype)

#     return image

def load_image(path):
	image = cv2.imread(path)
	image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

	return image

def make_gs_df(url):

	csv_export_url = url.replace('/edit#gid=', '/export?format=csv&gid=')

	df = pd.read_csv(csv_export_url)

	return df

def str_flt(array):
    new_array = array.astype(np.float)
    
    return new_array