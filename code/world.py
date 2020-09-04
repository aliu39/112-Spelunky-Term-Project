## CONTAINS ALL BLOCK CLASSES AND STAGE CLASS (handles stage/entity generation and storage) ##

import pygame
from pygame.locals import *

import random
import copy

import entity
import lighting

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, size, imgPath = 'stone.png'):
        pygame.sprite.Sprite.__init__(self)
        self.s = size
        self.x = x
        self.y = y
        self.pict = pygame.image.load(imgPath) #immutable image ('pict') allows for smooth rescaling
        if imgPath == 'stone.png':
            rotation = random.randint(0,3)
            self.pict = pygame.transform.rotate(self.pict, 90*rotation)
        self.initDims()
        self.transparent = False

    def initDims(self):
        self.image = pygame.transform.scale(self.pict, (self.s, self.s))
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        
    def __eq__(self, other):
        return (isinstance(other, Block) and self.x == other.x and self.y == other.y)

    def __hash__(self):
        return hash((self.x, self.y))

class Rope(Block):
    def __init__(self, x, y, rectX, rectY, size):
        super().__init__(x,y, size, 'rope.png')
        self.rect.x = rectX
        self.rect.y = rectY
        self.transparent = True
    
    def initDims(self):
        super().initDims()
        self.image = pygame.transform.rotate(self.image, 90)

class Flare(Block): #flares are drawn over darkFilter
    def __init__(self, x, y, rectX, rectY, size):
        super().__init__(x,y, size, 'flare.png')
        self.rect.x = rectX
        self.rect.y = rectY
        self.transparent = True

class Treasure(Block):
    def __init__(self, x, y, size):
        super().__init__(x,y,size,'treasure.png')

class Dirt(Block):
    def __init__(self, x, y, size):
        super().__init__(x,y,size,'dirt.png')

class Spike(Block):
    def __init__(self, x, y, size):
        super().__init__(x,y,size,'spike.png')
        self.transparent = True
    
    def checkRemove(self, STAGE): #returns True if self should be removed (i.e. there is no floor beneath it)
        row, col = int(self.y/self.s), int(self.x/self.s)
        if STAGE.map[row+1][col] != 1 and STAGE.map[row+1][col] != 3:
            STAGE.map[row][col] = 0
            return True
        else: 
            return False

class ExitBlock(Block): #block at exits to signal game win
    def __init__(self, x, y, size):
        super().__init__(x,y,size,'green.png')
        self.transparent = True

class Chest(Block):
    def __init__(self, x, y, size):
        super().__init__(x,y,size,'chest.png')
        self.type = random.randint(1,5) #5 hard coded types of chests (see below)
    
    def addItems(self, player):
        if self.type == 1: #lighting
            chance = random.randint(1,3)
            if chance == 1: 
                player.torches.insert(0,lighting.Torch())
            else: 
                player.flares += 2
        elif self.type == 2: #one of everything
            player.flares += 1
            player.bombs += 1
            player.swords += 1
        elif self.type == 3: #weapons
            chance = random.randint(1,2)
            if chance == 1: player.swords += 1
            player.bombs += chance
        elif self.type == 4: #stage removal
            chance = random.randint(1,2)
            player.bombs += chance
            if chance == 1: player.shovel = True
        elif self.type == 5: #guaranteed shovel or torch + sword
            if player.shovel:
                player.torches.insert(0,lighting.Torch())
                player.swords += 1
            else:
                player.shovel = True

##STAGE GENERATION FUNCTIONS / STAGE CLASS##

##NEIGHBOR COUNTING FUNCTIONS##

#Returns the number of cells alive in a ring around a given cell
def countAliveNeighbors(cave, col, row, steps, alive=1):
    count = 0
    for i in range(-1*steps, steps+1):
        for j in range(-1, 2): #MAKES NATURALLY MORE HORIZONTAL
            neighbor_row = col+i
            neighbor_col = row+j
            #middle is self, not neighbor
            if(i == 0 and j == 0):
                pass
            #off map counts as alive
            elif(neighbor_row < 0 or neighbor_col < 0 or neighbor_row >= len(cave) or neighbor_col >= len(cave[0])):
                count += 1
            elif(cave[neighbor_row][neighbor_col] == alive):
                count += 1
    return count

