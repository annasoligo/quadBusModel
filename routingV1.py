import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import areaDef as ar
from areaDef import haversine
import numpy as np
from math import *
import areaDef as ar
from matplotlib import rc
from sklearn.linear_model import LinearRegression


import routeFuncs as rF


# defines system parameters
busWhkm = 0.72              # bus ride Wh/km
flWhkm = 24                 # flight Wh/km
disPen = 1.1                # TOL penalty as an equivalent distance flown
busTolEn = disPen*flWhkm    # energy penalty for added bus landing + takeoff
bN,bE,bS,bW = ar.bBoxes[1]  # bounding box for routes
N,E,S,W = ar.bBoxes[0]      # bounding box for delivery locations
start = ar.startLL          # start location (specified warehouse)
nSGraphs = 10               # number of route comparison graphs to show
nSEff = 300                 # number of routes to compare energy consumption
nSLens = 300                # number of routes to compare flight/ride distances
warehouse = ar.warehouse    # warehouse name
sBus = 15                   # bus speed in km/hr       
sFly = 36                   # drone speed in km/hr

cost = 1 
#graph colours
gR = '#E22526'
gDO = '#D36027'
gO = '#E6A024'
gY = '#EFE442'
gP = '#CC79A7'
gB = '#0273B3'
gLB = '#5BB4E5'
gG = '#009E73'
gColors = {'UUK2':[gR,gO], 'DHA1':[gB,gLB], 'DXE1':[gG,gY]}
gc1 = gColors[warehouse][0]            # graph colour dark
gc2 = gColors[warehouse][1]            # graph colour light
# changes font for all plots
rc('font',**{'family':'sans-serif','sans-serif':['Arial']})  


def graphTitle(method, energy, length):
    title = method + ": " + str(round(energy,1)) + "Wh\n" + str(round(length,2)) +"km\n"
    return title

def compareRoutes(graph1, name1, graph2, name2, nSamples, destBounds):
    # plots maps of the lowest energy drone routes with and without hitchhiking 
    # for n random destination coordinatess
    N,S,E,W = destBounds
    randCoords = rF.genRanCoords(N,S,E,W,nSamples)
    fig, ax = plt.subplots(1,nSamples)
    for i in range(nSamples):
        print(i)
        try:
            lat, lon = randCoords[i]
            dest = ox.nearest_nodes(graph1, lon, lat)
            path1, energy1, lenR1, lenF1, _ = rF.weightedMER(graph1, dest, cost, busWhkm, flWhkm, sBus, sFly)
            path2, energy2, lenR2, lenF2, _ = rF.weightedMER(graph2, dest, cost, busWhkm, flWhkm, sBus, sFly)
            axi = ax[i]
            ox.plot_graph(graph1, bgcolor='none', node_size=0, edge_color='black', edge_linewidth= 0.2, show=False, close=False, ax = axi)
            ox.plot_graph_route(graph1, path1, orig_dest_size=10, show=False, close=False, ax = axi, route_color=gc1, route_linewidth=2)
            ox.plot_graph_route(graph2, path2, orig_dest_size=10, show=False, close=False, ax = axi, route_color=gc2, route_linewidth=2)
            axi.set_title((graphTitle(name1, energy1, lenR1+lenF1)+ graphTitle(name2, energy2, lenR2+lenF2)), fontsize=8)
        except:
            print('No route found')
    plt.show()

