# Agent.py
# Tianxiang Xu
# This code works only for the testworld that comes with the simulator.

import sys
import Action
import Orientation
import Search
import Percept

class MySearchEngine(Search.SearchEngine):
    def HeuristicFunction(self, state, goalState):
        self.xLocation = abs(goalState.location[0] - state.location[0])
        self.yLocation = abs(goalState.location[1] - state.location[1])
        return self.xLocation + self.yLocation
    
class Agent:
    def __init__(self):
        # Initialize new agent based on new, unkonwn world
        self.agentLocation = [1,1]
        self.agentOrientation = Orientation.RIGHT
        self.agentHasGold = False
        self.agentHasArrow = True
        self.previousAction = Action.CLIMB # dummy action
        #  Environment Initialization
        self.goldLocation = [0,0] # unknown
        self.wumpusLocation = [0,0] # unknown
        self.wumpusAlive =  True
        self.stenchLocations = []
        self.breezeLocations = []
        self.actionList = []
        self.searchEngine = MySearchEngine()
        self.worldSize = 3 # HW5: worldsize between 3x3 to 9x9
        self.worldSizeKnown = False
        #  Initialize locations
        self.visitedLocations = []
        #self.unvisitedLocation = []
        self.safeLocations = [] # not unknown to be unsafe
        self.unsafeLocations = []
        
    def __del__(self):
        pass
    
    def Initialize(self):
        # Works only for test world.
        # You won't initially know safe locations or world size.
        self.agentLocation = [1,1]
        self.agentOrientation = Orientation.RIGHT
        self.agentHasGold = False
        self.agentHasArrow = True
        self.previousAction = Action.CLIMB
        self.actionList = []
        self.wumpusAlive = True
        if self.wumpusLocation in self.safeLocations:
            self.safeLocations.remove(self.wumpusLocation)
        self.searchEngine.RemoveSafeLocation(self.wumpusLocation[0],self.wumpusLocation[1])
        
    # Input percept is a dictionary [perceptName: boolean]
    def Process(self,percept):
        actionLists2 = []
        self.UpdateState(self.previousAction,percept)
        if (self.actionList == []):
            if (percept.glitter):
                # HW5.4 If perceive a glitter, then GRAB
                print("Find gold. Grabbing it")
                self.actionList.append(Action.GRAB)
            if ((self.agentHasGold) and (self.agentLocation == [1,1])):
             # HW5.5: If agent has gold and is in (1,1), then CLIMB
             print("Have gold and in (1,1). Climbing")
             self.actionList.append(Action.CLIMB)
            if ((self.goldLocation != [0,0]) and (not self.agentHasGold)):
                # HW5.6: If agent doesn't have gold, but knows its location, then navigate to that location
                print("Moving to known gold location (" + str(self.goldLocation[0]) + "," + str(self.goldLocation[1]) + ").")
                actionLists2 = Search.SearchEngine.FindPath(self.agentLocation, self.agentOrientation,
                                                            self.goldLocation, self.agentOrientation)
                self.actionList.extend(actionLists2)
            if ((self.agentHasGold) and (self.agentLocation != [1,1])):
             # HW5.7: If agent has gold, but isn't in (1,1), then navigate to (1,1)
             print("Have gold. Moving to (1,1).")
             actionLists2 = self.searchEngine.FindPath(self.agentLocation, self.agentOrientation,
                                                       [1,1],self.agentOrientation)
             self.actionList.extend(actionLists2)
            safeUnvisitedLocation = self.SafeUnvisitedLocation()
            if safeUnvisitedLocation:
                print("Moving to safe unvisited location " + str(safeUnvisitedLocation))
                actionLists2 = self.searchEngine.FindPath(self.agentLocation, self.agentOrientation,
                                                          safeUnvisitedLocation, self.agentOrientation)
                if actionLists2:
                    self.actionList.extend(actionLists2)
            if self.WumpusCanbeShot():
                wumpusShootLocation, wumpusShootOrientation = self.wumpusShootLocation()
                # Move to wumpus kill location and SHOOT
                print("Moving to shoot wumpus " + str(wumpusShootLocation))
                actionLists2 = self.searchEngine.FindPath(self.agentLocation, self.agentOrientation,
                                                          wumpusShootLocation, wumpusShootOrientation)
                if actionLists2:
                    self.actionList.extend(actionLists2)
                    self.actionList.append(Action.SHOOT)
                else:
                    print("ERROR: no path to wumpus shot location")    # for  debugging
                    sys.exit(1)
            # Move to location not known to be unsafe, but not next to a stench
            notUnsafeUnvisitedLocation = self.notUnsafeUnvisitedLocation()
            if notUnsafeUnvisitedLocation:
                print("Moving to unvisited location not known to be unsafe " + str(notUnsafeUnvisitedLocation))
                actionList2 = self.searchEngine.FindPath(self.agentLocation, self.agentOrientation,
                                                         notUnsafeUnvisitedLocation, self.agentOrientation)
                if actionList2:
                    self.actionList.extend(actionList2)
        if (self.actionList == []):
            print("ERROR: action list empty") # for debugging
            sys.exit(1)
        action = self.actionList.pop(0)
        self.previousAction = action
        return action

    def GameOver(self, score):
        if score < -1000:
            # Agent died by going forward into pit or Wumpus
            percept = Percept.Percept() # dummy, values don't matter
            self.UpdateState(Action.GOFORWARD, percept, game_over = True)
            location = self.agentLocation
            if location not in self.unsafeLocations:
                self.unsafeLocations.append(location)
            self.searchEngine.RemoveSafeLocation(location[0], location[1])
            print("Find unsafe location " + str(location))
        return

    def locateWumpus(self):
        # Check stench and safe location info to see if wumpus can be located.
        # If located, then other locations adjacent to stenches are safe.
        for stench_location_1 in self.stenchLocations:
            x1 = stench_location_1[0]
            y1 = stench_location_1[1]
            for stench_location_2 in self.stenchLocations:
                x2 = stench_location_2[0]
                y2 = stench_location_2[1]
                if (x1 == x2-1) and (y1 == y2 - 1) and ([x1+1,y1] in self.safeLocations):
                    self.wumpusLocation = [x1,y1+1]
                if (x1 == x2-1) and (y1 == y2 - 1) and ([x1,y1+1] in self.safeLocations):
                    self.wumpusLocation = [x1+1,y1]
                if (x1 == x2+1) and (y1 == y2 - 1) and ([x1-1,y1] in self.safeLocations):
                    self.wumpusLocation = [x1,y1+1]
                if (x1 == x2+1) and (y1 == y2 - 1) and ([x1,y1+1] in self.safeLocations):
                    self.wumpusLocation = [x1-1,y1]
        if (self.wumpusLocation != [0,0]):
            print("Found wumpus at " + str(self.wumpusLocation))

    def UpdateState(self,previousAction,percept,game_over=False):
        X = self.agentLocation[0]
        Y = self.agentLocation[1]
        orientation = self.agentOrientation
        if (previousAction == Action.TURNLEFT):
            self.agentOrientation = (orientation + 1) % 4
        if (previousAction == Action.TURNRIGHT):
            if (orientation == Orientation.RIGHT):
                self.agentOrientation = Orientation.DOWN
            else:
                self.agentOrientation = orientation - 1
        if (previousAction == Action.GOFORWARD):
            if percept.bump:
                if (orientation == Orientation.RIGHT) or (orientation == Orientation.UP):
                    print("World size known to be " + str(self.worldSize) + "x" + str(self.worldSize))
                    self.worldSizeKnown = True
                    self.RemoveOutsideLocations()
            else:
                if orientation == Orientation.UP:
                    self.agentLocation = [X, Y + 1]
                elif orientation == Orientation.DOWN:
                    self.agentLocation = [X, Y - 1]
                elif orientation == Orientation.LEFT:
                    self.agentLocation = [X - 1, Y]
                elif orientation == Orientation.RIGHT:
                    self.agentLocation = [X + 1, Y]
        if (previousAction == Action.GRAB):
            self.agentHasGold = True     # Only GRAB when Glitter was present
        if (previousAction == Action.CLIMB):
            pass # Nothing to do for CLIMB
        # HW9: Shooting action
        if (previousAction == Action.SHOOT):
            self.agentHasArrow = False
            self.wumpusAlive = False
            self.addLocation(self.wumpusLocation, self.safeLocations, addToSearch=True)
        if percept.stench:
            self.AddLocation(self.agentLocation, self.stenchLocations)
        if percept.breeze:
            self.AddLocation(self.agentLocation, self.breezeLocations)
        # HW5.3.a
        if percept.glitter:
            self.goldLocation = self.agentLocation
            print("Find gold at " + str(self.goldLocation))
        # clarification: track world size
        new_max = max(self.agentLocation[0], self.agentLocation[1])
        if new_max > self.worldSize:
            self.worldSize = new_max
        # HW5.3.b
        if not game_over:
            self.UpdateSafeLocations(self.agentLocation)
        # HW5.3.c
        self.AddLocation(self.agentLocation, self.visitedLocations)

    def AddLocation(self,location,location_list,addToSearch=False):
        if location not in location_list:
            location_list.append(location)
        if addToSearch:
            self.searchEngine.AddSafeLocation(location[0],location[1])
        
    def UpdateWumpusLocation(self,percept,location):
        self.location = location
        self.location[0] += 1
        self.location[1] += 1
        if (not percept.bump):
            if percept.stench:
                self.location[0] -= 1
                if (self.location in self.safeLocations):
                    self.wumpusLocation[0] = self.location[0] + 1
                    self.wumpusLocation[1] = self.location[1] - 1
                else:
                    self.wumpusLocation =  self.location
        else:
            self.location = location
            self.location[0] -= 1
            self.location[1] -= 1
            if percept.stench:
                self.location[1] += 1
                if (self.location in self.safeLocations):
                    self.wumpusLocation[0] = self.location[0] - 1
                    self.wumpusLocation[1] = self.location[1] + 1
                else:
                    self.wumpusLocation =  self.location
        return self.wumpusLocation


    def WumpusCanbeShot(self):
        # Return True is Wumpus can be shot, i.e., wumpus is alive, wumpus location known,
        # agent has arrow, and there is a safe location in the same row or column as the wumpus.
        if not self.wumpusAlive:
            return False
        if self.wumpusLocation == [0,0]:
            return  False
        if not self.agentHasGold:
            return False
        for location in self.safeLocations:
            if (location[0] == self.wumpusLocation[0]) or (location[1] == self.wumpusLocation[1]):
                return True
        return False

    def wumpusShootLocation(self):
        # Return safe location in same row or column as wumpus and orientation facing wumpus.
        # Assumes Wumpus can be shot, i.e., location known.
        for location in self.safeLocations:
            if (location[0] == self.wumpusLocation[0]): # lopcation above or below wumpus
                orientation = Orientation.UP
                if location[1] > self.wumpusLocation[1]:
                    orientation = Orientation.DOWN
                return location, orientation
            if (location[1] == self.wumpusLocation[0]):  #  location left or right of wumpus
                orientation = Orientation.RIGHT
                if location[0] > self.wumpusLocation[0]:
                    orientation = Orientation.LEFT
                return location,  orientation

    def UpdateSafeLocations(self,location):
        # HW5 requirement 3b, and HW5 clarification about not known to be unsafe locations
        # Add current and adjacent locations to safe locations, unless known to be unsafe.
        if location not in self.safeLocations:
            self.safeLocations.append(location)
            self.searchEngine.AddSafeLocation(location[0],location[1])
        for adj_loc in self.AdjacentLocations(location):
            if ((adj_loc not in self.safeLocations) and (adj_loc not in self.unsafeLocations)):
                self.safeLocations.append(adj_loc)
                self.searchEngine.AddSafeLocation(adj_loc[0],adj_loc[1])

    def SafeUnvisitedLocation(self):
        # Find and return safe unvisited location
        for location in self.safeLocations:
            if location not in self.visitedLocations:
                return location
        return None

    def notUnsafeUnvisitedLocation(self):
        # Find and return safe unvisited location
        for location in self.safeLocations:
            if location not in self.stenchLocations:
                for adj_loc in self.AdjacentLocations(location):
                    if (adj_loc not in self.visitedLocations) and (adj_loc not in self.unsafeLocations):
                        return adj_loc

    def RemoveOutsideLocations(self):
        # Know exact world size, so remove locations outside the world
        boundary = self.worldSize + 1
        for i in range(1,boundary):
            if [i,boundary] in self.safeLocations:
                self.safeLocations.remove([i,boundary])
                self.searchEngine.RemoveSafeLocation(i,boundary)
            if [boundary,i] in self.safeLocations:
                self.safeLocations.remove([boundary,i])
                self.searchEngine.RemoveSafeLocation(boundary,i)
        if [boundary,boundary] in self.safeLocations:
            self.safeLocations.remove([boundary,boundary])
            self.searchEngine.RemoveSafeLocation(boundary,boundary)
    
    def AdjacentLocations(self,location):
        # Return list of locations adjacent to given location. One row/col beyond unknown
        # world size is okay. Locations outside the world will be removed later.
        X = location[0]
        Y = location[1]
        adj_locs = []
        if X > 1:
            adj_locs.append([X-1,Y])
        if Y > 1:
            adj_locs.append([X,Y-1])
        if self.worldSizeKnown:
            if (X < self.worldSize):
                adj_locs.append([X+1,Y])
            if (Y < self.worldSize):
                adj_locs.append([X,Y+1])
        else:
            adj_locs.append([X+1,Y])
            adj_locs.append([X,Y+1])
        return adj_locs
