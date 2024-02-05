class stop_candidate(point):
    def __init__(self, point):
        self.point = point
        self.enabled = False
        
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False