import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import areaDef as ar
from areaDef import haversine
import numpy as np
from math import *
import areaDef as ar


# defines system parameters
busTolEn = 0.0264           # energy penalty for added bus landing + takeoff
bN,bE,bS,bW = ar.bBoxes[1]  # bounding box for routes
N,E,S,W = ar.bBoxes[0]      # bounding box for delivery locations
start = ar.startLL           # start location (specified warehouse)
nSGraphs = 10               # number of route comparison graphs to show
nSEff = 200                 # number of routes to compare energy consumption
nSLens = 200                # number of routes to compare flight/ride distances
warehouse = ar.warehouse    # warehouse name
gc1 = 'red'                 # graph colour 1
gc2 = 'darkOrange'          # graph colour2


def loadGraph(fName):
    # loads graph and processes energy metrics
    P = ox.load_graphml(fName + '.graphml')
    for u,v in P.edges():
        P[u][v][0]['energy'] = float(P[u][v][0]['energy'])
    return P

def genRanCoords(maxN, maxS, maxE, maxW, nCoords):
    # generates a n pairs of random coordinate within the defined area
    # returns n*2 array
    rangeLat  = maxN-maxS
    rangeLon = maxE-maxW
    randLats = (np.random.rand(nCoords,1)*rangeLat)+maxS
    randLons = (np.random.rand(nCoords,1)*rangeLon)+maxW
    randCoords = np.column_stack((randLats, randLons))
    return randCoords

def minEnergyRoute(graph, start, end):
    # uses Dijkstras based on the energy attribute of edges to return the
    # lowest energy route from start to end, its estimated energy consumption,
    # and the distances flown and hitch-hiked
    path = nx.shortest_path(graph, start, end, weight='energy')
    energy = nx.shortest_path_length(graph, start, end, weight='energy')
    lenRide, lenFly = 0, 0
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        if graph[u][v][0]['method'] == 'ride':
            lenRide += graph[u][v][0]['length']/1000
        else:
            lenFly += graph[u][v][0]['length']/1000
    routeData = (path, energy, lenRide, lenFly)
    return routeData

def graphTitle(method, energy, length):
    title = method + ": " + str(round(energy,3)) + "kwh\n" + str(round(length,3)) +"km\n"
    return title

#ec = ['r' if d['method']=='ride'  else 'black' for u,v,k,d in flightP.edges(keys=True, data=True)]
#ox.plot_graph(flightP, bgcolor='none', node_size=0, edge_color=ec, edge_linewidth= 0.5, show=False, close=False, ax = ax1)

def compareRoutes(graph1, name1, graph2, name2, nSamples, destBounds, startCoord, penalty2):
    # plots maps of the lowest energy drone routes with and without hitchhiking 
    # for n random destination coordinatess
    startNode = ox.nearest_nodes(graph1, startCoord[1], startCoord[0])
    N,S,E,W = destBounds
    randCoords = genRanCoords(N,S,E,W,nSamples)
    fig, ax = plt.subplots(1,nSamples)
    for i in range(nSamples):
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        path1, energy1, lenR1, lenF1 = minEnergyRoute(graph1, startNode, dest)
        path2, energy2, lenR2, lenF2 = minEnergyRoute(graph2, startNode, dest)
        energy2+=2*penalty2
        energy1+=penalty2
        axi = ax[i]
        ox.plot_graph(graph1, bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.3, show=False, close=False, ax = axi)
        ox.plot_graph_route(graph1, path1, orig_dest_size=10, show=False, close=False, ax = axi, route_color=gc1, route_linewidth=2)
        ox.plot_graph_route(graph2, path2, orig_dest_size=10, show=False, close=False, ax = axi, route_color=gc2, route_linewidth=2)
        axi.set_title((graphTitle(name1, energy1, lenR1+lenF1)+ graphTitle(name2, energy2, lenR2+lenF2)), fontsize=8)
    plt.show()

def compareEff(graph1, name1, graph2, name2, nSamples, destBounds, startCoord, penalty2):
    # finds the lowest energy drone routes with and without hitchhiking for n random
    # destinations, and plots the energy difference against geodisic delivery distance
    startLat,startLon = startCoord
    startNode = ox.nearest_nodes(graph1, startLon, startLat)
    N,S,E,W = destBounds
    randCoords = genRanCoords(N,S,E,W,nSamples)
    data = []
    for i in range(nSamples):
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        distance = haversine(startLon,startLat,graph1.nodes[dest]['lon'],graph1.nodes[dest]['lat'])
        _, energy1, _, _ = minEnergyRoute(graph1, startNode, dest)
        _, energy2, _, _ = minEnergyRoute(graph2, startNode, dest)       
        energy2 += penalty2
        data.append([distance, energy1, energy2])
    data = np.array(data)

    fig, ax = plt.subplots()
    x=data[ :,0]
    y=(data[ :,1]-data[ :,2]).clip(min=0)
    print(y)
    ax.scatter(x, y, s=2, c='black')
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    ax.set_xlim(left=0)
    ax.set_xlabel('Geodesic Distance (km)')
    ax.set_ylabel('Reduction in Energy-use (kWh)')
    ax.set_title('Energy use of {} relative to {} only ({})\n '.format(name2, name1, warehouse))
    plt.show()

def getLenData(graph1, graph2, nSamples, destBounds, startCoord, penalty2):
    # finds the lowest energy drone route of the hitchhiking and non-hitchhiking 
    # options and plots the distances ridden and flown against total geodisic distance
    startLat, startLon = startCoord
    startNode = ox.nearest_nodes(graph1, startLon, startLat)
    N,S,E,W = destBounds
    randCoords = genRanCoords(N,S,E,W,nSamples)
    data = []
    for i in range(nSamples):
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        distance = haversine(startLon,startLat,graph1.nodes[dest]['lon'],graph1.nodes[dest]['lat'])
        _, energy1, lenR1, lenF1 = minEnergyRoute(graph1, startNode, dest)
        _, energy2, lenR2, lenF2 = minEnergyRoute(graph2, startNode, dest) 
        if energy1-energy2 > penalty2:
            lenRide,lenFly = lenR2, lenF2
        else:
            lenRide, lenFly = lenR1, lenF1 
        data.append([distance,lenRide,lenFly])
    data = np.array(data)

    fig, ax = plt.subplots()
    x=data[ :,0]
    Ride=data[ :,1]
    Flight=data[ :,2]
    ax.scatter(x, Ride, s=2, c=gc1)
    ax.scatter(x, Flight, s=2, c=gc2)
    ax.grid(b=True, which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(b=True, which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    ax.set_xlim(left=0)
    ax.set_xlabel('Geodesic Distance (km)')
    ax.set_ylabel('Distance Travelled (km)')
    ax.legend()
    ax.set_title('Distance travelled bus-riding and flying relative to the geodisic distance from start to end points ({})\n'.format(warehouse))
    plt.show()

flightP = loadGraph('flight')
rideP = loadGraph('ride')

compareRoutes(flightP, "F", rideP, "F&B", nSGraphs, [N,S,E,W], start, busTolEn)
compareEff(flightP, "flight", rideP, "flight and bus-use", nSEff, [N,S,E,W], start, busTolEn)
getLenData(flightP, rideP, nSLens, [N,S,E,W], start, busTolEn)