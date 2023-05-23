# Functions to solve for the minimum energy delivery route between specified start and end 
# points on a graph. Takes input coordinates, graph, payload mass, and charge option, and returns
# data on the minimum energy path, including lengths of path stages, optimal battery size, energy
# consumption and charging power received.

import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
import math
import networkx as nx
import osmnx as ox
from areaDef import haversine
import routeFuncs as rF

# Fixed parameters
# all masses in g

baseMass = 1618                 # mass w/out batteries & WPT, w/ empty payload container
WPTmass = 132                   # mass of onboard WPT system

battED = 0.170                  # LiPo energy density Wh/g https://www.tytorobotics.com/blogs/articles/a-guide-to-lithium-polymer-batteries-for-drones 
safeDischarge = 0.7             # safe discharge % of battery https://learn.adafruit.com/li-ion-and-lipoly-batteries/voltages
battST = 5/60                   # battery capacity safety factor, as hover time in hr
battV = 25.2                    # battery voltage
bAStep = 0.5                    # available battery ampages (mAh)
bMStep = battV*bAStep/battED    # battery mass interval

actChargeRate = 30          # actual prototype charge rate
actChargeEff = 0.65         # actual prototype DC-DC efficiency     
thChargeRate = 100          # charge rate based on that achieved in literature
actChargeEff = 0.80         # DC-DC efficiency based on literature

#thrustM = 0.165             # parameters for linear model for motor thrust vs energy consumption
#thrustC = -71.25
thrustA = 0.00003             # updated paramters for polynomial model
thrustB = 0.0672
miscW = 10

# distance equivalent to the power consumption of a take-off/accelerate/deccelerate/land cycle
# based on data gathered in https://doi.org/10.1016/j.patter.2022.100569
penalty = 1100
cruiseSpeed = 12            # drone cruise speed m/s - used to calculate flight time             
busSpeed = 15               # km/hr, from https://www.london.gov.uk/who-we-are/what-london-assembly-does/questions-mayor/find-an-answer/average-bus-speeds 

def findPathLengths(graph, start, end):
    # Finds the lowest energy route between the start and end points by 
    # comparing the energy consumption with and without the ride option

    # finds nearest graph nodes to start and end points
    start = ox.nearest_nodes(graph, start[1], start[0])
    end = ox.nearest_nodes(graph, end[1], end[0])
    path = nx.shortest_path(graph, start, end, weight='cost')  
    pathFLen = nx.shortest_path_length(graph, start, end, weight='length')

    # iterates through ride path to find path length of the 3 parts:
    # pre-bus flight, bus-riding and post-bus flight
    lenF1, lenR, enR, lenF2 = 0,0,0,0 
    preR = True
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edgeLen = graph[u][v][0]['length']
        method = graph[u][v][0]['method']
        if method == 'fly':
            if preR == True:
                lenF1 += edgeLen
            else:
                lenF2 += edgeLen
        else:
            preR = False
            edgeLen = graph[u][v][0]['length']
            # finds ride energy metric (length = energy metric for flight edges) 
            edgeEn = graph[u][v][0]['energy']
            lenR += edgeLen
            enR += edgeEn

    # uses TOL penalty to check if flight-only is more efficient, and updates lengths if so  
    if pathFLen-(lenF1+enR+lenF2) < penalty:
        lenF1=pathFLen
        lenR = 0
        lenF2 = 0

    return lenF1, lenR, lenF2, end


