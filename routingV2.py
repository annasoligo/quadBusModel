import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import areaDef as ar
from areaDef import haversine
import numpy as np
from math import *
import areaDef as ar
import pandas as pd
import csv
import random
from sklearn.linear_model import LinearRegression
from matplotlib import rc
import os

rc('font',**{'family':'sans-serif','sans-serif':['Arial']})


from energyModels import battDistOptP
import energyModels as EM

# defines system parameters
busTolEn = 0.0264           # energy penalty for added bus landing + takeoff
bN,bE,bS,bW = ar.bBoxes[1]  # bounding box for routes
N,E,S,W = ar.bBoxes[0]      # bounding box for delivery locations
start = ar.startLL          # start location (specified warehouse)
nSGraphs = 10               # number of route comparison graphs to show
nSEff = 200                 # number of routes to compare energy consumption
nSLens = 200                # number of routes to compare flight/ride distances
warehouse = ar.warehouse    # warehouse name

# graph colours
gR = '#E22526'
gDO = '#D36027'
gO = '#E6A024'
gY = '#EFE442'
gP = '#CC79A7'
gB = '#0273B3'
gLB = '#5BB4E5'
gG = '#009E73'


def loadGraph(fName):
    # loads graph and processes energy metrics
    P = ox.load_graphml(fName + '.graphml')
    for u,v in P.edges():
        P[u][v][0]['energy'] = float(P[u][v][0]['energy'])
    return P

# loads graph for specified warehouse
flightP = loadGraph(warehouse+'flight')
rideP = loadGraph(warehouse+'ride')

def genRanCoords(maxN, maxS, maxE, maxW, nCoords):
    # generates a n pairs of random coordinate within the defined area
    # returns n*2 array
    rangeLat  = maxN-maxS
    rangeLon = maxE-maxW
    randLats = (np.random.rand(nCoords,1)*rangeLat)+maxS
    randLons = (np.random.rand(nCoords,1)*rangeLon)+maxW
    randCoords = np.column_stack((randLats, randLons))
    return randCoords

def getEnergyData(nSamples, start, destBounds, payloadMass, chRate, chRate2=False, type=False):
    N,S,E,W = destBounds

    randCoords1 = genRanCoords(N,S,E,W,nSamples)
    print(randCoords1)
    if type:
        if type=="allNodes":
            nodes = ox.graph_to_gdfs(flightP, edges=False)
            rC1 = np.column_stack((nodes['y'].to_numpy(), nodes['x'].to_numpy()))
            rC1 = rC1[np.where(np.logical_and(rC1[:,0]>S, rC1[:,0]<N))]
            randCoords1 = rC1[np.where(np.logical_and(rC1[:,1]>W, rC1[:,1]<E))]
        randCoords2, randCoords3, randCoords4 = randCoords1, randCoords1, randCoords1
    else:
        randCoords2, randCoords3, randCoords4 = genRanCoords(N,S,E,W,nSamples),genRanCoords(N,S,E,W,nSamples),genRanCoords(N,S,E,W,nSamples)
    payload = payloadMass

    WPTP1 = np.empty((0,13))
    WPTP2 = np.empty((0,13))
    nWPTP = np.empty((0,13))
    nBusP = np.empty((0,13))
    print(len(randCoords1))
    for i in range(len(randCoords1)):
        print(i)            # progress counter
        if not isinstance(payloadMass, int):
            payload =random.randint(payloadMass[0], payloadMass[1])
        end1,end2,end3,end4 = randCoords1[i],randCoords2[i],randCoords3[i],randCoords4[i]
        try:
            p1 = battDistOptP(rideP, start, end1, payload, charge=chRate)
            p3 = battDistOptP(rideP, start, end3, payload)
            p4 = battDistOptP(flightP, start, end4, payload)
            if chRate2:
                p2 = battDistOptP(rideP, start, end2, payload, charge=chRate2)
                WPTP2 = np.append(WPTP2,p2,axis=0)
            WPTP1 = np.append(WPTP1, p1, axis=0)
            nWPTP = np.append(nWPTP,p3,axis=0)
            nBusP = np.append(nBusP,p4,axis=0)
        except:
            # skips occasional isolated maps sectionsso programme can continue
            print('no path')
    return WPTP1, WPTP2, nWPTP, nBusP

