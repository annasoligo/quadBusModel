# Uses the TFL API to identify the day bus routes which pass through the area defined 
# in areaDef and saves ordered lists of the stops on these lines into CSV files

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import areaDef as ar
from areaDef import EN2LL
import busAPIs as tfl

# loads map bound coordinates
bN,bE,bS,bW = ar.bBoxes[1]
# gets warehouse name
warehouse = ar.warehouse
# loads all London bus stops data
allStops = pd.read_csv('busData\\busStops.csv')

# converts stop Easting and Northing to Longitude and Latitude
lats, lons = EN2LL([allStops['Location_Easting'], allStops['Location_Northing']])
# creates array of stop Ids and Coordinates
allStopsLL= np.column_stack((allStops['Naptan_Atco'], lats, lons))

# creates array for bus stops in map bounds
areaStops =[1,1,1]
# adds stations which are within the map bounds and whose ID contain the bus stop code  
for stop in allStopsLL:
    if stop[2]>bW and stop[2]<bE:
       if stop[1]>bS and stop[1]<bN:
           naptan = str(stop[0])
           if '900' in naptan:
            areaStops = np.row_stack((areaStops, stop))
# deletes [1,1,1] placeholder
areaStops = np.delete(areaStops,0,0)

# creates array for bus lines passing through area
busLines = []

# iterates through stops in area and calls the TFL API to find corresponding 
# day bus lines. Appends new lines to the busLines array
for stop in areaStops:
    try:
        lines=tfl.fetchLines(stop[0])
    except:
        print('Failed ',stop[0])
    else:
        for line in lines:
            name = line['name']
            # checks line is a bus (contains at least 1 number) and a day route (no N)
            if any(str.isdigit(n) for n in name) and 'N' not in name:
                if name not in busLines:
                    print(name)
                    busLines.append(name)
print('Number of bus lines = ', len(busLines))


# iterates through the area bus lines and returns an ordered list of all stops on that line
# checks which bus stops are within the bounding box and removes the others
# saves stop IDs and coordinates within a directory for the warehouse

dirName =  'busData\\'+warehouse+'LineStops/'
completed = 0
for l in busLines:
    try:
        data = tfl.fetchStops(l)
    except:
        print('failed ', line)
    else:
        outInds = []
        for i in range(len(data)):
            stop=data[i]
            if stop[1]<bW or stop[1]>bE or stop[2]<bS or stop[2]>bN:
                outInds.append(i)
        for ind in sorted(outInds, reverse=True):
            data.pop(ind)
        if len(data)>3:
            fName = l + '.csv'
            fDir = dirName + fName
            pd.DataFrame(data).to_csv(fDir)
        completed+=1
        print('Lines complete = ', completed)