#used on a live block: returns true if two adjacents (not diagonal) are spaces and next to each other
#originally in an attempt to connect rooms, but now used to clear out space for some variety when used between game of life steps
def adjacentSpace(oldMap,row,col): 
    dirPairs = [(-1,0,0,1), (1,0,0,1), (1,0,0,-1), (-1,0,0,-1)]
    for (i1,j1,i2,j2) in dirPairs:
        count = 0
        neighbor_row1 = row+i1
        neighbor_col1 = col+j1
        #off map counts as alive
        if(neighbor_row1 < 0 or neighbor_col1 < 0 or neighbor_row1 >= len(oldMap) or neighbor_col1 >= len(oldMap[0])):
            pass
        elif(oldMap[neighbor_row1][neighbor_col1] == 0):
            count += 1

        neighbor_row2 = row+i2
        neighbor_col2 = col+j2
        #off map counts as alive
        if(neighbor_row2 < 0 or neighbor_col2 < 0 or neighbor_row2 >= len(oldMap) or neighbor_col2 >= len(oldMap[0])):
            pass
        elif(oldMap[neighbor_row2][neighbor_col2] == 0):
            count += 1

        if count == 2: return True

    return False

#completely random generation (see game of life step and Stage class functions for actual procedural generation)
def generateCave(height, width, deathLimit, birthLimit, initialChance, dirtChance):
    cave = [([1] * width) for row in range(height)]

    for row in range(1,len(cave)-1):
        for col in range(1,len(cave[0])-1):
            if(random.random() >= initialChance):
                cave[row][col] = 0
            elif row > 0 and row < len(cave)-1 and col > 0 and col < len(cave[0])-1:
                if random.random() < dirtChance:
                    cave[row][col] = 3

    return cave

## IMPORTANT LEVEL GENERATION CODE (ALSO SEE: SCANLINEGETROOM, FUNCTIONS IN Stage.furnish()) ##
#NOW ACCOUNTS FOR STONE AND DIRT
def gameOfLifeStep(oldMap, deathLimit, birthLimit): #results in best dirt splotches if used with step-rmvD-step
    newMap = copy.deepcopy(oldMap)
    for row in range(len(oldMap)):
        for col in range(len(oldMap[0])):
            #stone neighbors
            neighbors = countAliveNeighbors(oldMap, row, col, 1)
            neighbors_3 = countAliveNeighbors(oldMap, row, col, 3)
            #dirt neighbors
            neighborsD = countAliveNeighbors(oldMap, row, col, 1, 3)
            neighbors_3D = countAliveNeighbors(oldMap, row, col, 3, 3)

            #DEATH: blocks with not enough neighbors around them turn into spaces
            if(oldMap[row][col]==1 or oldMap[row][col]==3): #deaths factor both stone and dirt as alive
                if(neighbors + neighborsD < deathLimit):
                    newMap[row][col] = 0
            #BIRTH: spaces with enough neighbors around them are filled in as blocks
            else:
                if(neighbors > birthLimit and neighborsD <= 2): #prioritizes birthing of stone, to prevent large chunks of dirt
                    newMap[row][col] = 1
                elif(neighbors + neighborsD > birthLimit):
                    if row > 0 and col > 0 and row < len(oldMap) - 1 and col < len(oldMap) - 1:
                        newMap[row][col] = 3
                    else: newMap[row][col] = 1
                elif(neighbors_3 + neighbors_3D <= 1): #birthing of blocks in big spaces
                    if(neighbors_3 > 0):
                        newMap[row][col] = 3
                        #add dirt in big empty spaces only if 1 stone in area 
                        #(used with rmvD's clearing out, ultimately results in more dirt on edges) 
                    else:
                        newMap[row][col] = 1
    return newMap

def removeDiagonalsStep(oldMap):  
    newMap = copy.deepcopy(oldMap)
    for row in range(len(oldMap)):
        for col in range(len(oldMap[0])):
            if oldMap[row][col] == 1:
                if adjacentSpace(oldMap,row,col):
                    newMap[row][col] = 0
    return newMap

##FLOOD FILL FUNCTIONS##
def scanlineGetRoom(row, col, map, stage): #wrapper
    newRoom = set()
    shortLines = []
    recursiveScanlineFloodFill(row, col, map, stage, newRoom)
    return newRoom

