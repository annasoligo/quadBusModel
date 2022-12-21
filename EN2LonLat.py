from pyproj import Proj, transform
import pandas as pd


v84 = Proj(proj="latlong",towgs84="0,0,0",ellps="WGS84")
v36 = Proj(proj="latlong", k=0.9996012717, ellps="airy",
        towgs84="446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894")
vgrid = Proj(init="world:bng")

def EN2LL(eastings, northings):
    vlon36, vlat36 = vgrid(eastings, 
                           northings, 
                           inverse=True)
    converted = transform(v36, v84, vlon36, vlat36)
    lon = converted[0]
    lat = converted[1]
    return lon, lat

def LL2EN(longitude, latitude):
    pass