def battDistOptP(graph, start, end, payloadMass, charge=False):
    # Finds the lowest energy graph route between a start and end point, 
    # and determines the minimum battery size for that route, accounting 
    # for the relationship between battery mass and energy consumption, 
    # and power received from wireless charging at the specified charge rate.

    # finds length of flight and ride sections for lowest energy route
    lenF1, lenR, lenF2, endN = findPathLengths(graph, start, end)

    # symbolic equations defining relationship between system parameters, 
    # energy consumption and masses
    battCap, battMass = sp.symbols('battCap, battMass')     # sympy symbols

    tMass = baseMass + payloadMass + battMass           # mass with payload              
    eMass = baseMass + battMass                     # mass w/out payload              
    
    if charge:
        # if WPT is used adds WPT onboard mass
        tMass += WPTmass
        eMass += WPTmass
        
    # converts the drone masses to an estimated power consumption in hover
    #fullW = 4*((tMass/4)*thrustM + thrustC)        # power used in W w/payload
    #emptyW = 4*((eMass/4)*thrustM + thrustC)       # power used in W w/out payload
    fullW = 4*(thrustA*(tMass/4)**2 + thrustB*(tMass/4))
    emptyW = 4*(thrustA*(eMass/4)**2 + thrustB*(eMass/4))

    # calculates one-way flight time per section
    oWayFlT1 = ((lenF1+penalty)/cruiseSpeed)/3600   # flight time in hr, accounting for TOL penalty
    oWayFlT2 = 0
    if lenR !=0:
        # if bus used, second stage flight time, adds second TOL penalty
        oWayFlT2 = ((lenF2+penalty)/cruiseSpeed)/3600

    # flight energy consumptions on forward and return, as functions of battery mass
    energyF1 = oWayFlT1*(fullW+miscW)
    energyF2 = oWayFlT2*(fullW+miscW)
    energyR1 = oWayFlT1*(emptyW+miscW)
    energyR2 = oWayFlT2*(emptyW+miscW)
    energyT = energyF1+energyF2+energyR1+energyR2       # total estimated consumption

    energyST = battST*(fullW+miscW)   # energy for safety hover time
    energyN = energyT+energyST         
    battCap = (energyN/safeDischarge)    # safe battery capacity as function of battery mass

    chargeFull1 = 0     # binary - does battery reach full charge on forward bus-ride 
    chargeFull2 = 0     # binary - does battery reach full charge on return bus-ride
    chAct1 = 0          # charge energy on forward bus ride
    chAct2 = 0          # charge energy on return bus ride

    if charge and lenR>0:
        # if charging available and buses used, adjusts battery capacity based on WPT
        # calculates max charge received, if battery capacity is available
        chTime = (lenR/1000)/busSpeed                         # one way time on bus in hr
        chRates = {'low': actChargeRate, 'high': thChargeRate}  # charge powers in W
        chRate = chRates[charge]                                
        oWMaxCh = chRate*chTime         # max one-way battery charge .
        # defines charge received as the minimum of the max one-way battery charge and 
        # the remaining battery consumption based on energy used in flight since last charge
        # as functions of battery mass
        ch1 = sp.Piecewise((energyF1, energyF1<oWMaxCh), (oWMaxCh, True))
        ch2 = sp.Piecewise((energyF2+energyR2, energyF2+energyR2<oWMaxCh), (oWMaxCh, True))

        # updated necessary battery capacity as function of battery mass
        battCap = ((energyN-ch1-ch2)/safeDischarge)
        # solves for minimum battery mass
        minBattMass = sp.solve(battMass - battCap/battED, battMass)[0]
        # rounds battery mass up to nearest available battery size
        actBattMass = math.ceil(minBattMass/bMStep)*bMStep
        # substitutes battery mass to calculate charge power received 
        chAct1 = ch1.subs(battMass, actBattMass)
        chAct2 = ch2.subs(battMass, actBattMass)
        # updates binary metrics to show if battery reached full capacity in charge stages
        if chAct1<oWMaxCh:
            chargeFull1 = 1
        if chAct2<oWMaxCh:
            chargeFull2 = 1      
       
    else:
        # solves for battery mass if charging not used
        battCap = (energyN/safeDischarge)
        minBattMass = sp.solve(battMass - battCap/battED, battMass)[0]
        actBattMass = math.ceil(minBattMass/bMStep)*bMStep

    # calculates battery capacity
    battCap = actBattMass*battED
    # substitutes battery mass to find total flight energy consumption
    energyT = (energyT).subs(battMass,actBattMass)
    # calculates geodisic delivery distance from coordinates
    distance = haversine(start[1],start[0],end[1],end[0])

    return np.array([[distance, battCap, actBattMass, energyT, lenF1/1000, lenR/1000, lenF2/1000, chAct1, chAct2, chargeFull1, chargeFull2, payloadMass, endN]])

