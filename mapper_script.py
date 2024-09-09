import pygame
import json
import time
import numpy as np
import os
import glob
import map_functions as mf

########################################################
########################################################
########################################################
display = mf.display()
mdata = mf.mapdata()

#fetch the most recent log file
mf.get_latest_logfile(mdata)
#start off with previously collected data
mdata.loadMapData()

bloop = False
while(True):
    #getting user inputs
    if mf.get_inputs(display,mdata):
        break
    
    if not mdata.dataLoaded:
        mdata.loadMapData()

    
    #this code is for detecting journal events and adding to the set of POIs to be displayed
    mf.checkforevent(mdata, display)
    #reading the status file
    d = mf.getstatus(mdata.EDpath+'status.json')
    
    display.drawgrid()
    if "Latitude" in d:#are we in landing range of a planet (OSC or lower)?
        mdata.set_radius(d['PlanetRadius'])
        mdata.set_curpos([d['Latitude'],d['Longitude']])
        mdata.set_heading(d['Heading'])
        if len(mdata.refpos)==0:
            mdata.set_refpos([d['Latitude'],d['Longitude']])
        
        mdata.add_position()
        display.draw_navinfo(mdata)
    display.draw_sampleinfo(mdata)
    display.drawpois(mdata)
    display.draw_headneedle(mdata)
    
    pygame.display.flip()
    time.sleep(.1)

mdata.saveMapData()
