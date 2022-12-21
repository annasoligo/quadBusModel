
import osmnx as ox
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import networkx as nx
import math
import os
import areaDef as ar

def wtBusEdges(route, P):
    for n in range(len(route)-1):
        u = route[n]
        v = route[n+1]
        length = P[u][v][0]['length']
        nx.set_edge_attributes(P,{(u,v, 0):{'method': 'ride', 'energy':riKwhM*length}})

def nrNodeNrEdge(P, pLat, pLon):

    u, v, key = ox.nearest_edges(P, pLat, pLon)

    ux = P.nodes[u]['x']-pLon
    uy = P.nodes[u]['y']-pLat
    vx = P.nodes[v]['x']-pLon
    vy = P.nodes[v]['y']-pLat
    du = (ux*ux+uy*uy)
    dv = (vx*vx+vy*vy)
    if du < dv:
        nodeid = u
    else:
        nodeid = v
    return nodeid

def endRtSect(routesMatrix, routeSection, i, stopNodes):
    routeSection.append(stopNodes[i])
    # the current section of the route is added to the bus routes array
    routesMatrix.append(routeSection)
    print(routeSection)
    # creates new empty section
    return routesMatrix, []


bN,bS,bE,bW = ar.bBox
N,S,E,W = ar.N, ar.S, ar.E, ar.W
start = ar.start
flKwhM = 0.000024
riKwhM = 0.00000719

fig, ax = plt.subplots()
area = ox.graph_from_bbox(bN,bS,bE,bW, network_type="drive", simplify=True)
P = ox.project_graph(area, to_crs='WGS84')
ox.plot_graph(P, bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.5, show=False, close=False, ax = ax)

parallelEdges = []

for u,v in P.edges():
    if len(P[u][v])>1:
        if [u,v] not in parallelEdges:
            parallelEdges.append([u,v])
    length = P[u][v][0]['length']
    nx.set_edge_attributes(P,{(u,v, 0):{'method': 'fly', 'energy':flKwhM*length, 'oneway': False}})

for u,v in parallelEdges:
    P.remove_edge(u,v,1)

ox.save_graphml(P, filepath="flight2.graphml")

# creates list of busline stop file names
fileDir = 'areaLineStops/'
lineFiles = os.listdir(fileDir)

# creates empty array to store all bus routes
allBusRoutes =[]

# iterates through busline stop files
for fName in lineFiles:
    # loads bus stop id and coordinate data into np array
    data = pd.read_csv(fileDir+fName)
    bStops = np.column_stack((np.array(data['0']), np.array(data['2']),np.array(data['1'])))

    # creates a list of nearest nodes to each bus stop
    stopNodes = np.array([ox.nearest_nodes(P, s[2], s[1]) for s in bStops])
    #stopNodes = np.array([nrNodeNrEdge(P, s[2], s[1]) for s in bStops])
    # removes duplicates (in case of close stops with same nearest node)
    stopNodes = list(dict.fromkeys(stopNodes))
    
    # creates empty array to store this bus route
    busRoute = []
    # iterates through the bus stop nodes
    for i in range(len(stopNodes)-1):
        # tries to find a route between the node and the next node, returns the route minus the next node
        try:
            path = nx.shortest_path(P, stopNodes[i], stopNodes[i+1], weight='length')
        # executed if there is no route (bus route leaves and re-enters the graph)
        except:
            print('fail')
            allBusRoutes, busRoute = endRtSect(allBusRoutes, busRoute, i, stopNodes)
        else:
            print('success')
            print(path)
            if (nx.shortest_path_length(P, stopNodes[i], stopNodes[i+1], weight='length') > 1000):
               allBusRoutes, busRoute = endRtSect(allBusRoutes, busRoute, i, stopNodes) 
            else:
                busRoute = busRoute + path
    allBusRoutes, busRoute = endRtSect(allBusRoutes, busRoute, i, stopNodes)

# plots all bus route sections
for route in allBusRoutes:
    wtBusEdges(route, P)
    ox.plot_graph_route(P, route,bgcolor='none', node_size=0.5, edge_color='black', edge_linewidth= 0.5,
                        orig_dest_size=10, show=False, close=False, ax = ax, route_color='r', route_linewidth=1)

ox.save_graphml(P, filepath="ride2.graphml")

plt.show()