def plotConsumption(p1,p2,leg1,leg2,p3=False,leg3=False, p4=False,leg4=False, fitLines = False, order = 2 ):
    fig, ax = plt.subplots()
    al = 1
    if fitLines:
        al = 0.3
    arrays = [p1,p2]
    legendNames = [leg1,leg2]
    cols = [gLB, gB, gO, gDO]
    if leg3 :
        legendNames.append(leg3)
        arrays.append(p3)
    if leg4 :
        legendNames.append(leg4)
        arrays.append(p4)

    for i in range(len(arrays)):
        p = arrays[i]
        ax.scatter(p[:,0], p[:,3], s=6, c=cols[i], alpha=al, linewidth = 0)
        if fitLines:
            x=p[:,0]
            y = p[:,3]
            x, y = np.sort(np.array([x, y]))
            coeff = np.polyfit(x,y,order)
            xn = np.linspace(0,10,100)
            yn = np.poly1d(coeff)
            plt.plot(xn,yn(xn), c=cols[i])

    ax.set_xlabel('One-way Geodisic Distance (km)')
    ax.set_ylabel('Power Consumption (Wh)')
    ax.set_title('Hitch-hiking UAV Power Consumption for Return Delivery Journey\n')
    ax.legend(legendNames)
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    plt.show()
    
def plotCharge(p1,p2):
    fig, ax = plt.subplots()
    for r in p1:
        if r[9]==0:
            col = gLB
        elif r[10]+r[9]==2:
            col = gG
        else:
            col = gB
        ax.scatter(r[0], r[5], s=3, c=col)
    for r in p2:
        if r[9]==0:
            col = gY
        elif r[10]+r[9]==2:
            col = gR
        else:
            col = gO
        ax.scatter(r[0], r[5], s=3, c=col)
    ax.set_xlabel('One-way Geodisic Distance (km)')
    ax.set_ylabel('Ride Distance (km)')
    ax.set_title('Graph showing when batteries reach full capacity while charging at 30W and 100W\n')
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    plt.show()

def plotMostEfficient(p1,leg1,p2,leg2,p3,leg3,p4,leg4):
    arrays = [p4,p3,p2,p1]      # order reversed, so defaults to flight only, then no WPT if efficiencies equal
    for i in reversed(range(p1.shape[0])):
        print(i)
        vals = [arr[i][3] for arr in arrays]
        print('vals', vals)
        mEff = vals.index(min(vals))
        print('mEff', mEff)
        for j in range(4):
            if j != mEff:
                print(arrays[j][i])
                arrays[j]=np.delete(arrays[j],i,0)
    fig, ax = plt.subplots()
 
    legendNames = [leg1,leg2,leg3,leg4]
    p4,p3,p2,p1 = arrays
    ax.scatter(p1[:,0], p1[:,11], s=3, c=gLB)
    ax.scatter(p2[:,0], p2[:,11], s=3, c=gB)
    ax.scatter(p3[:,0], p3[:,11], s=3, c=gO)
    ax.scatter(p4[:,0], p4[:,11], s=3, c=gR)
    ax.set_xlabel('One-way Geodisic Distance (km)')
    ax.set_ylabel('Payload Mass (g)')
    ax.set_title('Most Efficient UAV Method by Distance and Payload Mass\n')
    ax.legend(legendNames)
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    plt.show()

def plotEnergyConsBP(p1,p2, p3):
    arrays = [p1,p2,p3]
    for i in range(len(arrays)):
        arr = arrays[i]
        print(arr)
        for j in reversed(range(arr.shape[0])):
            if arr[j][0]<3:
                arr = np.delete(arr,j, 0)
        arrays[i] = arr
    p1,p2,p3 = arrays
    fig, ax = plt.subplots()
    ax.boxplot([p2[:,3],p1[:,3],p3[:,3]], labels =['100W WPT','30W WPT', 'No WPT'], showfliers=False)
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2, axis ='y')
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1, axis ='y')

    ax.minorticks_on()

    plt.show()

def plotEnergyConsLin(p1,p2, p3):
    arrays = [p1,p2,p3]
    dInt = np.linspace(0.25,10.25,21)
    x = np.linspace(0.5,10,20)
    for i in range(len(arrays)):
        arr = arrays[i]
        meanArr =[]
        for j in range(len(dInt)-1):
            meanArr.append(np.mean(arr[:,3][np.where(np.logical_and(arr[:,0]>dInt[j],arr[:,0]<dInt[j+1]))]))
        arrays[i] = meanArr
    p1,p2,p3 = arrays
    fig, ax = plt.subplots()
    red1 = -100*np.subtract(np.array(p3),np.array(p1))/np.array(p3)
    red2 = -100*np.subtract(np.array(p3),np.array(p2))/np.array(p3)
    ax.scatter(x, red2, s=10, c=gB)
    ax.scatter(x, red1, s=10, c=gLB)
    
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.legend(['100W WPT','30W WPT'])
    ax.set_xlabel('Geodisic Distance (km)')
    ax.set_ylabel('% Change in Energy Consumption')
    ax.minorticks_on()
    plt.show()

