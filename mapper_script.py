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
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            #raise SystemExit
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            bloop = True
            #raise SystemExit
        #elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
        elif event.type == pygame.MOUSEWHEEL and event.y == 1:
            #zoom in by increasing ppm (const)
            display.increment_ppm()
        #elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
        elif event.type == pygame.MOUSEWHEEL and event.y == -1:
            #zoom out by decreasing ppm (const)
            display.decrement_ppm()
            #raise SystemExit
    if bloop:
        break
    
    display.drawgrid()
    if not mdata.dataLoaded:
        mdata.loadMapData()

    
    #this code is for detecting journal events and adding to the set of POIs to be displayed
    mf.checkforevent(mdata, display)
    #reading the status file
    d = mf.getstatus(mdata.EDpath+'status.json')
    
    if "Latitude" in d:#are we in landing range of a planet (OSC or lower)?
        mdata.set_radius(d['PlanetRadius'])
        mdata.set_curpos([d['Latitude'],d['Longitude']])
        mdata.set_heading(d['Heading'])
        if len(mdata.refpos)==0:
            mdata.set_refpos([d['Latitude'],d['Longitude']])
        
        mdata.add_position()
        display.drawpois(mdata)
        display.drawinfo(mdata)

    selfxys = [[-5,5],
               [5,5],
               [0,-8]]
    cosh = np.cos(mdata.h_rad)
    sinh = np.sin(mdata.h_rad)
    
    rotxys = [(s[0]*cosh-s[1]*sinh,s[0]*sinh+s[1]*cosh) for s in selfxys]

    selfsym = (rotxys[0]+display.centpos,
               rotxys[1]+display.centpos,
               rotxys[2]+display.centpos)
    pygame.draw.polygon(surface=display.screen,points=selfsym,color=(255,255,200),width=2)
    pygame.display.flip()
    time.sleep(.1)

mdata.saveMapData()
