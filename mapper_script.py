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

#from an example found at https://www.youtube.com/watch?v=ndtFoWWBAoE

eventline = []
bloop = False

fname = 'C:/Users/amhau/Saved Games/Frontier Developments/Elite Dangerous/Status.json'

for cmdr in ['amhau']:
    fpath = 'C:/Users/' + cmdr + '/Saved Games/Frontier Developments/Elite Dangerous/'

    flist = list(filter(os.path.isfile,
                    glob.glob(fpath + '*.log')))

# import time

latest_logfile = max(flist, key=os.path.getctime)
##get name of current body, also get the last line of the current log file
mdata.lastLine = None
with open(latest_logfile,'r') as f:
    lines = f.readlines()
for line in reversed(lines):
    if mdata.lastLine==None:
        mdata.lastLine=line

    eventline = json.loads(line)
    if "event" in eventline:
        if "Body" in eventline:
            mdata.currentBody = eventline["Body"]
    if len(mdata.currentBody)>0:
        break

#start off with previously collected data
mdata.loadMapData()

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
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            #zoom in by increasing ppm (const)
            display.increment_ppm()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            #zoom out by decreasing ppm (const)
            display.decrement_ppm()
            #raise SystemExit
    if bloop:
        break

    display.drawgrid()
    if not mdata.dataLoaded:
        mdata.loadMapData()

    #this code is for detecting journal events and adding to the set of POIs to be displayed
    mf.checkforevent(latest_logfile, mdata, display)
    #reading the status file
    d = mf.getstatus(fname)
    
    if "Latitude" in d:
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
    time.sleep(2)

mdata.saveMapData()
