import pygame
import json
import time
import pygame
import numpy as np
import os
import glob
#######################################################################
###################################################################
###################################################################

mapdatpath = 'C:/Users/Salome/Documents/EDlogreader/EDsurfacemapper/mapdata/'

ranges = {'Ale':	150,
        'Amp':	100,
        'Ane':	100,
        'Bac':	500,
        'Bar':	100,
        'Bra':	100,
        'Cac':	300,
        'Cly':	150,
        'Con':	150,
        'Cry':	100,
        'Ele':	1000,
        'Fon':	500,
        'Fru':	150,
        'Fum':	100,
        'Fun':	300,
        'Oss':	800,
        'Rec':	150,
        'Sin':	100,
        'Str':	500,
        'Tub':	800,
        'Tus':	200}

poicolors = [(127,127,0),
              (127,64,64),
              (64,127,64),
              (64,64,127),
              (127,0,127),
              (0,127,127),
              (127,64,0),
              (127,0,64),
              (64,127,0),
              (64,0,127),
              (0,127,64),
              (0,64,127)]

class mapdata:
    def __init__(self,EDpath='',currentBody=''):
        self.currentBody = currentBody
        self.cBsamples = {}
        self.curpos = np.array([])#current position in lat/long
        self.refpos = np.array([])#reference position in lat/long
        self.poslist = []#list of visited points, the 'trace', in lat/long
        self.POIlist = []#list of lat/long POIs with accompanying info
        self.td_pos = []#most recent touchdown location
        self.h_rad = 0#current heading in radians
        self.radius = 0#radius in meters of current body
        self.lastLine = ''#this should really go somewhere else
        self.dataLoaded = False
        self.distance = 0
        self.nlines = 0
        self.heading = ''

        if len(EDpath)==0:
            self.EDpath = os.path.expanduser('~/Saved Games/Frontier Developments/Elite Dangerous/')
        else:
            self.EDpath = EDpath
    
    def set_datafilename(self):
        self.savename = mapdatpath + self.currentBody + '_data.json'
    
    def set_radius(self,radius):
        self.radius = radius
        
    def set_curpos(self,curpos):
        self.curpos = np.array(curpos)

    def set_refpos(self,refpos):
        self.refpos = np.array(refpos)

    def set_heading(self,heading):
        self.heading = str(heading)
        self.h_rad = np.pi*float(heading)/180

    def pos_change(self):#formerly dmoved
        return chordlength(self.refpos[1], self.refpos[0], self.curpos[1], self.curpos[0], self.radius)
    
    def curpos_m(self):#formerly cloc
        return latlong2meter(self.curpos, self.refpos, self.radius)

    def add_position(self):
        d = self.pos_change()
        self.distance+=d
        if d>0:
            if len(self.poslist)==0:
                self.poslist.append(self.curpos)
            else:
                if not np.array_equal(self.poslist[-1],self.curpos):
                    self.poslist.append(self.curpos)
            self.set_refpos(self.curpos)

    def add_cBsample(self,POIname,POItype):
        if POIname in self.cBsamples:
            if POItype==2:
                self.cBsamples[POIname]+=1
        else:
            if POItype==2:
                self.cBsamples[POIname]=1
            else:
                self.cBsamples[POIname]=0

    def add_POI(self,POIname,POItype=0):
        s_n_split = POIname.split()
        if s_n_split[-1] in ["Fumerole","Vent","Geyser","Spout"]:
            POItype = 0
            POIname = s_n_split[-1]
        self.POIlist.append([self.curpos,POIname[0:3],POItype])
        if POIname != "X":
            self.add_cBsample(POIname[0:3],POItype)
    
#start off with previously collected data
    def loadMapData(self):
        if len(self.currentBody)>0:
            self.set_datafilename()
            if os.path.isfile(self.savename):
                with open(self.savename,'r') as f:
                    print('loading saved map data for ' + self.currentBody)
                    line = f.readlines()
                    mapdict = json.loads(line[0])
                    
                    self.poslist = [np.array(pos) for pos in mapdict["pathlist"]]
                    #print('loading dummy value for POI[2]')
                    self.POIlist = [[np.array(pos[0]),pos[1],pos[2]] for pos in mapdict["POIlist"]]

                    for POI in self.POIlist:
                        self.add_cBsample(POI[1],POI[2])
                    self.set_radius(mapdict["radius"])
                    self.set_curpos(self.poslist[-1])
                    self.set_heading(mapdict["heading"])
                    self.set_refpos(mapdict["refpos"])

                    self.dataLoaded = True
    
    def saveMapData(self):
        #de numpyfy data for jsonification
        self.set_datafilename()
        v_poslist = [pos.tolist() for pos in self.poslist]
        v_samposlist = [[pos[0].tolist(),pos[1],pos[2]] for pos in self.POIlist]

        mapdict = {"bodyname":self.currentBody,
                "radius":self.radius,
                "heading":self.heading,
                "refpos":self.refpos.tolist(),
                "pathlist":v_poslist,
                "POIlist":v_samposlist}
        json_object = json.dumps(mapdict)
        
        with open(self.savename, "w") as outfile:
            outfile.write(json_object)

