import requests
import time
from Structures.Venue import Venue
from Keys.keys import *
from pprint import pprint
import math
import sys

#Get List of nearby supermarkets from BestTime.app API
url = "https://besttime.app/api/v1/venues/search"
apikey = getBestTimeKey()
googlekey = getGoogleKey()
src_address = input("Enter Address\n")
num_places = 50
q = 'supermarkets near '+ src_address
params = {
    'api_key_private': apikey,
    'q': q,
    'num': 20,
    'fast': False,
    'opened': 'now'
}
r = requests.request("POST", url , params=params).json()
job_id = r['job_id']
collection_id = r['collection_id']
url = "https://besttime.app/api/v1/venues/progress"

params = {
    'job_id': job_id,
    'collection_id': collection_id
}
response = requests.request("GET", url, params=params).json()
job_finished = response['job_finished']
time_waited = 0
while(response['job_finished'] == False):
    time.sleep(1)
    time_waited += 1
    if(time_waited >= 40):
        print("Timeout, response is taking too long")
        sys.exit()
    response = requests.request("GET", url, params=params).json()
    job_finished = response['job_finished']
print("Surrounding supermarkets found, calculating best option")
num_venues = int(response['count_completed'])
venues = [None] * num_venues

best_venue = Venue()
best_decision_value = math.inf
for x in range(num_venues):
    #Initialize Key Venue using BestTime API
    venue_address = response['venues'][x]['venue_address']
    venue_lat = response['venues'][x]['venue_lat']
    venue_lon = response['venues'][x]['venue_lon']
    venue_name = response['venues'][x]['venue_name']
    venue_id = response['venues'][x]['venue_id']
    venue = Venue()
    venue.address = venue_address
    venue.id = venue_id
    venue.lat = venue_lat
    venue.lon = venue_lon
    venue.name = venue_name

    #Get Live forecast data for venue using BestTime API
    url = "https://besttime.app/api/v1/forecasts/live"
    params = {
        'api_key_private': apikey,
        'venue_id': venue.id
        }
    r = requests.request("POST", url, params=params).json()
    live_busyness = -1
    forecasted_busyness = -1
    forecasted_busyness_available = r['analysis']["venue_forecasted_busyness_available"]
    if forecasted_busyness_available == True:
        forecasted_busyness = r['analysis']["venue_forecasted_busyness"]
    live_busyness_available = r['analysis']["venue_live_busyness_available"]
    if live_busyness_available == True:
        live_busyness = r['analysis']["venue_live_busyness"]
    min_time = r['venue_info']["venue_dwell_time_min"]
    max_time = r['venue_info']["venue_dwell_time_max"]
    avg_time = r['venue_info']["venue_dwell_time_avg"]
    venue.min_time_spent = min_time * 60
    venue.max_time_spent = max_time * 60
    venue.avg_time_spent = avg_time * 60
    venue.forecasted_busy_factor = forecasted_busyness/100
    venue.live_busy_factor = live_busyness/100
    venue.forecast_avail = forecasted_busyness_available
    venue.live_avail = live_busyness_available

    #Get time to travel to venue using Google Matrix API
    origin = src_address
    key = googlekey
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&'
    google_response = requests.get(url + "origins=" + src_address + "&destinations=" + venue.address + "&key=" + key).json()
    time_in_secs = google_response['rows'][0]['elements'][0]['duration']['value']
    venue.time_in_secs = time_in_secs


    venue_busyness = 0
    if venue.forecast_avail == False and venue.live_avail == False:
        continue
    if venue.live_avail == True:
        venue_busyness = venue.live_busy_factor
    else:
        venue_busyness = venue.forecasted_busy_factor
    decision_value = (venue_busyness * venue.max_time_spent) + venue.time_in_secs
    if decision_value < best_decision_value:
        best_decision_value = decision_value
        best_venue = venue

print("The best supermarket to go to is ", best_venue.name, "located at ", best_venue.address)
print(num_venues," Supermarkets considered.")


