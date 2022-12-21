import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import areaDef as ar
import numpy as np
from math import *
import areaDef as ar
#VERSION 2, LARGER AREA
busTolEn = 0.0264
bN,bS,bE,bW = ar.bBox
N,S,E,W = ar.N, ar.S, ar.E, ar.W
start = ar.start
nSGraphs = 10
nSEff = 200
nSLens = 200
warehouse = ar.warehouse
gc1 = 'red'
gc2 = 'darkOrange'

def loadGraph(fName):
    P = ox.load_graphml(fName + '.graphml')
    for u,v in P.edges():
        P[u][v][0]['energy'] = float(P[u][v][0]['energy'])
    return P

def genRanCoords(maxN, maxS, maxE, maxW, nCoords):
    rangeLat  = maxN-maxS
    rangeLon = maxE-maxW

    randLats = (np.random.rand(nCoords,1)*rangeLat)+maxS
    randLons = (np.random.rand(nCoords,1)*rangeLon)+maxW
    randCoords = np.column_stack((randLats, randLons))
    return randCoords

def minEnergyRoute(graph, start, end):
    path = nx.shortest_path(graph, start, end, weight='energy')
    energy = nx.shortest_path_length(graph, start, end, weight='energy')
    length = 0
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        length += graph[u][v][0]['length']
    routeData = (path, energy, length/1000)
    return routeData

def methodLens(graph, start, end):
    path = nx.shortest_path(graph, start, end, weight='energy')
    energy = nx.shortest_path_length(graph, start, end, weight='energy')
    lenRide, lenFly = 0, 0
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        if graph[u][v][0]['method'] == 'ride':
            lenRide += graph[u][v][0]['length']/1000
        else:
            lenFly += graph[u][v][0]['length']/1000
    return lenRide, lenFly

def graphTitle(method, energy, length):
    title = method + ": " + str(round(energy,3)) + "kwh\n" + str(round(length,3)) +"km\n"
    return title

#ec = ['r' if d['method']=='ride'  else 'black' for u,v,k,d in flightP.edges(keys=True, data=True)]
#ox.plot_graph(flightP, bgcolor='none', node_size=0, edge_color=ec, edge_linewidth= 0.5, show=False, close=False, ax = ax1)

def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def compareGraphs(graph1, name1, graph2, name2, nSamples, destBounds, startCoord, penalty2):
    startNode = ox.nearest_nodes(graph1, startCoord[1], startCoord[0])
    N,S,E,W = destBounds
    randCoords = genRanCoords(N,S,E,W,nSamples)
    fig, ax = plt.subplots(1,nSamples)
    for i in range(nSamples):
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        path1, energy1, len1 = minEnergyRoute(graph1, startNode, dest)
        path2, energy2, len2 = minEnergyRoute(graph2, startNode, dest)
        energy2+=2*penalty2
        energy1+=penalty2
        axi = ax[i]
        ox.plot_graph(graph1, bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.3, show=False, close=False, ax = axi)
        ox.plot_graph_route(graph1, path1, orig_dest_size=10, show=False, close=False, ax = axi, route_color=gc1, route_linewidth=2)
        ox.plot_graph_route(graph2, path2, orig_dest_size=10, show=False, close=False, ax = axi, route_color=gc2, route_linewidth=2)
        axi.set_title((graphTitle(name1, energy1, len1)+ graphTitle(name2, energy2, len2)), fontsize=8)
    plt.show()

def compareEff(graph1, name1, graph2, name2, nSamples, destBounds, startCoord, penalty2):
    startLat,startLon = startCoord
    startNode = ox.nearest_nodes(graph1, startLon, startLat)
    N,S,E,W = destBounds
    randCoords = genRanCoords(N,S,E,W,nSamples)
    data = []
    for i in range(nSamples):
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        distance = haversine(startLon,startLat,graph1.nodes[dest]['lon'],graph1.nodes[dest]['lat'])
        _, energy1, _ = minEnergyRoute(graph1, startNode, dest)
        _, energy2, _ = minEnergyRoute(graph2, startNode, dest)       
        energy2 += penalty2
        data.append([distance, energy1, energy2])
    data = np.array(data)

    fig, ax = plt.subplots()
    x=data[ :,0]
    y=(data[ :,1]-data[ :,2]).clip(min=0)
    print(y)
    ax.scatter(x, y, s=2, c='black')
    ax.grid(b=True, which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(b=True, which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    ax.set_xlim(left=0)
    ax.set_xlabel('Geodesic Distance (km)')
    ax.set_ylabel('Reduction in Energy-use (kwh)')
    ax.set_title('Energy use of {} relative to {} only ({})\n '.format(name2, name1, warehouse))
    plt.show()

def getLenData(graph1, graph2, nSamples, destBounds, startCoord, penalty2):
    startLat,startLon = startCoord
    startNode = ox.nearest_nodes(graph1, startLon, startLat)
    N,S,E,W = destBounds
    randCoords = genRanCoords(N,S,E,W,nSamples)
    data = []
    for i in range(nSamples):
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        distance = haversine(startLon,startLat,graph1.nodes[dest]['lon'],graph1.nodes[dest]['lat'])
        _, energy1, len1 = minEnergyRoute(graph1, startNode, dest)
        _, energy2, _ = minEnergyRoute(graph2, startNode, dest) 
        if energy1-energy2 > penalty2:
            lenRide, lenFly = methodLens(graph2, startNode, dest)  
        else:
            lenRide, lenFly = 0, len1  
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

compareGraphs(flightP, "F", rideP, "F&B", nSGraphs, [N,S,E,W], start, busTolEn)
compareEff(flightP, "flight", rideP, "flight and bus-use", nSEff, [N,S,E,W], start, busTolEn)
getLenData(flightP, rideP, nSLens, [N,S,E,W], start, busTolEn)