##############
class display:
    def __init__(self,s=600,ppm=0.05,currentBody=''):
        pygame.init()
        self.s = s
        self.centpos = np.array([s/2,s/2])
        self.ppm = ppm#formerly const
        self.text_font = pygame.font.SysFont("Futura", 18)
        self.small_font = pygame.font.SysFont("Futura", 15)

        self.screen = pygame.display.set_mode((s,s))
        self.screen.fill("black")

    def increment_ppm(self):
        self.ppm = np.round((10**.25)*self.ppm,3)
    def decrement_ppm(self):
        self.ppm = np.round(self.ppm/(10**.25),3)

    def drawgrid(self):
        
        self.screen.fill("black")
        if self.ppm <.0025:
            gridres = 100000
        elif self.ppm < .025:
            gridres = 10000
        elif self.ppm < .25:
            gridres = 1000
        elif self.ppm < 2.5:
            gridres = 100
        else:
            gridres = 10

        period = gridres*self.ppm
        if False:
            vs = np.arange(s/2,s,period)

            for v in vs:
                pg.draw.line(surface=surf,color=(70,50,0),start_pos=(v,0),end_pos=(v,s))
                pg.draw.line(surface=surf,color=(70,50,0),start_pos=(0,v),end_pos=(s,v))
                if v>s/2:
                    pg.draw.line(surface=surf,color=(70,50,0),start_pos=(s-v,0),end_pos=(s-v,s))
                    pg.draw.line(surface=surf,color=(70,50,0),start_pos=(0,s-v),end_pos=(s,s-v))
        else:
            for ang in np.arange(0,2*np.pi,np.pi/6):
                aval = round(180*ang/np.pi)
                x = self.s/2 + .9*(self.s/2)*np.sin(ang)
                y = self.s/2 - .9*(self.s/2)*np.cos(ang)
                pygame.draw.line(self.screen,color=(25,20,0),start_pos=self.centpos,end_pos=(x,y))
                self.draw_text(str(aval), self.small_font, (255,255,150),x,y)

            vs = np.arange(period,self.s/2,period)
            rc = 0
            self.vmax = vs[-1]*self.ppm#in pixels, the outer boundary of the map
            for v in vs:#draw equidistance lines
                rc+=gridres
                if gridres<1000:
                    mll = str(rc)
                    if v==vs[-1]:
                        mll=mll+'m'
                else:
                    mll = str(round(rc/1000))
                    if v==vs[-1]:
                        mll=mll+'km'
                pygame.draw.circle(self.screen,color=(70,50,0),center=self.centpos,radius=v,width=1)
                self.draw_text(mll, self.text_font, (255,255,150),self.s/2,self.s/2-v)
            

    def draw_text(self,text, font, text_col, x,y):
        img = font.render(text, True, text_col)
        self.screen.blit(img,(x,y))

    def screen_pos(self,pos,mdata):
        mpos = latlong2meter(pos, mdata.refpos, mdata.radius)
        return self.ppm*mpos + self.centpos - self.ppm*mdata.curpos_m()

    def drawpois(self,mdata):
        for pos in mdata.poslist:
            dpos = self.screen_pos(pos,mdata)
            pygame.draw.circle(self.screen,center=dpos,radius=1,color=[127,32,64])
            #print(pos)
        for poslab in mdata.POIlist:
            ppos = self.screen_pos(poslab[0],mdata)#the coordinate of something scanned
            lab = poslab[1]#the name/label of something scanned
            if lab=="X":
                poicolor = (127,127,0)
            else:
                poicolor = poicolors[list(mdata.cBsamples.keys()).index(lab)]
            if lab in ranges:
                poirad = self.ppm*ranges[lab]
            else:
                poirad = 5
            if poslab[2]==2:
                pygame.draw.circle(self.screen,center=ppos,radius=poirad,color=poicolor,width=1)
            self.draw_text(lab, self.text_font, poicolor, ppos[0],ppos[1])
        for pos in mdata.td_pos:
            tpos = self.screen_pos(pos,mdata)
            pygame.draw.circle(self.screen,center=tpos,width=1,radius=3,color=(127,127,64))
            self.draw_text('TD', self.text_font, (255,255,200), tpos[0],tpos[1])
        
    def drawinfo(self,mdata):
        #body & position stuff, upper-right corner
        lat,long = mdata.curpos
        llstring =    'Lat/Long:  ' + str(np.round(lat,3)) + '/' + str(np.round(long,3))
        self.draw_text(mdata.currentBody, self.text_font, text_col=(250,250,150),x=10,y=10)
        self.draw_text(llstring, self.text_font, text_col=(250,250,150),x=10,y=24)
        self.draw_text('Heading:  ' + mdata.heading, self.text_font, text_col=(250,250,150),x=10,y=38)
        self.draw_text('Distance: ' + str(round(mdata.distance)/1000) + 'km', self.text_font, text_col=(255,245,145),x=10,y=52)

        #collected POI info
        yv = 10
        for key in mdata.cBsamples:
            poicolor = poicolors[list(mdata.cBsamples.keys()).index(key)]
            POIlabel = key + '/' + str(mdata.cBsamples[key])
            self.draw_text(POIlabel, self.text_font, text_col=poicolor,x=self.s - 60,y=yv)
            yv = yv+14