#adds adjacent (neighbors but not diagonal) spaces to room line by line
def recursiveScanlineFloodFill(row, col, map, stage, room, depth=0): #destructive #also returns list of floors
    stage.calls += 1
    if depth > stage.depth: stage.depth = depth
    if depth > 980: 
        print('max')
        return None

    x, y = col, row
    while (x < len(map[0])-1 and (map[y][x] == 0 or map[y][x] == 2)): #to the right
        room.add((y,x))
        x += 1

    x = col-1
    while (x > 0 and (map[y][x] == 0 or map[y][x] == 2)): #to the left
        room.add((y,x))
        x -= 1
    
    x = col
    while (x < len(map[0])-1 and (map[y][x] == 0 or map[y][x] == 2)): #to the right
        if y < len(map)-2 and (map[y+1][x] == 0 or map[y+1][x] == 2) and (y+1,x) not in room: #scanlines below
            recursiveScanlineFloodFill(y+1, x, map, stage, room, depth+1)
        if y > 1 and (map[y-1][x] == 0 or map[y-1][x] == 2) and (y-1,x) not in room: #scanlines above
            recursiveScanlineFloodFill(y-1, x, map, stage, room, depth+1)
        x += 1

    x = col-1
    while (x > 0 and (map[y][x] == 0 or map[y][x] == 2)): #to the left
        if y < len(map)-2 and (map[y+1][x] == 0 or map[y+1][x] == 2) and (y+1,x) not in room: #scanlines below
            recursiveScanlineFloodFill(y+1, x, map, stage, room, depth+1)
        if y > 1 and (map[y-1][x] == 0 or map[y-1][x] == 2) and (y-1,x) not in room: #scanlines above
            recursiveScanlineFloodFill(y-1, x, map, stage, room, depth+1)
        x -= 1

    return room

##SPECIAL BLOCK GENERATION HELPERS (spikes, treasures, chests)##
def isFloor(row, col, map, countTreasures=False):
    if countTreasures:
        return row > 0 and row < len(map) and col > 0 and col < len(map[0])-1 and (map[row][col] == 1 or map[row][col] == 3 or map[row][col] == 2) and map[row-1][col] == 0 
    else:
        return row > 0 and row < len(map) and col > 0 and col < len(map[0])-1 and (map[row][col] == 1 or map[row][col] == 3) and map[row-1][col] == 0 
    #can't be on top, right, and left borders

def isTerrain(row, col, map):
    return map[row][col] == 1 or map[row][col] == 3 or map[row][col] == 2 or map[row][col] == 5 #loot counts

def countAboveSpaces(row, col, map): #counts space above a floor
    count = 0
    i, j = row-1, col
    while map[i][j] == 0:
        count += 1
        i -= 1
    return count

