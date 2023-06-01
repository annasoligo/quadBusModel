import osmnx as ox
import matplotlib.pyplot as plt
import os
import networkx as nx
import pandas as pd
import numpy as np



P = ox.graph_from_place('London', network_type='drive')
fig, ax = plt.subplots()
allBusRoutes =[]
ox.plot_graph(P, bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.5, show=False, close=False, ax = ax)

for warehouse in ['UUK2','DXE1', 'DHA1']:
    print(warehouse)

    fileDir = 'busData\\' + warehouse +'LineStops\\'

    lineFiles = os.listdir(fileDir)
    

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
    ox.plot_graph_route(P, route,bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.5,
                        orig_dest_size=0, show=False, close=False, ax = ax, route_color='r', route_node_size=0, route_linewidth=1)

plt.show()