##############
def getstatus(status_file):
    #reading the status file
    f = open(status_file,'r',encoding='utf8')
    statuslines = []
    while len(statuslines)==0:
        statuslines = f.readlines()
    return json.loads(statuslines[0])

def get_latest_logfile(mdata):
    flist = list(filter(os.path.isfile,
                glob.glob(mdata.EDpath + '*.log')))

    # import time

    mdata.latest_logfile = max(flist, key=os.path.getctime)
    ##get name of current body, also get the last line of the current log file
    mdata.lastLine = None
    with open(mdata.latest_logfile,'r') as f:
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

def checkforevent(mapdata, display):
    with open(mapdata.latest_logfile,'r') as f:
        lines = f.readlines()
        nlines = len(lines)
        ldif = min(nlines - mapdata.nlines,3)
        mapdata.nlines = nlines
    
    eventline = []
    for line in [lines[x] for x in list(range(-ldif,0))]:#sometimes new lines might come out faster 
                                                #thanm the main loop would catch, 
                                                #and we just get the last one. This is a neutered fix
                                                #since the fix didn't work.
        if line != mapdata.lastLine:
            mapdata.lastLine = line
            #print(lines[-1])
            eventline = json.loads(mapdata.lastLine)
            if "event" in eventline:
                print(eventline["event"])
                if eventline["event"] in ["CodexEntry","ScanOrganic"]:
                    POItype = 0
                    if eventline["event"]=="CodexEntry":
                        sample_name = eventline['Name_Localised']
                        POItype = 1
                        s_n_split = sample_name.split()
                    if eventline["event"]=="ScanOrganic":
                        if eventline["ScanType"]=="Analyse":
                            print("SampleAnalysed")
                            POItype = -1
                        else:
                            sample_name = eventline['Species_Localised']
                            POItype = 2
                    if len(mapdata.refpos)>0 and POItype>0:
                        mapdata.add_POI(sample_name,POItype=POItype)
                if eventline["event"]=="Touchdown":
                    mapdata.td_pos = [np.array([eventline['Latitude'],eventline['Longitude']])]
                if eventline["event"]=="Liftoff":
                    mapdata.td_pos = []
                    if display.ppm>0.5:
                        display.ppm = .05                
                if eventline["event"]=="FSSDiscoveryScan":
                    mapdata.add_POI("X",POItype=0)
                if eventline["event"]=="Disembark":
                    display.ppm = .889
                if "Body" in eventline and len(mapdata.currentBody)==0:
                    mapdata.currentBody = eventline["Body"]
                if "StartJump" in eventline:
                    mapdata.saveMapData()

###############
def haversine_np(lon1, lat1, lon2, lat2, rad):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    
    All args must be of equal length.    
    radius in meters
    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    
    c = 2 * np.arcsin(np.sqrt(a))
    m = rad * c
    return m

##############
def chordlength(lon1,lat1,lon2,lat2,rad):
    #lon:lambda, lat:phi
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    
    dX = np.cos(lat2)*np.cos(lon2) - np.cos(lat1)*np.cos(lon1)
    dY = np.cos(lat2)*np.sin(lon2) - np.cos(lat1)*np.sin(lon1)
    dZ = np.sin(lat2) - np.sin(lat1)

    dist = rad*np.sqrt(dX**2 + dY**2 + dZ**2)
    return dist

##############
def latlong2meter(coord, refcoord, radius):
    posdif = coord - refcoord
    ddif = chordlength(refcoord[1], refcoord[0], coord[1], coord[0], radius)
    xdif = np.sign(posdif[1])*chordlength(refcoord[1], refcoord[0], coord[1], refcoord[0], radius)
    ydif = np.sign(posdif[0])*chordlength(refcoord[1], refcoord[0], refcoord[1], coord[0], radius)
    dang = np.arctan2(ydif,xdif)
    return np.array([np.cos(dang)*ddif,-np.sin(dang)*(ddif)])