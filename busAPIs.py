# Defines the account details and functions used to access TFL API data
import requests
import json

# TFL API account details
appID = 'a0bf554f7d134cd9a0467899c3a05d28'
appKey = '4692650cbf574584b1773043f1e22500'

# gets list of lines stopping at a specified stop
def fetchLines(stopID):
    response = requests.get(f"https://api.tfl.gov.uk/StopPoint/{stopID}?app_id={appID}&app_key={appKey}")

    if response.status_code != 200:
        raise RuntimeError('Failed request')
    else:
        lines = json.loads(response.text)['lines']
        return(lines)

# gets list of stops on a specified line
def fetchStops(lineID):
    stopData = []
    stations = requests.get(f"https://api.tfl.gov.uk/Line/{lineID}/Route/Sequence/inbound?app_id={appID}&app_key={appKey}")

    if stations.status_code != 200:
        raise RuntimeError('Failed request')
    else:
        data = (stations.json())
        stops = [data['orderedLineRoutes'][0]['naptanIds']]
        for s in stops[0]:
            response = requests.get(f"https://api.tfl.gov.uk/StopPoint/{s}?app_id={appID}&app_key={appKey}")
            if response.status_code != 200:
                raise RuntimeError('Failed request')
            else:
                data = response.json()
                lon = float(data['lon'])
                lat = float(data['lat'])
                stopData.append([s,lon,lat])
        return(stopData)



