import csv
import pickle
import osmnx as ox
import os

csv_filename = os.path.dirname(__file__) + '/../manila_amenities.csv'
pickle_filename = os.path.dirname(__file__) + '/../manila_amenities.pkl'

class stopCandidate():
    def __init__(self, lat, long, isTranspo):
        self.lat = lat
        self.long = long
        self.enabled = False
        self.degree = 0
        self.isTranspo = isTranspo 
        
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False
        
    def getLat(self):
        return self.lat
    
    def getLong(self):
        return self.long
    
    def getDegree(self):
        return self.degree
    
    def getisTranspo(self):
        return self.isTranspo

