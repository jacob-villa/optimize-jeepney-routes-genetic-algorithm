class stopCandidate():
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
        self.enabled = False
        
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False
        
    def getLat(self):
        return self.lat
    
    def getLong(self):
        return self.long