def compareEff(graph1, name1, graph2, name2, nSamples, destBounds):
    # finds the lowest energy drone routes with and without hitchhiking for n random
    # destinations, and plots the energy difference against geodisic delivery distance
    startLat,startLon = start
    N,S,E,W = destBounds
    randCoords = rF.genRanCoords(N,S,E,W,nSamples)
    data = []
    for i in range(nSamples):
        print(i)
        try:
            lat, lon = randCoords[i]
            dest = ox.nearest_nodes(graph1, lon, lat)
            distance = haversine(startLon,startLat,graph1.nodes[dest]['lon'],graph1.nodes[dest]['lat'])
            _, energy1, _, _, _ = rF.weightedMER(graph1, dest, cost, busWhkm, flWhkm, sBus, sFly)
            _, energy2, _, _, _ = rF.weightedMER(graph2, dest, cost, busWhkm, flWhkm, sBus, sFly)       
            data.append([distance, energy1, energy2])
        except:
            print('No route found')
    data = np.array(data)

    fig, ax = plt.subplots()
    x=data[ :,0]
    en1 = data[ :,1]
    en2 = data[ :,2]
    red=(en1-en2).clip(min=0.01)
    ax.scatter(x, red, s=3, c='black', alpha = 0.3)
    x = x.reshape(-1, 1)
    reg = LinearRegression().fit(x,red)
    x2 = np.linspace(1.5,10.25,25).reshape(-1, 1)
    ax.plot(x2, reg.predict(x2), c='black', alpha = 0.8, linewidth = 1.5)
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    ax.set_xlim(left=0)
    ax.set_xlabel('Geodesic Distance (km)')
    ax.set_ylabel('Reduction in Energy-use (Wh)')
    ax.set_title('Energy use of {} relative to {} only ({})\n '.format(name2, name1, warehouse))
    plt.show()

    fig, ax = plt.subplots()
    ax.scatter(x, en1, s=3, c=gc1, alpha = 0.3)
    ax.scatter(x, en2, s=3, c=gc2, alpha = 0.3)
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    ax.set_xlabel('Geodesic Distance (km)')
    ax.set_ylabel('One-way Energy Consumption (Wh)')
    meanFl = np.mean(en1)
    meanRi = np.mean(en2)
    meanV = 260/2
    ax.hlines(meanFl, 0, 10.25, linewidth= 1.5, color = gc1)
    ax.hlines(meanRi, 0, 10.25, linewidth= 1.5, color = gc2)
    ax.hlines(meanV, 0, 10.25, linewidth= 1.5, color = 'black')
    print('Mean flight: ', meanFl)
    print('Mean HH: ', meanRi)
    ax.legend(['Flight-only routes', 'Hitch-hiking routes', 'Flight-only mean', 'Hitch-hiking mean', 'Electric-van mean'])
    plt.show()

def getLenData(graph1, graph2, nSamples, destBounds):
    # finds the lowest energy drone route of the hitchhiking and non-hitchhiking 
    # options and plots the distances ridden and flown against total geodisic distance
    startLat, startLon = start
    N,S,E,W = destBounds
    randCoords = rF.genRanCoords(N,S,E,W,nSamples)
    data = []
    busLen = 0
    nBusLen = 0
    sDist = 0
    busFlDist = 0
    busRCount = 0
    above2km = 0
    for i in range(nSamples):
        print(i)
        try:
            lat, lon = randCoords[i]
            dest = ox.nearest_nodes(graph1, lon, lat)
            distance = haversine(startLon,startLat,graph1.nodes[dest]['lon'],graph1.nodes[dest]['lat'])
            _, energy1, lenR1, lenF1, _ = rF.weightedMER(graph1, dest, cost, busWhkm, flWhkm, sBus, sFly)
            _, energy2, lenR2, lenF2, _ = rF.weightedMER(graph2, dest, cost, busWhkm, flWhkm, sBus, sFly)
    
            busLen+=lenR2+lenF2
            nBusLen+=lenR1+lenF1
            sDist+=distance
            if energy1>energy2:
                lenRide,lenFly = lenR2, lenF2
                busRCount+=1
                busFlDist +=lenF2
                if lenFly>2:
                    above2km+=1
            else:
                lenRide, lenFly = lenR1, lenF1 
            data.append([distance,lenRide,lenFly])
        except:
            print('No route found')
    print('Mean travel/geodisic distances: ', busLen/sDist, nBusLen/sDist)
    print('Mean flight distance for HH routes: ',busFlDist/busRCount)
    print('Percent over 2km: ', above2km/nSamples )
    print('Percent improved w/ HH: ', busRCount/nSamples)
    data = np.array(data)

    fig, ax = plt.subplots()
    x=data[ :,0]
    Ride=data[ :,1]
    Flight=data[ :,2]
    ax.scatter(x, Ride, s=2, c=gc1, alpha = 0.8)
    ax.scatter(x, Flight, s=2, c=gc2, alpha = 0.8)
    ax.grid(b=True, which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(b=True, which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    ax.set_xlabel('Geodesic Distance (km)')
    ax.set_ylabel('Distance Travelled (km)')
    ax.legend(['Bus-ride', 'Flight'])
    plt.show()

flightP = rF.loadGraph('flight', busWhkm, flWhkm)
rideP = rF.loadGraph('ride', busWhkm, flWhkm)

#compareRoutes(flightP, "F", rideP, "F&B", 6, [N,S,E,W])
#compareEff(flightP, "flight", rideP, "flight and bus-use", nSEff, [N,S,E,W])
getLenData(flightP, rideP, nSLens, [N,S,E,W])
