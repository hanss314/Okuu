from enum import Enum

class Teams:
    RED, BLUE = 1, 2
    
class StateCount(int):
    def __new__(cls, value, count):
        return  super(StateCount, cls).__new__(cls, value)
    
    def __init__(self, value, count):
        self.count = count
    
class TileStates(Enum):
    RED = (1, 9)
    BLUE = (2, 8)
    ASSASSIN = (-1, 1)
    BYSTANDER = (0, 0)
    
    def __init__(self, value, count):
        self.state = value
        self.count = count
    
