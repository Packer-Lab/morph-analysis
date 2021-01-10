
# coding: utf-8

# ## This notebook uses the pygsheets library in tandem with existing Google spreadsheets and the Google API to update a spreadsheet of analysed variables everytime a new Ephys recording from a cell is made (.paq file). 
# #### New cells are appended to the end of this sheet, which is then reloaded and modified with data from additional cells.
# ### pygsheets can be installed through pip and takes the path to a .JSON file as an authorization/credential in order to use the API. This file can be created through the [Google Developers Console](https://console.developers.google.com/cloud-resource-manager). 

# ### Get ur shit together

# In[1]:


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import ams_utilities as au # a custom library from the Allen with useful, basic functions
import ams_paq_utilities as apu # a custom library specifically to deal with PackIO and .paq files. THE MEAT LIVES HERE

get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')

get_ipython().run_line_magic('matplotlib', 'notebook')

sns.set()
sns.set_style('white')
params = {'legend.fontsize': 'x-large',
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
plt.rcParams.update(params)
# thanks Jimmy


# ### Load Cell GSheets as a DataFrame

# In[2]:


'''This url is for links into PackStation for all the whole-cell recordings I've made. 
This is easier and faster than trying to index through all of the datafiles individually'''

url = 'https://docs.google.com/spreadsheets/d/1ziOx80em0ZhmMmSjKePYbOq3K6sHcOapfHjy9S4oDbk/edit#gid=940626433'
all_cells = au.make_gs_df(url)
all_cells


# In[3]:


'''Remove all cells that don't meet a qualitative criterion as being 'good.' It's very possible that some shit cells
are in my current analyses, but these can be easily currated out.
'''
good_cells = all_cells[(all_cells['PackEphys']=='Yes')&(all_cells['Ephys Quality']=='Good')].reset_index()


# In[4]:


#This url links to the existing gsheet containing the analyzed data of recorded cells

params_url = 'https://docs.google.com/spreadsheets/d/1ziOx80em0ZhmMmSjKePYbOq3K6sHcOapfHjy9S4oDbk/edit#gid=1828339698'
param_df = au.make_gs_df(params_url)
param_df = param_df.rename(columns={'Unnamed: 0':'metric'})


# In[5]:


# Index through the 'good' datapaths and pull out the .paq files

datapaths = []

for path in good_cells['Ephys Path']:
    for filename in os.listdir(path):
        if 'allparams' in filename:
            datapaths.append(os.path.join(path,filename))


# ### Analyse EVERYTHING
# 
# #### This is where the magic happens. Create an empty dict, convert the .paq files to python dataframes, add some columns, then run through an analysis of all the variables I've included so far. Takes forever to run if starting from scratch but just about 10s for every new cell added

# In[6]:


df_all = {}

for i,path in enumerate(datapaths):
    df = apu.make_paq_df_multi(datapaths[i])
    df['mouseID'] = good_cells['Pseudo ID'][i]
    df_all[''.join(df.mouseID.unique()+'_'+df.Cell.unique())] = df
    
    '''This bit is important. Essentially measures the length of the parameter dataframe and asks
    if the new cells would be indexed higher if added. If so, add them. If not, fuck off.'''
    
    if i>(len(param_df.keys())-2):
        params = apu.make_param_df(df)
        param_df[i] = pd.DataFrame(np.insert(params[params.columns[0]].values,0,params.columns[0]))
        
    else:
        pass


# In[7]:


param_df_T = au.transpose_raw_df(param_df,cols='metric',drop='metric')


# In[8]:


#TA DAAAA
param_df_T.tail(25)


# ### Add Ephys Metrics to Google Spreadsheet
# 
# #### This is where the API is actually used. In essence, pygsheets uses the credentials .JSON to access the Google authentification server. This is then validated and allows me to read and write a gsheet of my choice and post it to a drive location.

# In[9]:


import pygsheets

#authorization
gc = pygsheets.authorize(service_file=r"Z:\ashelton\JSON\Cell Data-3a412a97c7b7.json")


# In[10]:


# Find the sheet I want to use in the list of available sheets

sh = gc.open('Claustrum_Mice')


# In[11]:


# determine the sheet in the gsheet I'll open and write over

wks = sh[2]


# In[12]:


# write over existing gsheet with the newly updated dataframe

wks.set_dataframe(param_df,(1,1))


# ## Some actual analysis. Because I've only collected about 80 good cells so far, I haven't dived into PCA yet. But some basic stuff is possible:
# 
# ### Plot Traces (2x Rheobase) for Each Cell
# #### This is good for getting a basic idea of the quality of the recordings

# In[13]:


df = pd.concat(df_all)

mice = df.mouseID.unique()


# In[14]:


mice


# In[15]:


for mouse in mice[len(mice)-6:len(mice)]:
#     if mouse == 'AS113':
        df_mouse = df[df.mouseID==mouse]
        cells = df_mouse.Cell.unique()
        fig,ax=plt.subplots(1,len(cells),sharex=True,sharey=True,figsize=(15,5))
        sns.despine()

        for i,cell in enumerate(cells):
            if len(cells)>1:
                df_cell = df_mouse[df_mouse.Cell==cell]
                ax[i].set_title(mouse+' '+cell)
                ax[i].plot(df_cell['time'][290000:315000].values,
                        df_cell['Voltage'][290000:315000].values,
                        color='r',
                        lw=0.5)


            else:
                df_cell = df_mouse[df_mouse.Cell==cell]
                ax.set_title(mouse+' '+cell)
                ax.plot(df_cell['time'][270000:315000].values,
                        df_cell['Voltage'][270000:315000].values,
                        color='r',
                        lw=0.5)

            fig.tight_layout()


# ### Quick analysis using the updated analyzed variables gsheet. Good for looking at all the cells at once

# In[16]:


dfp = param_df.transpose()
dfp.columns = dfp.iloc[0]
dfp = dfp.drop('metric')
dfp.keys()


# In[17]:


dfp


# In[18]:


fig,ax=plt.subplots(1,3,figsize=(12,4))
plt.style.use(u'default')

metrics = ['Input_Resistance (MOhm)','AP_1/2_Width (ms)','Max FR (spikes/sec)','Rheobase (pA)','Onset_Voltage (mV)','AP1_abs_amp (mV)']

x1 = au.str_flt(dfp[metrics[0]].values)
y1 = au.str_flt(dfp[metrics[1]].values)

x2 = au.str_flt(dfp[metrics[2]].values)
y2 = au.str_flt(dfp[metrics[3]].values)

x3 = au.str_flt(dfp[metrics[4]].values)
y3 = au.str_flt(dfp[metrics[5]].values)

ax[0].scatter(x1,y1,facecolors='none',edgecolor='k')
ax[0].set_xlabel(metrics[0])
ax[0].set_ylabel(metrics[1])

fit = np.polyfit(x1.flatten(),y1.flatten(),1)
fit_fn = np.poly1d(fit) 
ax[0].plot(x1,fit_fn(x1),'r')



# ax[0].plot(a,b,dashes=[0.5,1])

ax[1].scatter(x2,y2,facecolors='none',edgecolor='k')
ax[1].set_xlabel(metrics[2])
ax[1].set_ylabel(metrics[3])

fit = np.polyfit(x2.flatten(),y2.flatten(),1)
fit_fn = np.poly1d(fit) 
ax[1].plot(x2,fit_fn(x2),'r')

ax[2].scatter(x3,y3,facecolors='none',edgecolor='k')
ax[2].set_xlabel(metrics[4])
ax[2].set_ylabel(metrics[5])

fit = np.polyfit(x3.flatten(),y3.flatten(),1)
fit_fn = np.poly1d(fit) 
ax[2].plot(x3,fit_fn(x3),'r')




fig.subplots_adjust(wspace=0.4)
fig.tight_layout()

