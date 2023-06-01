# Defines geographic model features:
# Defines a specified warehouse start point and generates a boounding box round it
# Defines functions to convert between British National Grid Eastings/Northings
# and latitude/longitude, to find the geodisic distances between lat/long points,

from scipy.spatial import Voronoi
from pyproj import Proj, transform
from math import *

# Specify warehouse (UUK2 = S, DXE1 = NE, DHA1 = NW)
warehouse = 'UUK2'

# map expansion from start/end coordinates in m
expNS = 500
expEW = 500

# closest warehouse locations to London (eastings, northings - British National Grid system)
whCoords = {'UUK2': [525992, 169591], 'DXE1': [538278, 182093], 'DHA1': [520415, 185628]}
print(whCoords['UUK2'])
# furthest point from London's 3 central Amazon warehouses
centreEN = Voronoi([whCoords['UUK2'], whCoords['DXE1'], whCoords['DHA1']]).vertices[0]

# defines furthest start and end delivery points                         
start = whCoords[warehouse]
end = centreEN

# coordinate system parameters
v84 = Proj(proj="latlong",towgs84="0,0,0",ellps="WGS84")
v36 = Proj(proj="latlong", k=0.9996012717, ellps="airy",
        towgs84="446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894")
vgrid = Proj(init="world:bng")


def EN2LL(EN):
    # converts British National Grid coordinates to latitude and longitude
    vlon36, vlat36 = vgrid(EN[0], 
                           EN[1], 
                           inverse=True)
    converted = transform(v36, v84, vlon36, vlat36)
    lon = converted[0]
    lat = converted[1]
    return lat, lon

def haversine(lon1, lat1, lon2, lat2):
    # implements Haversine formula to find the geodisic distances between points 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2]) 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def getBounds(start, end, expNS, expEW):
    # returns unexpanded and expanded NESW bounds, based on start and end points
    NE = EN2LL([max(start[0], end[0]),max(start[1],end[1])])
    SW = EN2LL([min(start[0], end[0]),min(start[1],end[1])])
    bounds = NE+SW
    exNE = EN2LL([max(start[0], end[0])+expNS,max(start[1],end[1])+expEW])
    exSW = EN2LL([min(start[0], end[0])-expNS,min(start[1],end[1])-expEW])
    expanded = exNE+exSW
    return[bounds, expanded]

# bounding box values 
bBoxes = getBounds(start, end, expNS, expEW)
startLL = EN2LL(start)