def plotTimes(bus, nBus):
    # calculates travel and TOL times based on parameters defined in energy models
    bTkm = 60/EM.busSpeed
    fTkm = 60/(EM.cruiseSpeed*3.6)
    TOLT = (EM.penalty/1000)*fTkm
    print(bTkm, fTkm, TOLT)
    times = fTkm*(bus[:,4]+bus[:,6])+bTkm*bus[:,5]+2*TOLT
    nBusTimes = fTkm*nBus[:,4]+TOLT
    al = 0.4

    fig, ax = plt.subplots()
    busD=bus[:,0].reshape(-1, 1)
    nBusD=nBus[:,0].reshape(-1, 1)

    reg = LinearRegression().fit(busD, times)
    ax.plot(bus[:,0], reg.predict(busD), c=gB)
    reg2 = LinearRegression().fit(nBusD, nBusTimes)
    ax.plot(nBus[:,0], reg2.predict(nBusD), c=gDO)

    ax.scatter(bus[:,0], times, s=3, facecolor=gLB, alpha=al)
    ax.scatter(nBus[:,0], nBusTimes, s=3, facecolor=gO, alpha=al)

    ax.legend(['Hitch-hiking Routes','Flight-only Routes'])
    ax.set_xlabel('Geodisic Distance (km)')
    ax.set_ylabel('Travel Time (min)')
    ax.grid(which='major', color='black', linestyle='-', alpha=0.2)
    ax.grid(which='minor', color='black', linestyle='-', alpha=0.1)
    ax.minorticks_on()
    plt.show()

def plotMEGraph(p1,p2,p3,p4, graph):
    cols = [gDO, gO, gLB, gB]
    arrays = [p4,p3,p2,p1]      # order reversed, so defaults to flight only, then no WPT if efficiencies equal
    for i in reversed(range(p1.shape[0])):
        vals = [arr[i][3] for arr in arrays]
        print(vals)
        mEff = vals.index(min(vals))
        print(mEff)
        for j in range(4):
            if j != mEff:
                arrays[j]=np.delete(arrays[j],i,0)
    for k in range(4):
        arrays[k]=arrays[k][:,12]
    nc = []
    ns = [] 
    for n in graph.nodes():
        assigned = False
        for k in range(4):
            if assigned == False:
                if n in arrays[k]:
                    nc.append(cols[k])
                    ns.append(8)
                    print(k)
                    assigned = True
        if assigned == False:
            nc.append('black')
            ns.append(0)
    
    ox.plot_graph(graph, bgcolor='white', node_color=nc, node_size=ns, node_alpha=0.8, node_zorder=2, edge_color='black', edge_linewidth=0.3)
    plt.show()
          
def saveFile(data, name):
    # convert data to 2D form and save to file
    dir = os.path.dirname(__file__) + '\\energyData\\' + warehouse + 'ED\\'
    print(dir)
    with open(dir+name+'.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def saveData(lowWPT, highWPT, nWPT, nBus, id):
    saveFile(lowWPT, 'lowWPT'+id)
    saveFile(highWPT, 'highWPT'+id)
    saveFile(nWPT, 'nWPT'+id)
    saveFile(nBus, 'nBus'+id)

def loadData(id):
    dir = os.path.dirname(__file__) + '\\energyData\\' + warehouse + 'ED\\'
    lowWPT = np.loadtxt(dir+"lowWPT"+id+'.csv', delimiter=",", dtype=float)
    highWPT = np.loadtxt(dir+"highWPT"+id+'.csv', delimiter=",", dtype=float)
    nWPT = np.loadtxt(dir+"nWPT"+id+'.csv', delimiter=",", dtype=float)
    nBus = np.loadtxt(dir+"nBus"+id+'.csv', delimiter=",", dtype=float)
    return lowWPT, highWPT, nWPT, nBus
    # loads data and reverses reshaping

lowWPT, highWPT, nWPT, nBus = getEnergyData(1, start, [N,S,E,W], 1000, 'low', 'high', 'allNodes')
saveData(lowWPT, highWPT, nWPT, nBus, 't')

#lowWPT, highWPT, nWPT, nBus = loadData('all_1000')
#plotEnergyConsLin(lowWPT, highWPT, nWPT)
#plotConsumption(lowWPT, highWPT,'30W WPT','100W WPT',nWPT,'No WPT',nBus, 'Flight Only')
plotMEGraph(highWPT, lowWPT, nWPT, nBus, flightP)

#lMeans = np.mean(lowWPT, axis=0)
#flMeans = np.mean(nBus, axis=0)
#dFlRatio = (flMeans[4])/flMeans[0]
#dRiRatio = (lMeans[4]+lMeans[5]+lMeans[6])/lMeans[0]
#print('Fl/Geo: ', dFlRatio)
#print('Ri/Geo: ', dRiRatio)

