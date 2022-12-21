import numpy as np
from scipy.spatial import Voronoi

# This file defines the longitude and latitude of the furthest start and end points
# It generates bounding box coordinates for an area around this based on
# a N/S and a E/W expansion


# closest Amazon warehouses to London
# latitude, longitude
coords = {'UUK2':[51.411353, -0.189772], 'DXE1': [51.520839, -0.008333], 'DHA1':[51.556695, -0.264460]}
# eastings, northings
amUUK2 = [525992, 169591]
amDXE1 = [538278, 182093]
amDHA1 = [520415, 185628]

warehouse = 'UUK2'

# furthest point from London's 3 central Amazon warehouses
vor = Voronoi([amUUK2, amDXE1, amDHA1])

# print(vor.vertices)
# centre in lat/long, converted online

vorCen = (51.499316,-0.150560)

# map N/S expansion from start and end coordinates in km
expNS = 0.5
# map E/W expansion from start and end coordinates in km
expEW = 0.5

# assigns start and furthest end points
end = vorCen
start = coords[warehouse]

# finds bounding value in each direction
N = max(start[0], end[0])
E = max(start[1], end[1])
S = min(start[0], end[0])
W = min(start[1], end[1])

def expandMap(N, S, dNS, E, W, dEW):
    #expands bounding box defined by coordinates above
    #by the distances dNS and dEW km respectively
    N = round(N+dNS/110.574,6)
    S = round(S-dNS/110.574,6)
    mNS = (N+S)/2
    E = round(E+dEW/(110.574*np.cos(np.deg2rad(mNS))),6)
    W = round(W-dEW/(110.574*np.cos(np.deg2rad(mNS))),6)
    return[N,S,E,W]

# returns bounding box values 
bBox= expandMap(N, S, expNS, E, W, expEW)

# display graph of area
