
import osmnx as ox
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import networkx as nx
import os
import areaDef as ar

# fetches expanded bounding box coordinates
bN,bE,bS,bW = ar.bBoxes[1]
# fetches warehouse name
warehouse = ar.warehouse
# fetches start/end point coordinates
N,E,S,W = ar.bBoxes[0]
start = ar.start


# imports open street map graph of area
area = ox.graph_from_bbox(bN,bS,bE,bW, network_type="drive", simplify=True)
P = ox.project_graph(area, to_crs='WGS84')

# identifies and removes duplicate edges between each pair of nodes
parallelEdges = []
for u,v in P.edges():
    if len(P[u][v])>1:
        if [u,v] not in parallelEdges:
            parallelEdges.append([u,v])
for u,v in parallelEdges:
    P.remove_edge(u,v,1)

# for every edge, adds travel method attribute with default as fly and energy consumption with placeholder value=length
for u,v in P.edges():
    length = P[u][v][0]['length']
    nx.set_edge_attributes(P,{(u,v, 0):{'method': 'fly', 'energy':length, 'cost':length, 'oneway': False}})

# plots area map
fig, ax = plt.subplots()
ox.plot_graph(P, bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.5, show=False, close=False, ax = ax)

# saves graph with flight-only energy attributes
ox.save_graphml(P, filepath="graphs\\" + warehouse + "flight.graphml")

def wtBusEdges(route, P):
    # adds travel method and energy consumption attributes to edges of graph P
    # along the route based on energy consumption of hitch-hikinge
    for n in range(len(route)-1):
        u = route[n]
        v = route[n+1]
        length = P[u][v][0]['length']
        nx.set_edge_attributes(P,{(u,v, 0):{'method': 'ride'}})

def nrNodeNrEdge(P, pLat, pLon):
    # efficiently estimates nearest node to each bus stop by  finding its nearest edge
    # then calculating which edge end-node is closest (max distance node -> stop 170m)
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

# creates list of busline stop file names
fileDir = 'busData\\' + warehouse +'LineStops\\'
lineFiles = os.listdir(fileDir)

# creates empty array to store all bus routes
allBusRoutes =[]

# iterates through bus-line file and generates map route based on bus-stop nearest nodes
for fName in lineFiles:
    # loads bus stop id and coordinate data into np array
    data = pd.read_csv(fileDir+fName)
    bStops = np.column_stack((np.array(data['0']), np.array(data['2']),np.array(data['1'])))

    # create list of nearest node to each bus stop
    stopNodes = np.array([ox.nearest_nodes(P, s[2], s[1]) for s in bStops])
    # removes duplicates (in case of close stops with same nearest node)
    stopNodes = list(dict.fromkeys(stopNodes))
    
    busRoute = []
    # iterates through the bus stop nodes
    for i in range(len(stopNodes)-1):
        
        try:
            # finds a path between consecutive nodes
            path = nx.shortest_path(P, stopNodes[i], stopNodes[i+1], weight='length')[:-1]
        except:
            # if there is no path (bus route leaves and re-enters the graph)
            # ends route section and adds it to bus routes array
            busRoute.append(stopNodes[i])
            allBusRoutes.append(busRoute)
            # creates new empty section
            busRoute = []
        else:
            # if there is a path >1km also ends route section and adds it to bus routes array
            if nx.shortest_path_length(P, stopNodes[i], stopNodes[i+1], weight='length') > 1000:
                busRoute.append(stopNodes[i])
                allBusRoutes.append(busRoute)
                busRoute = []
            # if there is a path <1km adds it the current section of the bus route
            else:
                busRoute = busRoute + path
    # adds the final stop node to the route section
    busRoute.append(stopNodes[-1])
    allBusRoutes.append(busRoute)

for route in allBusRoutes:
    # updates energy consumption in all bus route sections
    wtBusEdges(route, P)
    ox.plot_graph_route(P, route,bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.5,
                        orig_dest_size=10, show=False, close=False, ax = ax, route_color='r', route_node_size=0, route_linewidth=1)

# saves graph with flight and hitch-hike energy attributes
ox.save_graphml(P, filepath="graphs\\" + warehouse +"ride.graphml")

plt.show()
