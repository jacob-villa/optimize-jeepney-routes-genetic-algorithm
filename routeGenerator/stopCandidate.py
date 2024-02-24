import csv
import pickle
import osmnx as ox
import os

csv_filename = os.path.dirname(__file__) + '/../manila_amenities.csv'
pickle_filename = os.path.dirname(__file__) + '/../manila_amenities.pkl'

class stopCandidate():
    def __init__(self, a_type, city, name, lat, long):
        self.a_type = a_type
        self.city = city
        self.name = name
        self.lat = lat
        self.long = long
        self.enabled = False
        self.road_lat = None
        self.road_long = None
        
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False
        
    def getLat(self):
        return self.lat
    
    def getLong(self):
        return self.long
    
def read_data_from_csv():
    stops = []
    with open(csv_filename, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        # Amenity type, City, Amenity Name, longtitude , latitude, POINT (120.9680041 14.6253727)
        for row in csv_reader:
            amenity_type, city, amenity_name, long, lat, point = row
            print(amenity_type, city, amenity_name, long, lat, point)
            candidate = stopCandidate(amenity_type, city, amenity_name, float(lat), float(long))
            stops.append(candidate)
    return stops

def save_stops_to_pickle(stops):
    with open(pickle_filename, 'wb') as file:
        pickle.dump(stops, file)

def load_stops_from_pickle():
    with open(pickle_filename, 'rb') as file:
        data = pickle.load(file)
    return data

def get_stopCandidates():
    try:
        stops = load_stops_from_pickle()
    except FileNotFoundError:
        stops = read_data_from_csv()
        save_stops_to_pickle(stops)
    return stops
