#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 13:39:27 2020

@author: root
"""

#%% User input

lon_lim = [-98.5,-60.0]
lat_lim = [10.0,45.0]

#cycle = '2019090118'
#cycle = '2019083018'
cycle = '2019082800'
#cycle = '2019082918'

delta_lon = 0 # delta longitude around hurricane track to calculate
               # statistics
Nini = 0 # 0 is the start of forecating cycle (2019082800)
      # 1 is 6 hours of forecasting cycle   (2019082806)
      # 2 is 12 hours ...... 20 is 120 hours 

Nend = 22 # indicates how far in the hurricabe track you want
          # include in the analysis. This is helpful if for ex:
          # you onl want to analyse the portion of the track
          # where the storm intensifies
          # 22 corresponds to all the hurricane track forecasted in a cycle
#Nend = 13

cycle = '2019082800'

delta_lon = 0 # delta longitude around hurricane track to calculate
               # statistics
Nini = 0 # 0 is the start of forecating cycle (2019082800)
      # 1 is 6 hours of forecasting cycle   (2019082806)
      # 2 is 12 hours ...... 20 is 120 hours 

Nend = 22 # indicates how far in the hurricabe track you want
          # include in the analysis. This is helpful if for ex:
          # you onl want to analyse the portion of the track
          # where the storm intensifies
          # 22 corresponds to all the hurricane track forecasted in a cycle
#Nend = 13

# Bathymetry file
bath_file = '/home/aristizabal/bathymetry_files/GEBCO_2014_2D_-100.0_0.0_-10.0_50.0.nc'

# KMZ file best track Dorian
kmz_file_Dorian = '/home/aristizabal/KMZ_files/al052019_best_track-5.kmz'

# url for GOFS 3.1
url_GOFS = 'http://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_93.0/ts3z'

# figures
folder_fig = '/home/aristizabal/Figures/'

# folder nc files POM
folder_pom19 =  '/home/aristizabal/HWRF2019_POM_Dorian/'
folder_pom20 =  '/home/aristizabal/HWRF2020_POM_Dorian/'

# folde HWRF2020_HYCOM
folder_hycom20 = '/home/aristizabal/HWRF2020_HYCOM_Dorian/'

###################

# folder nc files POM
folder_pom_oper = folder_pom19 + 'HWRF2019_POM_dorian05l.' + cycle + '_pom_files_oper/'
folder_pom_exp = folder_pom20 + 'HWRF2020_POM_dorian05l.'  + cycle + '_pom_files_exp/'
prefix_pom = 'dorian05l.' + cycle + '.pom.00'

pom_grid_oper = folder_pom_oper + 'dorian05l.' + cycle + '.pom.grid.nc'
pom_grid_exp = folder_pom_exp + 'dorian05l.' + cycle + '.pom.grid.nc'

# Dorian track files
hwrf_pom_track_oper = folder_pom_oper + 'dorian05l.' + cycle + '.trak.hwrf.atcfunix'
hwrf_pom_track_exp = folder_pom_exp + 'dorian05l.' + cycle + '.trak.hwrf.atcfunix'

# folder nc files hwrf
folder_hwrf_pom19_oper = folder_pom19 + 'HWRF2019_POM_dorian05l.' + cycle + '_grb2_to_nc_oper/'
folder_hwrf_pom20_exp = folder_pom20 + 'HWRF2020_POM_dorian05l.' + cycle + '_grb2_to_nc_exp/'

##################
# folder ab files HYCOM
folder_hycom_exp = folder_hycom20 + 'HWRF2020_HYCOM_dorian05l.' + cycle + '_hycom_files_exp/'
prefix_hycom = 'dorian05l.' + cycle + '.hwrf_rtofs_hat10_3z'

#Dir_HMON_HYCOM = '/Volumes/aristizabal/ncep_model/HMON-HYCOM_Michael/'
Dir_HMON_HYCOM = '/home/aristizabal/ncep_model/HWRF-Hycom-WW3_exp_Michael/'
# RTOFS grid file name
hycom_grid_exp = Dir_HMON_HYCOM + 'hwrf_rtofs_hat10.basin.regional.grid'

# Dorian track files
hwrf_hycom_track_exp = folder_hycom_exp + 'dorian05l.' + cycle + '.trak.hwrf.atcfunix'

# folder nc files hwrf
folder_hwrf_hycom20_exp = folder_hycom20 + 'HWRF2020_HYCOM_dorian05l.' + cycle + '_grb2_to_nc_exp/'

#%%
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import netCDF4
from datetime import datetime
import matplotlib.dates as mdates
import os
import os.path
import glob
import seawater as sw
import cmocean

import sys
sys.path.append('/home/aristizabal/NCEP_scripts')
from utils4HYCOM import readBinz, readgrids

# Increase fontsize of labels globally
plt.rc('xtick',labelsize=14)
plt.rc('ytick',labelsize=14)
plt.rc('legend',fontsize=14)

#%% Get storm track from HWRF/POM output

def get_storm_track_POM(file_track):

    ff = open(file_track,'r')
    f = ff.readlines()
    
    latt = []
    lont = []
    lead_time = []
    for l in f:
        lat = float(l.split(',')[6][0:4])/10
        if l.split(',')[6][4] == 'N':
            lat = lat
        else:
            lat = -lat
        lon = float(l.split(',')[7][0:5])/10
        if l.split(',')[7][4] == 'E':
            lon = lon
        else:
            lon = -lon
        latt.append(lat)
        lont.append(lon)
        lead_time.append(int(l.split(',')[5][1:4]))
    
    latt = np.asarray(latt)
    lont = np.asarray(lont)
    lead_time, ind = np.unique(lead_time,return_index=True)
    lat_track = latt[ind]
    lon_track = lont[ind]  

    return lon_track, lat_track, lead_time

#%% Reading POM temperature and salinity for the N time step in forecasting cycle
# following an along track

def get_profiles_from_POM(N,folder_pom,prefix,lon_track,lat_track,\
                                          lon_pom,lat_pom,zlev_pom,zmatrix_pom):   
    
    pom_ncfiles = sorted(glob.glob(os.path.join(folder_pom,prefix+'*.nc')))   
    file = pom_ncfiles[N]
    pom = xr.open_dataset(file)
    tpom = pom['time'][:]
    timestamp_pom = mdates.date2num(tpom)[0]
    time_POM = mdates.num2date(timestamp_pom)
    
    oklon = np.round(np.interp(lon_track,lon_pom[0,:],np.arange(len(lon_pom[0,:])))).astype(int)
    oklat = np.round(np.interp(lat_track,lat_pom[:,0],np.arange(len(lat_pom[:,0])))).astype(int)
    
    temp_POM_along_track = np.empty((len(zlev_pom),len(oklat)))
    temp_POM_along_track[:] = np.nan
    salt_POM_along_track = np.empty((len(zlev_pom),len(oklat)))
    salt_POM_along_track[:] = np.nan
    zmatrix_POM_along_track = np.empty((len(zlev_pom),len(oklat)))
    zmatrix_POM_along_track[:] = np.nan
    dens_POM_along_track = np.empty((len(zlev_pom),len(oklat)))
    dens_POM_along_track[:] = np.nan
    for x,lonn in enumerate(oklon):
        print(x)
        temp_POM_along_track[:,x] = np.asarray(pom['t'][0,:,oklat[x],oklon[x]])
        salt_POM_along_track[:,x] = np.asarray(pom['s'][0,:,oklat[x],oklon[x]])
        zmatrix_POM_along_track[:,x] = zmatrix_pom[oklat[x],oklon[x],:]
        dens_POM_along_track[:,x] = np.asarray(pom['rho'][0,:,oklat[x],oklon[x]])
        
    temp_POM_along_track[temp_POM_along_track==0] = np.nan
    salt_POM_along_track[salt_POM_along_track==0] = np.nan
    dens_POM_along_track = dens_POM_along_track * 1000 + 1000 
    dens_POM_along_track[dens_POM_along_track == 1000.0] = np.nan   
    
    return temp_POM_along_track,salt_POM_along_track,dens_POM_along_track,zmatrix_POM_along_track, time_POM

#%%    
def get_profiles_from_HYCOM(N,folder_hycom,prefix,lon_track,lat_track,\
                   lon_hycom,lat_hycom,var):

    afiles = sorted(glob.glob(os.path.join(folder_hycom,prefix+'*.a')))    
    file = afiles[N]
    
    #Reading time stamp
    year = int(file.split('/')[-1].split('.')[1][0:4])
    month = int(file.split('/')[-1].split('.')[1][4:6])
    day = int(file.split('/')[-1].split('.')[1][6:8])
    hour = int(file.split('/')[-1].split('.')[1][8:10])
    dt = int(file.split('/')[-1].split('.')[3][1:])
    timestamp_hycom = mdates.date2num(datetime(year,month,day,hour)) + dt/24
    time_hycom = mdates.num2date(timestamp_hycom)
    
    # Interpolating lat_track and lon_track into HYCOM grid
    oklon = np.round(np.interp(lon_track+360,lon_hycom[0,:],np.arange(len(lon_hycom[0,:])))).astype(int)
    oklat = np.round(np.interp(lat_track,lat_hycom[:,0],np.arange(len(lat_hycom[:,0])))).astype(int)
    
    # Reading 3D variable from binary file 
    var_hyc = readBinz(file[:-2],'3z',var)
    var_hycom = var_hyc[oklat,oklon,:].T
    
    time_hycom = np.asarray(time_hycom)
    
    return var_hycom, time_hycom

#%% Reading temperature and salinity from DF on target_time following an along track    

def get_profiles_from_GOFS(DF,target_time,lon_track,lat_track):

    depth = np.asarray(DF.depth[:])
    tt_G = DF.time
    t_G = netCDF4.num2date(tt_G[:],tt_G.units)
    oklon = np.round(np.interp(lon_track+360,DF.lon,np.arange(len(DF.lon)))).astype(int)
    oklat = np.round(np.interp(lat_track,DF.lat,np.arange(len(DF.lat)))).astype(int)
    okt = np.where(mdates.date2num(t_G) == mdates.date2num(target_time))[0][0]
    
    temp_along_track = np.empty((len(depth),len(oklon)))
    temp_along_track[:] = np.nan
    salt_along_track = np.empty((len(depth),len(oklon)))
    salt_along_track[:] = np.nan
    for x,lonn in enumerate(oklon):
        print(x)
        temp_along_track[:,x] = np.asarray(DF.water_temp[okt,:,oklat[x],oklon[x]])
        salt_along_track[:,x] = np.asarray(DF.salinity[okt,:,oklat[x],oklon[x]])
    
    return temp_along_track, salt_along_track

#%%
def MLD_temp_and_dens_criteria(dt,drho,time,depth,temp,salt,dens):

    MLD_temp_crit = np.empty(temp.shape[1]) 
    MLD_temp_crit[:] = np.nan
    Tmean_temp_crit = np.empty(temp.shape[1]) 
    Tmean_temp_crit[:] = np.nan
    Smean_temp_crit = np.empty(temp.shape[1]) 
    Smean_temp_crit[:] = np.nan
    Td_temp_crit = np.empty(temp.shape[1]) 
    Td_temp_crit[:] = np.nan
    MLD_dens_crit = np.empty(temp.shape[1])
    MLD_dens_crit[:] = np.nan
    Tmean_dens_crit = np.empty(temp.shape[1])
    Tmean_dens_crit[:] = np.nan
    Smean_dens_crit = np.empty(temp.shape[1]) 
    Smean_dens_crit[:] = np.nan
    Td_dens_crit = np.empty(temp.shape[1]) 
    Td_dens_crit[:] = np.nan
    for t in np.arange(temp.shape[1]):
        if depth.ndim == 1:
            d10 = np.where(depth >= 10)[0][0]
        if depth.ndim == 2:
            d10 = np.where(depth[:,t] >= -10)[0][-1]
        T10 = temp[d10,t]
        delta_T = T10 - temp[:,t] 
        ok_mld_temp = np.where(delta_T <= dt)[0]
        rho10 = dens[d10,t]
        delta_rho = -(rho10 - dens[:,t])
        ok_mld_rho = np.where(delta_rho <= drho)[0]
        
        if ok_mld_temp.size == 0:
            MLD_temp_crit[t] = np.nan
            Td_temp_crit[t] = np.nan
            Tmean_temp_crit[t] = np.nan
            Smean_temp_crit[t] = np.nan            
        else:                             
            if depth.ndim == 1:
                MLD_temp_crit[t] = depth[ok_mld_temp[-1]]
                ok_mld_plus1m = np.where(depth >= depth[ok_mld_temp[-1]] + 1)[0][0]                 
            if depth.ndim == 2:
                MLD_temp_crit[t] = depth[ok_mld_temp[-1],t]
                ok_mld_plus1m = np.where(depth >= depth[ok_mld_temp[-1],t] + 1)[0][0]
            Td_temp_crit[t] = temp[ok_mld_plus1m,t]
            Tmean_temp_crit[t] = np.nanmean(temp[ok_mld_temp,t])
            Smean_temp_crit[t] = np.nanmean(salt[ok_mld_temp,t])
                
        if ok_mld_rho.size == 0:
            MLD_dens_crit[t] = np.nan
            Td_dens_crit[t] = np.nan
            Tmean_dens_crit[t] = np.nan
            Smean_dens_crit[t] = np.nan           
        else:
            if depth.ndim == 1:
                MLD_dens_crit[t] = depth[ok_mld_rho[-1]]
                ok_mld_plus1m = np.where(depth >= depth[ok_mld_rho[-1]] + 1)[0][0] 
            if depth.ndim == 2:
                MLD_dens_crit[t] = depth[ok_mld_rho[-1],t]
                ok_mld_plus1m = np.where(depth >= depth[ok_mld_rho[-1],t] + 1)[0][0] 
            Td_dens_crit[t] = temp[ok_mld_plus1m,t]        
            Tmean_dens_crit[t] = np.nanmean(temp[ok_mld_rho,t])
            Smean_dens_crit[t] = np.nanmean(salt[ok_mld_rho,t]) 

    return MLD_temp_crit,Tmean_temp_crit,Smean_temp_crit,Td_temp_crit,\
           MLD_dens_crit,Tmean_dens_crit,Smean_dens_crit,Td_dens_crit

#%% Read POM grid

print('Retrieving coordinates from POM')
POM_grid_oper = xr.open_dataset(pom_grid_oper,decode_times=False)
lon_pom_oper = np.asarray(POM_grid_oper['east_e'][:])
lat_pom_oper = np.asarray(POM_grid_oper['north_e'][:])
zlev_pom_oper = np.asarray(POM_grid_oper['zz'][:])
hpom_oper = np.asarray(POM_grid_oper['h'][:])
zmatrix = np.dot(hpom_oper.reshape(-1,1),zlev_pom_oper.reshape(1,-1))
zmatrix_pom_oper = zmatrix.reshape(hpom_oper.shape[0],hpom_oper.shape[1],zlev_pom_oper.shape[0])

POM_grid_exp = xr.open_dataset(pom_grid_exp,decode_times=False)
lon_pom_exp = np.asarray(POM_grid_exp['east_e'][:])
lat_pom_exp = np.asarray(POM_grid_exp['north_e'][:])
zlev_pom_exp = np.asarray(POM_grid_exp['zz'][:])
hpom_exp = np.asarray(POM_grid_exp['h'][:])
zmatrix = np.dot(hpom_exp.reshape(-1,1),zlev_pom_exp.reshape(1,-1))
zmatrix_pom_exp = zmatrix.reshape(hpom_exp.shape[0],hpom_exp.shape[1],zlev_pom_exp.shape[0])
        
#%% Reading HYCOM grid

# Reading lat and lon
lines_grid = [line.rstrip() for line in open(hycom_grid_exp+'.b')]
lon_hycom = np.array(readgrids(hycom_grid_exp,'plon:',[0]))
lat_hycom = np.array(readgrids(hycom_grid_exp,'plat:',[0]))

# Extracting the longitudinal and latitudinal size array
idm=int([line.split() for line in lines_grid if 'longitudinal' in line][0][0])
jdm=int([line.split() for line in lines_grid if 'latitudinal' in line][0][0])

afiles = sorted(glob.glob(os.path.join(folder_hycom_exp,prefix_hycom+'*.a')))

# Reading depths
lines=[line.rstrip() for line in open(afiles[0][:-2]+'.b')]
z = []
for line in lines[6:]:
    if line.split()[2]=='temp':
        #print(line.split()[1])
        z.append(float(line.split()[1]))
depth_HYCOM_exp = np.asarray(z) 

nz = len(depth_HYCOM_exp) 

#%% Read GOFS 3.1 grid

print('Retrieving coordinates from GOFS')
GOFS = xr.open_dataset(url_GOFS,decode_times=False) 

tt_G = GOFS.time
t_G = netCDF4.num2date(tt_G[:],tt_G.units)
lat_G = np.asarray(GOFS.lat[:])
lon_G = np.asarray(GOFS.lon[:]) 
depth_GOFS = np.asarray(GOFS.depth[:])

#%% Get Dorian track from models

lon_forec_track_pom_oper, lat_forec_track_pom_oper, lead_time_pom_oper = get_storm_track_POM(hwrf_pom_track_oper)

lon_forec_track_pom_exp, lat_forec_track_pom_exp, lead_time_pom_exp = get_storm_track_POM(hwrf_pom_track_exp)

lon_forec_track_hycom_exp, lat_forec_track_hycom_exp, lead_time_hycom_exp = get_storm_track_POM(hwrf_hycom_track_exp)

#%% Reading POM operational temperature and salinity for time step Nini in forecast cycle 2018082800
# following a band around the forecasted storm track by HWRF/POM
'''
for N in np.arange(Nini,Nend-4,4):
    print(N)
    
    dlon = 0.1
    nlevels = int(2*delta_lon /dlon) + 1
    
    lon_bnd = np.linspace(lon_forec_track_pom_oper[2*N:2*Nend-1]-delta_lon,lon_forec_track_pom_oper[2*N:2*Nend-1]+delta_lon,nlevels) 
    lon_band = lon_bnd.ravel()
    lat_bd = np.tile(lat_forec_track_pom_oper[2*N:2*Nend-1],lon_bnd.shape[0])
    lat_bnd = lat_bd.reshape(lon_bnd.shape[0],lon_bnd.shape[1])
    lat_band = lat_bnd.ravel()
    
    dist_along_track = np.cumsum(np.append(0,sw.dist(lat_bnd[0],lon_bnd[0],units='km')[0]))
    
    temp_POM_band_oper , salt_POM_band_oper, dens_POM_band_oper,\
        zmatrix_POM_band_oper, time_POM = \
            get_profiles_from_POM(N,folder_pom_oper,prefix_pom,lon_band,lat_band,\
                                          lon_pom_oper,lat_pom_oper,zlev_pom_oper,zmatrix_pom_oper)
    
             
    color_map = cmocean.cm.thermal
    dist_matrix = np.tile(dist_along_track,(zmatrix_POM_band_oper.shape[0],1))
           
    okm = depth_GOFS <= 200 
    #min_val = np.floor(np.min([np.nanmin(tempg_gridded[okg]),np.nanmin(target_temp_GOFS[okm])]))
    #max_val = np.ceil(np.max([np.nanmax(tempg_gridded[okg]),np.nanmax(target_temp_GOFS[okm])]))
        
    #nlevels = max_val - min_val + 1
    #kw = dict(levels = np.linspace(min_val,max_val,nlevels))
    kw = dict(levels = np.linspace(16,31,16))
    
    fig, ax = plt.subplots(figsize=(12, 2))     
    cs = plt.contourf(dist_matrix,zmatrix_POM_band_oper,temp_POM_band_oper,cmap=color_map,**kw)
    plt.contour(dist_matrix,zmatrix_POM_band_oper,temp_POM_band_oper,[26],colors='k')
    plt.plot(dist_matrix[:,8],np.linspace(-200,0,dist_matrix.shape[0]),'.-k')
    cs = fig.colorbar(cs, orientation='vertical') 
    cs.ax.set_ylabel('($^oC$)',fontsize=14,labelpad=15)
    ax.set_ylim(-200, 0)
    ax.set_ylabel('Depth (m)',fontsize=14) 
    ax.set_xlabel('Distance Along Track (km)',fontsize=14)
    plt.title('Along Forecasted Track ' + 'Temperature '  + 'POM Operational on '+ str(time_POM)[0:13] + ' (cycle= ' + cycle +')',fontsize=14)  
     
    
    file = folder_fig + ' ' + 'along_track_temp_top200_POM_oper_' + cycle + '_' + str(time_POM)[0:13]
    plt.savefig(file,bbox_inches = 'tight',pad_inches = 0.1) 
    '''                    
#%% Reading POM experimental temperature and salinity for time step Nini in forecast cycle 2018082800
# following a band around the forecasted storm track by HWRF/POM
'''
for N in np.arange(Nini,Nend-4,4):
    print(N)
    
    dlon = 0.1
    nlevels = int(2*delta_lon /dlon) + 1
    
    lon_bnd = np.linspace(lon_forec_track_pom_oper[2*N:2*Nend-1]-delta_lon,lon_forec_track_pom_oper[2*N:2*Nend-1]+delta_lon,nlevels) 
    lon_band = lon_bnd.ravel()
    lat_bd = np.tile(lat_forec_track_pom_oper[2*N:2*Nend-1],lon_bnd.shape[0])
    lat_bnd = lat_bd.reshape(lon_bnd.shape[0],lon_bnd.shape[1])
    lat_band = lat_bnd.ravel()
    
    dist_along_track = np.cumsum(np.append(0,sw.dist(lat_bnd[0],lon_bnd[0],units='km')[0]))
    
    temp_POM_band_exp , salt_POM_band_exp, dens_POM_band_exp, \
    zmatrix_POM_band_exp, time_POM = \
    get_profiles_from_POM(N,folder_pom_exp,prefix_pom,lon_band,lat_band,\
                                              lon_pom_exp,lat_pom_exp,zlev_pom_exp,zmatrix_pom_exp)
        
    color_map = cmocean.cm.thermal
    dist_matrix = np.tile(dist_along_track,(zmatrix_POM_band_oper.shape[0],1))
           
    okm = depth_GOFS <= 200 
    #min_val = np.floor(np.min([np.nanmin(tempg_gridded[okg]),np.nanmin(target_temp_GOFS[okm])]))
    #max_val = np.ceil(np.max([np.nanmax(tempg_gridded[okg]),np.nanmax(target_temp_GOFS[okm])]))
        
    #nlevels = max_val - min_val + 1
    #kw = dict(levels = np.linspace(min_val,max_val,nlevels))
    kw = dict(levels = np.linspace(16,31,16))
    
    fig, ax = plt.subplots(figsize=(12, 2))     
    cs = plt.contourf(dist_matrix,zmatrix_POM_band_exp,temp_POM_band_exp,cmap=color_map,**kw)
    plt.contour(dist_matrix,zmatrix_POM_band_exp,temp_POM_band_exp,[26],colors='k')
    plt.plot(dist_matrix[:,8],np.linspace(-200,0,dist_matrix.shape[0]),'.-k')
    cs = fig.colorbar(cs, orientation='vertical') 
    cs.ax.set_ylabel('($^oC$)',fontsize=14,labelpad=15)
    
    ax.set_ylim(-200, 0)
    ax.set_ylabel('Depth (m)',fontsize=14)
    ax.set_xlabel('Distance Along Track (km)',fontsize=14)
    plt.title('Along Forecasted Track ' + 'Temperature ' + 'POM Experimental on '+str(time_POM)[0:13] + ' (cycle= ' + cycle +')',fontsize=14)  
     
    
    file = folder_fig + ' ' + 'along_track_temp_top200_POM_exp_' + cycle + '_' + str(time_POM)[0:13]
    plt.savefig(file,bbox_inches = 'tight',pad_inches = 0.1)  
'''
#%%
'''
for N in np.arange(Nini,Nend-4,4):
    print(N)
    
    dlon = 0.1
    nlevels = int(2*delta_lon /dlon) + 1
    
    lon_bnd = np.linspace(lon_forec_track_pom_oper[2*N:2*Nend-1]-delta_lon,lon_forec_track_pom_oper[2*N:2*Nend-1]+delta_lon,nlevels) 
    lon_band = lon_bnd.ravel()
    lat_bd = np.tile(lat_forec_track_pom_oper[2*N:2*Nend-1],lon_bnd.shape[0])
    lat_bnd = lat_bd.reshape(lon_bnd.shape[0],lon_bnd.shape[1])
    lat_band = lat_bnd.ravel()
    
    dist_along_track = np.cumsum(np.append(0,sw.dist(lat_bnd[0],lon_bnd[0],units='km')[0]))    

    temp_HYCOM_band_exp, time_HYCOM = \
        get_profiles_from_HYCOM(N,folder_hycom_exp,prefix_hycom,\
                            lon_band,lat_band,lon_hycom,lat_hycom,'temp')
        
    color_map = cmocean.cm.thermal

    okm = depth_HYCOM_exp <= 200 
    #min_val = np.floor(np.min([np.nanmin(tempg_gridded[okg]),np.nanmin(target_temp_GOFS[okm])]))
    #max_val = np.ceil(np.max([np.nanmax(tempg_gridded[okg]),np.nanmax(target_temp_GOFS[okm])]))
        
    #nlevels = max_val - min_val + 1
    #kw = dict(levels = np.linspace(min_val,max_val,nlevels))
    kw = dict(levels = np.linspace(16,31,16))
    
    fig, ax = plt.subplots(figsize=(12, 2))     
    cs = plt.contourf(dist_along_track,-depth_HYCOM_exp,temp_HYCOM_band_exp,cmap=color_map,**kw)
    plt.contour(dist_along_track,-depth_HYCOM_exp,temp_HYCOM_band_exp,[26],colors='k')
    plt.plot(np.tile(dist_along_track[8],len(np.linspace(-200,0))),np.linspace(-200,0),'.-k')
    cs = fig.colorbar(cs, orientation='vertical') 
    cs.ax.set_ylabel('($^oC$)',fontsize=14,labelpad=15)
    
    ax.set_ylim(-200, 0)
    ax.set_ylabel('Depth (m)',fontsize=14)
    ax.set_xlabel('Distance Along Track (km)',fontsize=14)
    plt.title('Along Forecasted Track ' + 'Temperature ' + 'HYCOM Experimental on '+ str(time_HYCOM)[0:13] + ' (cycle= ' + cycle +')',fontsize=14)  
     
    
    file = folder_fig + ' ' + 'along_track_temp_top200_HYCOM_exp_' + cycle + '_' + str(time_HYCOM)[0:13]
    plt.savefig(file,bbox_inches = 'tight',pad_inches = 0.1)  
'''        
#%% Reading GOFS temperature and salinity for firts time step in forecast cycle 2018082800
# following a band around the forecasted storm track by HWRF/POM     
'''
target_time = [datetime(2019,8,28,0),datetime(2019,8,29,0),datetime(2019,8,30,0),\
               datetime(2019,8,31,0),datetime(2019,9,1,0)]

for n,N in enumerate(np.arange(Nini,Nend-4,4)):
    print(N)
    
    dlon = 0.1
    nlevels = int(2*delta_lon /dlon) + 1
    
    lon_bnd = np.linspace(lon_forec_track_pom_oper[2*N:2*Nend-1]-delta_lon,lon_forec_track_pom_oper[2*N:2*Nend-1]+delta_lon,nlevels) 
    lon_band = lon_bnd.ravel()
    lat_bd = np.tile(lat_forec_track_pom_oper[2*N:2*Nend-1],lon_bnd.shape[0])
    lat_bnd = lat_bd.reshape(lon_bnd.shape[0],lon_bnd.shape[1])
    lat_band = lat_bnd.ravel()
    
    dist_along_track = np.cumsum(np.append(0,sw.dist(lat_bnd[0],lon_bnd[0],units='km')[0]))  
    
    DF = GOFS

    temp_GOFS_band , _ = \
    get_profiles_from_GOFS(DF,target_time[n],lon_band,lat_band)
    
    color_map = cmocean.cm.thermal
       
    okm = depth_GOFS <= 200 
    #min_val = np.floor(np.min([np.nanmin(tempg_gridded[okg]),np.nanmin(target_temp_GOFS[okm])]))
    #max_val = np.ceil(np.max([np.nanmax(tempg_gridded[okg]),np.nanmax(target_temp_GOFS[okm])]))
        
    #nlevels = max_val - min_val + 1
    #kw = dict(levels = np.linspace(min_val,max_val,nlevels))
    kw = dict(levels = np.linspace(16,31,16))
    
    dist_along_track = np.cumsum(np.append(0,sw.dist(lat_bnd[0],lon_bnd[0],units='km')[0]))
    
    fig, ax = plt.subplots(figsize=(12, 2))     
    cs = plt.contourf(dist_along_track,-depth_GOFS,temp_GOFS_band,cmap=color_map,**kw)
    plt.contour(dist_along_track,-depth_GOFS,temp_GOFS_band,[26],colors='k')
    plt.plot(np.tile(dist_along_track[8],len(np.linspace(-200,0))),np.linspace(-200,0),'.-k')
    cs = fig.colorbar(cs, orientation='vertical') 
    cs.ax.set_ylabel('($^oC$)',fontsize=14,labelpad=15)
    ax.set_ylim(-200, 0)
    ax.set_ylabel('Depth (m)',fontsize=14)
    ax.set_xlabel('Distance Along Track (km)',fontsize=14)
    plt.title('Along Forecasted Track ' + 'Temperature ' + 'GOFS 3.1 on '+ str(target_time[n])[0:13] + ' (cycle= ' + cycle +')',fontsize=14)  
    
    file = folder_fig + ' ' + 'along_track_temp_top200_GOFS_' + cycle + '_' + str(target_time[n])[0:13]
    plt.savefig(file,bbox_inches = 'tight',pad_inches = 0.1)  
'''

#%% time series temp ML

target_time = [datetime(2019,8,28,0),datetime(2019,8,29,0),datetime(2019,8,30,0),\
               datetime(2019,8,31,0),datetime(2019,9,1,0)]

dt = 0.2
drho = 0.125

for n,N in enumerate(np.arange(Nini,Nend-4,4)):
    print(N)
    
    dlon = 0.1
    nlevels = int(2*delta_lon /dlon) + 1
    
    lon_bnd = np.linspace(lon_forec_track_pom_oper[2*N:2*Nend-1]-delta_lon,lon_forec_track_pom_oper[2*N:2*Nend-1]+delta_lon,nlevels) 
    lon_band = lon_bnd.ravel()
    lat_bd = np.tile(lat_forec_track_pom_oper[2*N:2*Nend-1],lon_bnd.shape[0])
    lat_bnd = lat_bd.reshape(lon_bnd.shape[0],lon_bnd.shape[1])
    lat_band = lat_bnd.ravel()
    
    dist_along_track = np.cumsum(np.append(0,sw.dist(lat_bnd[0],lon_bnd[0],units='km')[0]))
    
    # POM oper
    temp_POM_band_oper , salt_POM_band_oper, dens_POM_band_oper,\
        zmatrix_POM_band_oper, time_POM = \
            get_profiles_from_POM(N,folder_pom_oper,prefix_pom,lon_band,lat_band,\
                                          lon_pom_oper,lat_pom_oper,zlev_pom_oper,zmatrix_pom_oper)
    # POM exp            
    temp_POM_band_exp , salt_POM_band_exp, dens_POM_band_exp, \
    zmatrix_POM_band_exp, time_POM = \
    get_profiles_from_POM(N,folder_pom_exp,prefix_pom,lon_band,lat_band,\
                                              lon_pom_exp,lat_pom_exp,zlev_pom_exp,zmatrix_pom_exp)
    # HYCOM exp    
    temp_HYCOM_band_exp, time_HYCOM = \
    get_profiles_from_HYCOM(N,folder_hycom_exp,prefix_hycom,\
                        lon_band,lat_band,lon_hycom,lat_hycom,'temp')
        
    salt_HYCOM_band_exp, time_HYCOM = \
    get_profiles_from_HYCOM(N,folder_hycom_exp,prefix_hycom,\
                        lon_band,lat_band,lon_hycom,lat_hycom,'salinity')
        
    nx = temp_HYCOM_band_exp.shape[1]
    dens_HYCOM_band_exp = sw.dens(salt_HYCOM_band_exp,temp_HYCOM_band_exp,np.tile(depth_HYCOM_exp,(nx,1)).T)
    
    # GOFS     
    temp_GOFS_band , salt_GOFS_band = \
    get_profiles_from_GOFS(GOFS,target_time[n],lon_band,lat_band)
    
    nx = temp_GOFS_band.shape[1]
    dens_GOFS_band = sw.dens(salt_GOFS_band,temp_GOFS_band,np.tile(depth_GOFS,(nx,1)).T)
    
    # POM oper
    MLD_temp_crit_POM_oper, _, _, _, MLD_dens_crit_POM_oper, Tmean_dens_crit_POM_oper, \
    Smean_dens_crit_POM_oper, _ = \
    MLD_temp_and_dens_criteria(dt,drho,time_POM,zmatrix_POM_band_oper,temp_POM_band_oper,\
                               salt_POM_band_oper,dens_POM_band_oper)
        
    # POM exp
    MLD_temp_crit_POM_exp, _, _, _, MLD_dens_crit_POM_exp, Tmean_dens_crit_POM_exp, \
    Smean_dens_crit_POM_exp, _ = \
    MLD_temp_and_dens_criteria(dt,drho,time_POM,zmatrix_POM_band_exp,temp_POM_band_exp,\
                               salt_POM_band_exp,dens_POM_band_exp)
    # HYCOM exp
    depth=depth_HYCOM_exp
    temp=np.asarray(temp_HYCOM_band_exp)
    salt=np.asarray(salt_HYCOM_band_exp)
    dens=np.asarray(dens_HYCOM_band_exp)
    time = time_HYCOM 
    temp[temp>100]=np.nan
    salt[salt>100]=np.nan
    dens[dens<1000]=np.nan
    
    MLD_temp_crit_HYCOM_exp, _, _, _, MLD_dens_crit_HYCOM_exp, Tmean_dens_crit_HYCOM_exp, \
    Smean_dens_crit_HYCOM_exp, _ = \
    MLD_temp_and_dens_criteria(dt,drho,time_HYCOM,depth,temp,salt,dens)    
        
    # GOFS 3.1 
    MLD_temp_crit_GOFS, _, _, _, MLD_dens_crit_GOFS, Tmean_dens_crit_GOFS, Smean_dens_crit_GOFS, _ = \
    MLD_temp_and_dens_criteria(dt,drho,target_time,depth_GOFS,temp_GOFS_band,salt_GOFS_band,dens_GOFS_band)          

    fig,ax = plt.subplots(figsize=(12, 2))
    plt.plot(dist_along_track,Tmean_dens_crit_GOFS,'--o',color='indianred',label='GOFS 3.1')
    plt.plot(dist_along_track,Tmean_dens_crit_POM_oper,'-X',color='mediumorchid',label='POM Oper')
    plt.plot(dist_along_track,Tmean_dens_crit_POM_exp,'-^',color='teal',label='POM Exp')
    plt.plot(dist_along_track,Tmean_dens_crit_HYCOM_exp,'-H',color='orange',label='HYCOM Exp')
    plt.plot(np.tile(dist_along_track[8],len(np.linspace(28,30))),np.linspace(28,30),'.-k')
    plt.ylabel('($^oC$)',fontsize = 14)
    plt.xlabel('Distance Along Track (km)',fontsize = 14)
    plt.title('Mixed Layer Temperature Dorian Track on ' + str(time_POM)[0:13] + ' (cycle= ' + cycle +')',fontsize=16)
    plt.grid(True)
    plt.legend(loc='upper left',bbox_to_anchor=(1,0.9))
    
    file = folder_fig + 'temp_ml_' + cycle + ' ' + str(time_POM)[0:13]
    plt.savefig(file,bbox_inches = 'tight',pad_inches = 0.1) 
        