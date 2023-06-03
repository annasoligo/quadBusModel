# Bus-Drone Routing
> An analyis framework for  optimal routing of  for a London delivery drone which hitchikes and wirelessly charges on buses and compares it to the energy use of a drone-only delivery.


## Context
This work explores the efficiency of a novel delivery concept, where small quadcopters minimise their flight time and thus energy consumption by riding on the roof of public-transport vehicles. Similarly to the concept of paired delivery vans and drones, this mitigates the issue of efficiency reducing as flight distance increases, because it enables significantly smaller batteries to be used. However, the use of public-transport further reduces ground congestion, and provides a (relatively) consistent service that does not require the coordination of multi-destination van routes, thus enabling rapid, high-efficiency deliveries independent of overall system demand.

The code presented here enables the comparison of the energy-consumption of hitchhiking and non hitchhiking drones when delivering packages to real London destinations using the TFL bus-network. The work was done in tandem with a hardware drone build, which demonstrates the integration of autonomous payload-delivery and wirelss-charging, and a value-sensitive design study, which explores the ethical implications of urban-delivery drones. These aspects are documented on the [project web-page](www.annasoligo.co.uk/projectpages/busQuad).


## Methods & Usage

Two frameworks are presented: 
1. V1 uses the estimated-specifications of the commercially-successfully Matternet drone platform to compare the energy consumption of flight-only and hitch-hiking routes. Energy consumption is a linear function of the distances flown and ridden. This was used or initial justification of the merits of the hitchhiking UAV concept.
2. V2 uses the specifications of a custom quadcopter build to compare these scenarios, in addition to the scenarios where the drone can recharge at 30W or 100W while on public-transport. Battery size is minimised for the necessary flight distance. This was used to produce higher accuracy estimates of the energy-consumption of different system options.

These are built on the same routing approach:

'areaDef.py' defines the destination area as the rectangle drawn from an origin point and a furthest delivery point. The current options refer to the 3 Amazon distribution centres in London, and the central-London point equidistant from the three. *Changing the warehouse referenced in the 'areaDef' file will change the warehouse used by all of the other scripts*

'findBusStops.py' uses the list of all London bus stops in 'busStops.csv' and the TFL API calls defined in 'busAPIs.py' to identify the daytime bus lines that pass through the area defined in 'areaDef.py'. The second defined API call is subsequently used to generate ordered lists of the bus stops along each relevant bus-line, and save these as csv files in the relevant warehouse folder.

'generateGraphs.py' generates a weighted graph of the road-network defined in 'areaDef.py'. Based on the bus line files generated by 'findBusStops.py', Dijkstra's algorithm is used estimate the bus routes as the shortest paths connecting consecutive bus stops and the relevant edges are assigned ride attributes. A flight-only and bus and flight version of the network are saved under the warehouse name.

'routeFuncs.py' contains functions to generate routes on these saved networks. These individually enable: loading the graphs, generating random coordinates within the graph, weighting the 'energy' and 'cost' values of graph edges according to their method attribute (flight or ride), and using Dijkstra's algorithm to find the routes on the graphs which minimise the sum of the values of a given attribute. The 'costParameterPlot' function finds the minimum-weight route with different cost ratios between the flight and ride edges. It then calculates the time and energy changes resulting from hitch-hiking in each case, and plots a set of graphs to visualise this. This enables an acceptable trade-off of energy-saving and journey-time increase to be determined, and the corresponding cost factors for V1 and V2 defined in the same file are used by the 'routing' files


This is where the versions diverge:

    1. 'routingV1.py' defines the specifications of the Matternet drone and finds the optimal routes to randomly generated destination points, based on minimising the total route cost according to edges weighted by the cost in 'routeFuncs.py'. A selection of graphs and  averages can be returned comparing the energy consumption, distances travelled and time taken for hitchhiking and flight-only drones.

    2. 'routingV2.py' defines the specifications of the custom drone build, including its energy-consumption as defined by the 'aerodynamicModel.mlx' MatLab script, and finds optimal routes in the same way. However, the final energy consumption is subsequently determined based on the 'energyModels.py' file, for the hitchhiking and flight only scenarios, in addition to scenarios where the drone can recharge at 30W and 100W. 

    This energy model defines the relationship between battery-capacity and mass, total UAV mass and power consumption. It additionally accounts for a maximum battery-charge for battery health, and a safety margin on flight time, and consequently solves for the optimum battery-size and minimum energy-consumption using the Python symbolic-maths library. In the charging case, this is extended by calculating the charge received based on the time spent hitch-hiking, and limiting this to ensure  the model does not allow battery capacity to 100%. This results in a smaller battery-requirement and thus a lower overall battery mass, but this is a trade-off with the additional mass added to account for the onboard WPT system.

    The 'routingV2.py' contains functions to save and load the route data it generates (making it practical to work with significantly more data points) and can plot graphs to show raw energy-consumption, the impact of WPT on energy consumption, journey times, and the geographic distribution of the most efficient method to reach nodes

The results are shown and discussed in the accompanying master's thesis.


## Limitations & Suggested Extensions

This is by far not a comprehensive list, but includes a few of the most significant inaccuracies of current analysis, and consequent improvements to be implemented.

*Live-routing*
- Routes are generated statically over previously saved maps, so assume a bus is always available with rooftop capacity, and always travels at the same constant seed. Real-time use of the TFL API could be implemented instead, with a further extension to a two-part assignment problem: What packages are assigned to drones as opposed to ground delivery vehicle, and which of these drones are most beneficially assigned to buses?

*Real Data*
-  The UAV metrics are derived based on theoretical models of power consumption. Experimental data would be significantly more accurate, especially in determining the energy penalty assigned for the package delivery and bus-landing stages. Similarly, a broader analysis could enable the time cost-factor to be realistically determined based on its implications with regards to fleet-size, package size and overall bus-capacity.

*Network Accuracy*
- The processing of the OSMNX networks and TFL data is imperfect: destinations and bus stops are moved to their nearest map nodes (up to 170m) to avoid adding nodes and increasing routing time, buses are assumed to drive the shortest distance between consecutive stops along the same route in both directions, and public spaces such as parks and the river are not included as traversable areas. The accuracy here could be improved, but likely at the cost of introducing manual post-processing, or using a paid transport API.


## Change History

* 21/12
    * Initial Commit, README added
* 16/01
    * Detail added to README
* 22/05
    * Added V2 analysis and energy modelling
    * Restructure for ease of changing warehouses and data access
    * Updated README for new analysis
* 02/06
    * MatLab Aerodynamic model  added
* 03/06
    * README re-written and extended to place code in the context of broader work
