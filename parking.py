# Latitude/Longitude distance calculation - https://stackoverflow.com/questions/41336756/find-the-closest-latitude-and-longitude
from math import cos, asin, sqrt
import json, time, requests
import schedule

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))

def only_available(input):
	for spot in input:
		if spot.available: yield spot

def closest(data, v):
    return min(only_available(data), key=lambda p: distance(v['lat'],v['lon'],float(p.latitude),float(p.longitude)))

def is_available(available):
	if available == 'Unoccupied':
		return True
	else:
		return False

class ParkingSpot:
	id = 0
	latitude = ''
	longitude = ''
	available = False
	restrictions = ''

	def __init__(self, id, latitude, longitude, available):
		self.id = id
		self.latitude = latitude
		self.longitude = longitude
		self.available = is_available(available)

class ParkingRestriction:
	bay_id = 0
	description = ''
	disability_ext = ''
	duration = ''
	end_time = ''
	from_day = ''
	start_time = ''
	to_day = ''
	type_desc = ''

	def __init__(self, bay_id, description, start_time, end_time, duration, from_day, to_day, type_desc, disability_ext):
		self.bay_id = bay_id
		self.description = description
		self.start_time = start_time
		self.end_time = end_time
		self.duration = duration
		self.from_day = day_conversion(from_day)
		self.to_day = day_conversion(to_day)
		self.type_desc = type_desc
		self.disability_ext = disability_ext


def day_conversion(day_number):
	#  Returns a string with the day of the week
	days_of_the_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
	return days_of_the_week[int(day_number)]

def minutes_to_hours(minutes):
	hours = int(int(minutes)/60)
	minutes = int(minutes) % 60
	if minutes > 0:
		return str(hours) + ' hours & ' + str(minutes) + ' minutes.' 
	else:
		return str(hours) + ' hours.'

parking_spots = []

def update_db():
	parking_spots = []
	response = requests.get('https://data.melbourne.vic.gov.au/resource/dtpv-d4pf.json?$limit=5000')
	spot_data = json.loads(response.text)
	
	for item in spot_data:
		spot = ParkingSpot(item['bay_id'], item['lat'], item['lon'], item['status'])
		parking_spots.append(spot)

	with open('parking_restrictions.json') as restrictions_file:
		restriction_data = json.load(restrictions_file)

	parking_restrictions = []
	for restriction_item in restriction_data:
		bay_id = restriction_item['bayid']
		spots = filter(lambda ps: ps.id == bay_id, parking_spots)
		if spots:
			
			spot = spots[0]
			restriction_string = ''
	
			for x in xrange(1,6):
				if 'description' + str(x) in restriction_item:
					restriction = ParkingRestriction(restriction_item['bayid'], restriction_item['description' + str(x)], restriction_item['starttime' + str(x)], restriction_item['endtime' + str(x)], restriction_item['duration' + str(x)], restriction_item['fromday' + str(x)], restriction_item['today' + str(x)], restriction_item['typedesc' + str(x)], restriction_item['disabilityext' + str(x)])
					parking_restrictions.append(restriction)
					pass
				else:
					break
			spots[0].restrictions = restriction_string
	# Example location within the CBD
	v = {'lat': -37.810127, 'lon': 144.956712}
	closest_spot = closest(parking_spots, v)
	print("Closest spot is one with id " + str(closest_spot.id))
	restrictions = filter(lambda pr: pr.bay_id == closest_spot.id, parking_restrictions)
	for rest in restrictions:
		print('Parking Restriction - ' + rest.description + '. Start Time: ' + rest.start_time + ' ' + rest.from_day +  ' End Time: ' + rest.end_time + ' ' + rest.to_day + ' Duration: ' + minutes_to_hours(rest.duration))

schedule.every(2).minutes.do(update_db)

while True:
	schedule.run_pending()
	time.sleep(1)


