# Bus-Drone Routing
> A code repository which estimates the minimum-energy route for a London delivery drone which hitchikes on buses and compares it to the energy use of a drone-only delivery.


## Usage
To use these files, first define the area of London that will be considered in the areaDef.py file. Currently the delivery start point is set as the South London Amazon warehouse, and the furthest delivery point is the furthest point in centra London which is closer to this warehouse than any other Amazon warehouse.

Then, use the findBusStops.py file to generate ordered list of the bus stops in the defined area. This is necessary before running the generateGraphs.py file, which produces and saves the weighted flight-only and fligh+bus networks the delivery routes are generated on.

Once the networks are saved, the routing file can be run to generate and compare the lowest-energy routes with and without the use of buses. Three functions are defined to analyse the results:

**compareGraphs** plots the routes on the network map, along with their energy-use and lengths, for visual comparison and checking.

![image](https://user-images.githubusercontent.com/56299537/212654011-1e09f1bf-c033-405e-815b-c4e19a3aa55b.png)

**compareEff** plots the difference in energy consumption of deliveries to 200 random destinations, as a function of geodisic delivery distance.

![image](https://user-images.githubusercontent.com/56299537/212654072-8e92b7da-6772-4285-9cfe-8eac233da416.png)

**getLenData** plots the distances of the flight and bus-riding parts of the lowest-energy delivery route to 200 random destinations, as a function of total geodisic delivery distance. 

![image](https://user-images.githubusercontent.com/56299537/212654127-a29c118e-ce7e-4b26-bb76-4a36cb437467.png)


## Model Assumptions

This routing is simplified and relies on several assumptions. The main ones are as follows:
- Energy estimates for ToL and cruise flight are based on extrapolation of DJI Matrice and Matternet M2V9 flight data and mathematical models. It assumes flight is at a constant speed of 10m/s and accounts for acceleration and deceleration are accounted for in the take off and landing energy 'penalty' added.
- Energy to change buses is negligible (small hop to waiting point, then back to bus = short hover period with minimal height change)
- Drones must follow roads because of debate surrounding the ownership of airspace directly above housing, and the variable height of buildings.
- Additional energy required due to turning corners is negligible.
- Bus routes assumed to be the same in both directions (inbound route)
- Take off and landing on a bus is assumed possible at any point

## Code Details
A more detailed description of the function of each file is defined in the table below:

![image](https://user-images.githubusercontent.com/56299537/212643740-413206fa-cbab-4123-a48a-b3742317587d.png)




## Change History

* 21/12
    * Initial Commit, README added
* 16/01
   * Detail added to README