class Stage(object):
    def __init__(self, height, width, block_s, snakes):
        #self.map = MAP2 #for testing
        self.height, self.width, self.size = height, width, height*width
        #these parameters are hard coded based on what I think makes the best stage, they can be tampered with though
        self.deathLimit = 2
        self.birthLimit = 4
        self.initialChance = .4
        self.dirtChance = .05 #best kept very low
        self.block_s = block_s
        self.map = generateCave(self.height, self.width, self.deathLimit, self.birthLimit, self.initialChance, self.dirtChance)
        self.entities = set() #sprite objects
        self.maxSnakes = snakes
        self.exitBlocks = set()
        self.initStage()
        self.calls = 0 #for stage generation report
        self.depth = 0
        self.snakes = 0

    def initStage(self): #map-->stage #removes player-placed blocks (ropes and flares)
        self.stage = set()
        self.exitBlocks = set()
        self.spikes = set()
        self.loot = set() #treasures and chests
        for row in range(len(self.map)):
            for col in range(len(self.map[0])):
                if (self.map[row][col] == 1):
                    if row == 0 or col == 0 or row == len(self.map)-1 or col == len(self.map[0])-1:
                        newBlock = Block(col*self.block_s, row*self.block_s, self.block_s, 'stone3.png')
                    else:
                        newBlock = Block(col*self.block_s, row*self.block_s, self.block_s)
                    self.stage.add(newBlock)
                elif (self.map[row][col] == 2):
                    newBlock = Treasure(col*self.block_s, row*self.block_s, self.block_s)
                    self.stage.add(newBlock)
                    self.loot.add(newBlock)
                elif (self.map[row][col] == 3):
                    newBlock = Dirt(col*self.block_s, row*self.block_s, self.block_s)
                    self.stage.add(newBlock)
                elif (self.map[row][col] == 4):
                    newBlock = Spike(col*self.block_s, row*self.block_s, self.block_s)
                    self.stage.add(newBlock)
                    self.spikes.add(newBlock)
                elif (self.map[row][col] == 5):
                    newBlock = Chest(col*self.block_s, row*self.block_s, self.block_s)
                    self.stage.add(newBlock)
                    self.loot.add(newBlock)
                elif (self.map[row][col] == 6):
                    newBlock = ExitBlock(col*self.block_s, row*self.block_s, self.block_s)
                    self.stage.add(newBlock)
                    self.exitBlocks.add(newBlock)

    def scroll(self,dx,dy): #scrolls stage and entities
        for block in self.stage:
            block.rect.x -= dx
            block.rect.y -= dy
        for entity in self.entities:
            entity.rect.x -= dx
            entity.rect.y -= dy

    def changeSize(self,newSize, DX=0, DY=0): #recenters stage on starting level, though
        for block in self.stage:
            block.x, block.y = block.x/block.s * newSize, block.y/block.s * newSize
            block.s = newSize
            block.initDims()
        self.block_s = newSize
        self.scroll(DX,DY)
    
    def storeRooms(self, printReport=True):
        self.rooms = []
        spaces = 0
        for row in range(1,len(self.map)-1):
            for col in range(1,len(self.map[0])-1):
                if (self.map[row][col] == 0 or self.map[row][col] == 2):
                    spaces += 1
                    inOldRoom = False
                    for oldRoom in self.rooms:
                        if (row,col) in oldRoom:
                            inOldRoom = True
                    if not inOldRoom:
                        newRoom = scanlineGetRoom(row, col, self.map, self)
                        self.rooms.append(newRoom)

        if printReport:
            print('-----STAGE GENERATION REPORT-----')
            print('RECURSION:', self.calls, 'calls,', self.depth, 'depth')
            print(spaces, 'SPACES')
            roomSizes = []
            for room in self.rooms:
                size = len(room)
                spaces -= size
                roomSizes.append(str(size))
            print('ROOM SIZES:', ','.join(roomSizes))
            print(len(self.rooms), 'ROOMS')
            print(spaces*-1, 'overcounted spaces')
            print('---------------------------------')
            self.calls = 0
    
    def newStage(self): #completely remake stage, minus spikes, treasures, snakes
        print('------------NEW STAGE------------')
        self.map = generateCave(self.height, self.width, self.deathLimit, self.birthLimit, self.initialChance, self.dirtChance)
        self.entities, self.spikes, self.loot, self.exitBlocks = set(), set(), set(), set()
        self.step()
        self.rmvD()
        self.step()

    def furnish(self): #make pathways and spawn special blocks (does not clear old ones, so preferably use with newStage)
        self.createExits()
        self.addTreasure() #two per room
        self.connectRooms()
        self.addSpikes()
        self.addChests(self.size//500)
        #self.spawnSnakes() #problems with sandbox mode--now manually called

    ##SPAWNING FUNCTIONS##
    def addTreasure(self):
        minTreasures = 1
        for room in self.rooms:
            treasuresPerRoom = minTreasures + len(room)//800
            count = 0
            for (row,col) in room:
                if count == treasuresPerRoom:
                    break
                if isFloor(row+1, col, self.map) and (row > len(self.map)//5 or col > len(self.map[0])//5): 
                    #placed on ground, and not too close to start
                    self.map[row][col] = 2
                    count += 1
            print(count, 'treasures')
        self.initStage()
        self.storeRooms()
    
    def addChests(self, maxChests):
        maxRoom = None
        maxRoomSize = 0
        for room in self.rooms:
            if len(room) > maxRoomSize: 
                maxRoomSize = len(room)
                maxRoom = room
        count = 0
        for (row,col) in maxRoom:
            if count == maxChests:
                break
            if isFloor(row+1, col, self.map): 
                #placed on ground, and not too close to start
                self.map[row][col] = 5
                count += 1
        unplaced = maxChests - count
        print(count, 'chests')
        print(unplaced, 'unplaced')
        self.initStage()
        self.storeRooms()
    
    def addSpikes(self):
        for block in self.stage:
            row, col = int(block.y/block.s), int(block.x/block.s)
            if isFloor(row, col, self.map):
                aboveSpaces = countAboveSpaces(row, col, self.map)
                #single spike pits
                if isTerrain(row-1,col-1, self.map) and isTerrain(row-1,col+1, self.map) and aboveSpaces > 2:
                    addSpike = random.randint(0,3)
                    if addSpike == 1:
                        self.map[row-1][col] = 4
                #double spike pits
                elif isTerrain(row-1,col-1, self.map) and isFloor(row, col+1, self.map) and isTerrain(row-1,col+2, self.map) and aboveSpaces > 2:
                    addSpike = random.randint(0,2)
                    if addSpike == 1:
                        self.map[row-1][col] = 4
                        self.map[row-1][col+1] = 4
                #triple spike pits
                elif isTerrain(row-1,col-1, self.map) and isFloor(row, col+1, self.map) and isFloor(row, col+2, self.map) and isTerrain(row-1,col+3, self.map) and aboveSpaces > 2:
                    addSpike = random.randint(0,2)
                    if addSpike == 1:
                        self.map[row-1][col] = 4
                        self.map[row-1][col+1] = 4
                        self.map[row-1][col+2] = 4
                else: #put spikes at bottom of big falls (>6)
                    if aboveSpaces > 16: aboveSpaces = 16 #cap
                    if aboveSpaces > 5:
                        addSpike = random.randint(0,25-aboveSpaces) #1/20 to 1/10 chance
                        if addSpike == 1:
                            self.map[row-1][col] = 4

        self.initStage()
        self.storeRooms()

    def spawnSnakes(self):
        snakes = 0
        for block in self.loot: #higher chance to spawn on loot
            if snakes == self.maxSnakes: break
            row, col = int(block.y/block.s), int(block.x/block.s)
            if isFloor(row, col, self.map, True):
                spawn = random.randint(0,10) 
                if spawn == 1:
                    self.entities.add(entity.Snake(block))
                    snakes += 1
        for block in self.stage:
            if snakes == self.maxSnakes: break
            row, col = int(block.y/block.s), int(block.x/block.s)
            if isFloor(row, col, self.map, True):
                spawn = random.randint(0,10)
                if spawn == 1:
                    self.entities.add(entity.Snake(block))
                    snakes += 1
        print(len(self.entities), 'snakes')
        self.snakes = len(self.entities)

    ##FUNCTIONS CREATING PATHS##
    def connectRooms(self): #destructive
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        for room in self.rooms:
            testCount = 0
            shortestTunnel = []
            shortestTunnelLength = len(self.map[0]) #used as max possible tunnel length
            connectedRoom = set() #store the room that's connected
            for (row, col) in room:
                for dir in dirs:
                    newTunnel = self.tunnel(row, col, dir, room)
                    if newTunnel != None and newTunnel[0] < shortestTunnelLength:
                        shortestTunnel = newTunnel[1]
                        connectedRoom = newTunnel[2]
                testCount += 1
                if testCount == len(room)//10 + 1: break #tests an amount of points in room correlated with its size
            #clear out tunnel
            if len(room) <= 9 or len(connectedRoom) <= 9:
                count = 0
                for (row, col) in shortestTunnel: #100% connect with dirt if very small room
                    if count < 9: #ten dirt placed max
                        self.map[row][col] = 3 
                        count += 1
                    else:
                        self.map[row][col] = 0
            elif len(room) <= 25 or len(connectedRoom) <= 25 or shortestTunnelLength <= 3:
                useDirt = random.randint(0,1)
                if useDirt:
                    count = 0
                    for (row, col) in shortestTunnel: 
                        if count < 9: #ten dirt placed max
                            self.map[row][col] = 3
                            count += 1
                        else:
                            self.map[row][col] = 0 #50% chance to be connected with dirt if small room
                else:
                    for (row, col) in shortestTunnel: 
                        self.map[row][col] = 0
            else:
                for (row, col) in shortestTunnel:
                    self.map[row][col] = 0
        self.initStage()
        self.storeRooms()

    def tunnel(self, row, col, dir, room): #non-destructively returns possible tunnel in given direction
        removed = []
        x, y = col, row
        while True:
            if x <= 0 or y <= 0 or x >= len(self.map[0])-1 or y >= len(self.map)-1: #cannot tunnel in border
                return None

            if self.map[y][x] == 1:
                removed.append((y,x))
            else:
                if (y, x) in room:
                    removed = []
                else:
                    for otherRoom in self.rooms:
                        if (y,x) in otherRoom:
                            return (len(removed), removed, otherRoom)
            x += dir[1]
            y += dir[0]

    def createExits(self):
        dirs = [(0,1), (1,0), (0,-1)] #favors going: right,down,left
        maxExits = len(self.map) * len(self.map[0]) // 800 + 1 #limits number of exits based on size of stage
        exits = 0
        for i in range(-1,-1*len(self.rooms)-1, -1):
            room = self.rooms[i]
            testCount = 0
            shortestTunnel = []
            tunnelDir = None
            shortestTunnelLength = len(self.map[0]) #used as max possible tunnel length
            for (row, col) in room:
                for dir in dirs:
                    newTunnel = self.tunnelForExit(row, col, dir, room)
                    if newTunnel != None and newTunnel[0] < shortestTunnelLength:
                        shortestTunnel = newTunnel[1]
                        tunnelDir = newTunnel[2]
                testCount += 1
                if testCount == len(room)//10 + 1: break #tests an amount of points in room correlated with its size
            #clear out tunnel
            if len(shortestTunnel) > 0:
                for i in range(len(shortestTunnel)):
                    (row, col) = shortestTunnel[i]
                    if i == len(shortestTunnel) - 1: #add exitBlock
                        self.map[row][col] = 6
                    else:
                        self.map[row][col] = 0
                exits += 1
                print(shortestTunnel)
                print('exit made')
            if exits == maxExits: break
        self.initStage()
        self.storeRooms()

    def tunnelForExit(self, row, col, dir, room): #non-destructively returns possible tunnel in given direction
        if dir == (0, -1) and row <= len(self.map)//2: 
            #prevents easy exits on the left (can only be on bottom third)
            return None
        removed = []
        x, y = col, row
        while True:
            if x < 0 or y < 0 or x >= len(self.map[0]) or y >= len(self.map):
                return (len(removed), removed, dir)

            if self.map[y][x] == 1:
                removed.append((y,x))
            else:
                if (y, x) in room:
                    removed = []
                else:
                    for otherRoom in self.rooms:
                        if (y,x) in otherRoom:
                            return None
            x += dir[1]
            y += dir[0]

    ##MANUAL SANDBOX FUNCTION ONLY##
    def step(self):
        #remove non-stone blocks so it won't bug the generation
        for row in range(len(self.map)):
            for col in range(len(self.map[0])):
                if self.map[row][col] != 0 and self.map[row][col] != 1 and self.map[row][col] != 3:
                    self.map[row][col] = 0

        self.map = gameOfLifeStep(self.map, self.deathLimit, self.birthLimit)
        self.initStage()
        self.storeRooms()
    
    ##MANUAL SANDBOX FUNCTION ONLY##
    def rmvD(self):
        #remove non-stone and dirt blocks so it won't bug the generation
        for row in range(len(self.map)):
            for col in range(len(self.map[0])):
                if self.map[row][col] != 0 and self.map[row][col] != 1 and self.map[row][col] != 3:
                    self.map[row][col] = 0

        self.map = removeDiagonalsStep(self.map)
        self.initStage()
        self.storeRooms()

    ##MANUAL SANDBOX FUNCTION ONLY##
    def fillRoom(self):
        for (row,col) in self.rooms[0]:
            self.map[row][col] = 1
        self.initStage()
        self.storeRooms()

'''
#old code--LESS EFFICIENT RECURSION (block-by-block flood fill)
#recursion depth exceeded for large maps

def recursiveFloodFill(row,col,map,room,stage,depth=0): #actual recursion
    if depth > 980: #prevent stack overflow (still leads to overcounting of rooms)
        print('MAX!!')
        return None

    stage.calls += 1
    if depth > stage.depth: stage.depth = depth
    if (row,col) in room:
        return None

    room.add((row,col))
    for (i,j) in [(1,0), (-1,0), (0,1), (0,-1)]:
        newRow = row + i
        newCol = col + j
        if newRow < 0 or newCol < 0 or newRow >= len(map) or newCol >= len(map[0]):
            pass
        elif (newRow,newCol) in room:
            pass
        elif (map[newRow][newCol] == 0) and not (i == 0 and j == 0):
            addToRoom(row+i,col+j,map,room,stage,depth+1)

def getRoom(row, col, oldRooms, map,stage): #wrapper
    for room in oldRooms:
        if (row, col) in room:
            return None

    newRoom = set()
    recursiveFloodFill(row,col,map,newRoom,stage)
    return newRoom
'''