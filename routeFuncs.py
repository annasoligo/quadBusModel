# Defines functions to plot the impact of the time cost factor on the
# optimum routes and their relative time and energy consumptions.
# Defines the selected costs for access by routing files.
# Defines functions to load graphs with cost factor applied (for V2) and
# to generate routes on an unweighted graph, accounting for a cost factor (for V1)
 

import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import areaDef as ar
from areaDef import haversine
import numpy as np
from math import *
import areaDef as ar
from matplotlib import rc

# System parameters
disPen = 1.1 
sBus = 15                   # bus speed in km/hr
bN,bE,bS,bW = ar.bBoxes[1]  # bounding box for routes
N,E,S,W = ar.bBoxes[0]      # bounding box for delivery locations
start = ar.startLL          # start location (specified warehouse)
warehouse = ar.warehouse    # warehouse name

''' # To plot relationshops for V1
busWhkm = 0.72              # bus ride Wh/km
flWhkm = 24                 # flight Wh/km
sBus = 15
sFly = 36
'''
''' # To plot relationships for V2
busWhkm = 0.02              # bus ride relative energy
flWhkm = 1                  # flight relative energy
sBus = 15
sFly = 43.2
'''

# FILE OUTCOME:
# Defines cost factors dtermined based on the plots generated by costParameterPlot
# Factors called by routingV1 and V2 files
costV1 = 12
costV2 = 25

#graph colours
gDO = '#D36027'
gO = '#E6A024'
gB = '#0273B3'
gLB = '#5BB4E5'
# changes font for all plots
rc('font',**{'family':'sans-serif','sans-serif':['Arial']})  

def loadGraph(fName, busWhkm, flWhkm):
    # loads graph from file for analysis of impact of cost
    P = ox.load_graphml('graphs/'+warehouse+fName+'.graphml')
    # changes energy attribute value to V1 version
    for u,v in P.edges():
        if P[u][v][0]['method'] == 'ride':
            P[u][v][0]['energy'] = float(busWhkm/1000 * P[u][v][0]['length'])
            P[u][v][0]['cost'] = float(busWhkm/1000 * P[u][v][0]['length'])
        else:
            P[u][v][0]['energy'] = float(flWhkm/1000 * P[u][v][0]['length'])
            P[u][v][0]['cost'] = float(flWhkm/1000 * P[u][v][0]['length'])
    return P

def loadCostedGraph(fName, busWhkm, flWhkm, cost):
    # loads graph from file, for a specified fixed cost
    P = ox.load_graphml('graphs/'+warehouse+fName+'.graphml')
    # changes energy attribute value to V1 version
    for u,v in P.edges():
        if P[u][v][0]['method'] == 'ride':
            P[u][v][0]['energy'] = float(busWhkm/1000 * P[u][v][0]['length'])
            P[u][v][0]['cost'] = float(busWhkm/1000 * P[u][v][0]['length']*cost)
        else:
            P[u][v][0]['energy'] = float(flWhkm/1000 * P[u][v][0]['length'])
            P[u][v][0]['cost'] = float(flWhkm/1000 * P[u][v][0]['length'])
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

def minEnergyRoute(graph, end, sBus, sFly):
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
    pnPen = 1
    if lenRide != 0:
        pnPen+=1
    time = 60*lenRide/sBus + 60*(lenFly+disPen)/sFly        # estimates- journey time in min
    routeData = (path, energy, lenRide, lenFly, time)
    return routeData

def weightedMER(graph, end, cost, busWhkm, flWhkm, sBus, sFly):
    # adapted version of the minEnergyRoute function which finds the shortest
    # path incorporating a cost for bus use
    startN = ox.nearest_nodes(graph, start[1], start[0])
    P = graph
    for u,v in P.edges():
        if P[u][v][0]['method'] == 'ride':
            P[u][v][0]['cost'] = float(cost*busWhkm/1000 * P[u][v][0]['length'])
    costGraph = P
    path = nx.shortest_path(costGraph, startN, end, weight='cost')
    lenRide, lenFly, energy = 0, 0, 0
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        #print(energy)
        if graph[u][v][0]['method'] == 'ride':
            lenRide += graph[u][v][0]['length']/1000
            energy += graph[u][v][0]['energy']
        else:
            lenFly += graph[u][v][0]['length']/1000
            energy += graph[u][v][0]['energy']
    pnPen = 1
    if lenRide != 0:
        pnPen+=1
    time = 60*lenRide/sBus + 60*(lenFly+(pnPen*disPen))/sFly       # estimates- journey time in min
    energy += pnPen*disPen*flWhkm
    routeData = (path, energy, lenRide, lenFly, time)
    return routeData

def costParameterPlot(graph1,graph2, costs, nSamples, busWhkm, flWhkm, sBus, sFly):
    # Plots two graphs showing the relationship between the average increase  in 
    # journey time and decrease in energy consumption for different cost factors.
    # Graphs used to subjectively determine appropriate trade-off and cost factor
    cData = []
    rData = []
    eData = []
    tData = []
    
    startLat,startLon = start
    startN = ox.nearest_nodes(graph1, startLon, startLat)
    randCoords = genRanCoords(N,S,E,W,nSamples)
    for i in range(nSamples):
        print(i)
        lat, lon = randCoords[i]
        dest = ox.nearest_nodes(graph1, lon, lat)
        for cost in costs:
            _, energy1, _, _, time1 = weightedMER(graph1, dest, cost, busWhkm, flWhkm, sBus, sFly)
            # print('fly: ',energy1, time1)
            _, energy2, _, _, time2 = weightedMER(graph2, dest, cost, busWhkm, flWhkm, sBus, sFly)
            # print('ride: ', energy2, time2)
            tInc = (time2-time1)/time1  #increase in time, to be minimised
            eDec = (energy1-energy2)/energy1      #decrease in energy, to be maximised
            rData.append(-tInc+eDec)
            eData.append(eDec)
            tData.append(tInc)
            cData.append(cost)

    mRatios = []
    mTInc = []
    mEDec = []
    cData = np.array(cData)
    rData =np.array(rData)
    for cost in costs:
        inds = np.where(cData==cost)
        mR = np.mean(np.array(rData)[inds])
        mRatios.append(mR)
        mT = np.mean(np.array(tData)[inds])
        mTInc.append(mT)
        mE = np.mean(np.array(eData)[inds])
        mEDec.append(mE)
    print([costs, mTInc, mEDec])

    _, [ax1,ax2] = plt.subplots(1,2)

    ax2.scatter(costs, mTInc, s = 4,alpha = 1, c=gLB)
    ax2.scatter(costs, mEDec, s = 4,alpha = 1, c=gO)
    ax2.legend(['Time Increase','Energy Decrease'])
    ax2.set_ylabel('Fractional Change')
    ax2.set_xlabel('Time Cost Factor')
    ax2.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax2.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax2.minorticks_on()
    ax1.scatter(mTInc, mEDec, s = 4,alpha = 1, c=gO)
    ax1.set_xlabel('Fractional Increase in Time')
    ax1.set_ylabel('Fractional Decrease in Energy Consumption')
    ax1.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax1.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax1.minorticks_on()
    plt.show()

#flightP = loadGraph('flight', busWhkm, flWhkm)
#rideP = loadGraph('ride', busWhkm, flWhkm)
#costParameterPlot(flightP,rideP, np.linspace(1,30,91), 20, busWhkm, flWhkm, sBus, sFly)
