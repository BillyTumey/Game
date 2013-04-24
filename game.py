# Author - Billy Tumey
# Created 4/18/2013

#------ Globals ------#
import random, sys, copy, os, pygame
from pygame.locals import *

FPS = 60
TITLE = "Push Rocks 'n Shit"
TILEHEIGHT = 32 #Tile size is 32x32
TILEWIDTH = 32 
SCREENHEIGHT = 13*TILEHEIGHT
SCREENWIDTH = 24*TILEWIDTH # 16:9 aspect ratio

#Initialize 
imageFolder = "images/"
pygame.init()
pygame.display.set_caption(TITLE)
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))

#Dictionary Key Constants
LeverNums = ['Lever1']
Colors = ["green","purple","red","yellow"]
PortalNums = ["Portal1","Portal2","Portal3","Portal4"]

#Directional Constants
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

#Will be filled from the parsed file "levels.txt"
levels = []
portals = []
levelNumber = 0

#Each Level contains these things
TILES = []
xOffset,yOffset = 0,0
Buttons,Walls,Players,Movables,Goals = [],[],[],[],[]
PortalDict,SwitchDict,LeverDict = {},{},{}
player1,player2,player1Goal,player2Goal = None,None,None,None
keyPressed,performedAction = False, False

#CLASS DEFINITIONS

class Portal:
    def __init__(self,pos,portalNum):
        self.portalNum = portalNum
        self.x,self.y = pos[0],pos[1]
        self.image = pygame.image.load(os.path.join(imageFolder,'portal.png'))
        self.otherPortal = None
        appendToBucket(PortalDict,portalNum,self)
        
    def position(self):
        return (self.x,self.y)
    
    def findOtherPortal(self):
        PortalPair = PortalDict[self.portalNum]
        if self == PortalPair[0]:
            self.otherPortal = PortalPair[1]
        else:
            self.otherPortal = PortalPair[0]
                           
    def checkUse(self):
        global performAction
        for p in Players:
            if (self.position() == p.position() and not p.teleported): #Player standing on the portal
                #Can't teleport to a spot if there's a rock on the other portal
                is_rock_on_spot = False
                for m in Movables:
                    if (self.otherPortal.position() == m.position()):
                        is_rock_on_spot = True
                if not is_rock_on_spot:
                    p.x = self.otherPortal.x 
                    p.y = self.otherPortal.y
                    p.teleported = True
                
class Switch:
    def __init__(self,pos,color):
        self.color = color
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load(os.path.join(imageFolder,'switch{0}.png'.format(color)))
        self.active = True
        appendToBucket(SwitchDict,color,self)
        
    def position(self):
        return (self.x,self.y)   
        
    def setStatus(self,active):
        if (self.active == True and active == False):
            self.image = pygame.image.load(os.path.join(imageFolder,'tile.png'))
            self.active = active
        elif (self.active == False and active == True):
            self.image = pygame.image.load(os.path.join(imageFolder,'switch{0}.png'.format(self.color)))
            self.active = active
            
    def checkStatus(self):
        flag = True
        for b in Buttons:
            if (b.color == self.color):
                for m in Movables:
                    if (b.position() == m.position()):
                        flag = False
        self.setStatus(flag)
                    
class Wall:
    def __init__(self,pos):
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load(os.path.join(imageFolder,'wall.png'))
        Walls.append(self)
        
    def position(self):
        return (self.x,self.y)
    
class Button:
    def __init__(self,pos,color):
        self.color = color
        self.x,self.y = pos[0],pos[1]
        self.image = pygame.image.load(os.path.join(imageFolder,'button{0}.png'.format(color)))
        Buttons.append(self)
        
    def position(self):
        return (self.x,self.y)
    
class Lever:
    def __init__(self,pos,direction,leverNum):
        self.justChanged = False
        self.leverNum = leverNum
        self.direction = direction
        self.x,self.y = pos[0],pos[1]
        self.image = pygame.image.load(os.path.join(imageFolder,'lever{0}.png'.format(direction)))
        appendToBucket(LeverDict,leverNum,self)
        
    def position(self):
        return (self.x,self.y)
    
    def changeDirection(self):
        if self.direction == RIGHT:
            self.direction = LEFT
        else:
            self.direction = RIGHT
        self.image = pygame.image.load(os.path.join(imageFolder,'lever{0}.png'.format(self.direction)))
    
    def checkUse(self):
        for p in Players:
            if p.x == self.x:
                if ( (p.y + TILEHEIGHT == self.y) and p.direction == DOWN):
                    self.changeDirection()
                elif ( (p.y - TILEHEIGHT == self.y) and p.direction == UP):
                    self.changeDirection()
            if p.y == self.y:
                if ( (p.x + TILEWIDTH == self.x) and p.direction == RIGHT):
                    self.changeDirection()
                elif ( (p.x - TILEWIDTH == self.x) and p.direction == LEFT):
                    self.changeDirection()                
                 
class Goal:
    def __init__(self,pos,color):
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load(os.path.join(imageFolder,'goal{0}.png'.format(color)))
        Goals.append(self)
    def position(self):
        return (self.x,self.y)

class Movable:
    def __init__(self,imageName,pos,playable):
        self.direction = None
        self.imageName = imageName
        self.x,self.y = pos[0],pos[1]
        self.playable = playable
        self.image = pygame.image.load(os.path.join(imageFolder,'{0}.png'.format(imageName)))
        self.toMove = False
        if playable:
            Players.append(self)
        else:
            Movables.append(self)
    
    def setDirection(self,direction):
        self.direction = direction
        if (self.playable and direction != None):
            self.image = pygame.image.load(os.path.join(imageFolder,'{0}{1}.png'.format(self.imageName,direction)))
          
    def move_single_axis(self,dx,dy):
        self.x += dx
        self.y += dy
        
    def position(self):
        return (self.x,self.y)

    def boundaryCheck(self,dx,dy):
        if self.direction == UP:  
            if ( self.y + dy < 0 ):
                return False
        elif self.direction == DOWN:
            if ( self.y + dy > (SCREENHEIGHT-TILEHEIGHT) ):
                return False
        elif self.direction == RIGHT:
            if ( self.x + dx > (SCREENWIDTH-TILEWIDTH) ):
                return False
        elif self.direction == LEFT: 
            if ( self.x + dx < 0 ):
                return False
        return True
    
    def checkSwitchCollisions(self,dx,dy):
        for SwitchList in SwitchDict.itervalues():
            for switch in SwitchList:
                if ( switch.active and (self.y + dy == switch.y) and (self.x + dx == switch.x) ):
                    return True
        return False
                
    def checkPlayerCollisions(self,dx,dy):
        for p in Players:
            if (self != p):
                if ( (self.y + dy == p.y) and (self.x + dx == p.x) ):
                    return True
        return False
                
    def checkMovableCollisions(self,dx,dy):
        for m in Movables:
            if ( (self.y + dy == m.y) and (self.x + dx == m.x) ):
                    return True
        return False
    
    def checkLeverCollisions(self,dx,dy):
        for Levers in LeverDict.itervalues():
            for l in Levers:
                if ( (self.y + dy == l.y) and (self.x + dx == l.x)):
                    return True
        return False
    
    def checkWallCollisions(self,dx,dy):
        for w in Walls:
            if ( (self.y + dy == w.y) and (self.x + dx == w.x) ):
                return True
        return False
           
    def pushMovable(self,dx,dy):
        for m in Movables:
            if ( (self.y + dy == m.y) and (self.x + dx == m.x) ):
                m.setDirection(self.direction)
                if (not m.checkMovableCollisions(dx,dy)): #You can't an object if it bumps into another object
                    m.move()
                
    def validMove(self,dx,dy):
        return ( self.boundaryCheck(dx,dy) 
                and ( not self.checkPlayerCollisions(dx,dy) 
                and (not self.checkWallCollisions(dx,dy) ))
                and (not self.checkSwitchCollisions(dx,dy)) 
                and (not self.checkLeverCollisions(dx,dy)))
            
    def move(self):
        dx,dy = 0,0
        if self.direction == UP:
            dx,dy = 0,-TILEHEIGHT
        elif self.direction == DOWN:
            dx,dy = 0,TILEHEIGHT
        elif self.direction == RIGHT:
            dx,dy = TILEWIDTH,0
        elif self.direction == LEFT: 
            dx,dy = -TILEWIDTH,0
        if (self.validMove(dx,dy)):
            self.pushMovable(dx,dy)
            if (not self.checkMovableCollisions(dx,dy)):
                self.move_single_axis(dx,dy)
                
def terminate():
    pygame.quit()
    sys.exit()
    
def readLevelsFile(filename):
    assert os.path.exists(filename), 'Cannot find the level file: %s' % (filename)
    mapFile = open(filename, 'r')
    # Each level must end with a blank line
    content = mapFile.readlines() + ['\r\n']
    mapFile.close()
    levels, portals = [],[]
    mapLines, mapPortals = [],{}
    for lineNum in range(len(content)):
        line = content[lineNum].rstrip('\r\n')
        if '>>' in line:
            #This line contains portal information
            portalData = line.strip('>')
            key = int(portalData.split(":")[0])
            portalLocations = []
            for portalLocation in portalData.split(":")[1].split(";"):
                x,y = map(int, portalLocation.strip().replace('(', "").replace(')',"").split(',')) #value stripping
                portalLocations.append((x,y))
            mapPortals[key] = portalLocations
        if '-' in line:
            #This is the comment of a the levels file
            pass
        if '%' in line: #This line is part of a level
            mapLines.append(line)
        elif line == '' and len(mapLines) > 0:
            portals.append(mapPortals)
            mapPortals = {}
            levels.append(mapLines)
            mapLines = [] #reset it for the next level
    
    return (levels,portals)
    
def resetGlobals():
    global xOffset,yOffset
    global Players,Movables,Goals,Walls,Buttons,TILES
    global PortalDict, SwitchDict, LeverDict
    global player1,player2,player1Goal,player2Goal
    xOffset,yOffset = 0,0
    player1,player2,player1Goal,player2Goal = None,None,None,None
    PortalDict = {}
    SwitchDict = {'red': [], 'green': [], 'purple': [], 'yellow':[]}
    LeverDict = {'Lever1': []}
    Players,Movables,Goals,Walls,Buttons,TILES = [],[],[],[],[],[]
    #TODO - MAYBE REWRITE THE SETS AND SWITCHES TO WORK LIKE PORTALS?
    assert(set(Colors) == set(SwitchDict.keys()))   
    assert(set(LeverNums) == set(LeverDict.keys()))

def appendToBucket(Dict, key, val):
    try:
        temp = Dict[key] #The key exists - get the existing bucket
    except KeyError:
        temp = [] #The key doesn't already exist - make a new empty bucket
    temp.append(val)
    Dict[key] = temp
    
def setupLevelPortals(levelNumber):
    this_levels_portals = portals[levelNumber]
    for key in this_levels_portals:
        portalLocations = this_levels_portals[key]
        for p in portalLocations:
            x,y = p
            Portal((x*32+xOffset,y*32+yOffset),key)
            
#Fills the map with the proper objects needed to display the level
def populateLevel(levelNumber):
    global player1,player2,player1Goal,player2Goal
    resetGlobals()
    (x,y) = adjustOffsets()
    setupLevelPortals(levelNumber)
    
    for row in levels[levelNumber]:
        for col in row:
            if col == "W":
                Wall((x, y))
            elif col == "1":
                if player1 == None:
                    player1 = Movable("characterGreen",(x,y), True)
                else:
                    print "Can't have more than one Player 1 on Level {0}".format(levelNumber)
                    terminate()
            elif col == "2":
                if player2 == None:
                    player2 = Movable("characterBlue",(x,y), True)
                else:
                    print "Can't have more than one Player 2 on Level {0}".format(levelNumber)
                    terminate()
                         
            elif col == "G":
                if player1Goal == None:
                    player1Goal = Goal((x,y),"Green")
                else:
                    print "Can't have more than one Player 1 Goal on Level {0}".format(levelNumber)
                    terminate()
                    
            elif col == "B":
                if player2Goal == None:
                    player2Goal = Goal((x,y),"Blue")
                else:
                    print "Can't have more than one Player 2 Goal on Level {0}".format(levelNumber)
                    terminate()
                    
            elif col == "O":
                Movable("rock",(x,y), False) 
                
            elif col == "9": #green switch
                Switch((x,y),"green")
            elif col == "(": #green button
                Button((x,y),"green")
            elif col == "8": #purple
                Switch((x,y),"purple")
            elif col == "*": #purple button
                Button((x,y),"purple")
            elif col == "7": #red 
                Switch((x,y),"red")
            elif col == "&": #red button
                Button((x,y),"red")
            elif col == "6": #yellow
                Switch((x,y),"yellow")
            elif col == "^": #yellow button
                Button((x,y),"yellow")
                    
            elif col == "@":
                check = False
                for portal in PortalDict.itervalues():
                    for p in portal:
                        if ( (x,y) == p.position() ):
                            check = True
                try:
                    assert(check)
                except:
                    print "Level Design Error on Level {0}".format(levelNumber)
                    print "Your level mapping and coordinate information does not coincide."
                    terminate()
                                 
            #Ensure that all maps have corresponding Levers!
            elif col == "L": #Lever 1
                Lever((x,y),RIGHT,"Lever1")
            elif col == "l": #Lever 1
                Lever((x,y),RIGHT,"Lever1")
            
            if col != "%":
                TILES.append((x,y))
              
            x += TILEWIDTH
        y += TILEHEIGHT
        x = xOffset
        
    assertLevelCorrectness()
    
    #Match up all the Portals    
    for Portals in PortalDict.itervalues():
        for p in Portals:
            p.findOtherPortal()
            
def adjustOffsets():     
    global xOffset,yOffset
    levelHeight = len(levels[levelNumber])
    maxWidth = -1
    for row in levels[levelNumber]:
        if len(row) > maxWidth:
            maxWidth = len(row)
    levelWidth = maxWidth-1
    #SCREENHEIGHT = 18*TILEHEIGHT
    #SCREENWIDTH = 32*TILEWIDTH # 16:9 aspect ratio
    xOffset = (SCREENWIDTH - levelWidth*TILEWIDTH)/2
    yOffset = (SCREENHEIGHT - levelHeight*TILEHEIGHT)/2
    return (xOffset,yOffset)

def assertLevelCorrectness():
    try:
        assert((player1 != None) and (player2 != None))
    except AssertionError:
        print "Level Design Error on Level {0}".format(levelNumber)
        print "Need to have Player 1 and Player 2 placed on the map."
        terminate()
              
    try:
        assert((player1Goal != None) and (player2Goal != None))
    except AssertionError:
        print "Level Design Error on Level {0}".format(levelNumber)
        print "Need to have Player 1 Goal and Player 2 Goal on the map."
        terminate()    
                    
def isLevelCompleted():
    return ( (player1.position() == player1Goal.position()) 
             and (player2.position() == player2Goal.position()) )

def floodTiles(): #TODO - find a way to surround the area with walls if they're not in the levels
    tile = pygame.image.load(os.path.join(imageFolder,'tile.png'))
    for tileSpot in TILES:
        SCREEN.blit(tile,tileSpot)
            
def fillScreen():
    SCREEN.fill((0,0,0))
    floodTiles()
    for wall in Walls:
        SCREEN.blit(wall.image,wall.position())
        
    for SwitchList in SwitchDict.itervalues():
        for switch in SwitchList:
            switch.checkStatus()
            SCREEN.blit(switch.image,switch.position())
            
    for button in Buttons:
        SCREEN.blit(button.image,button.position())
        
    for Levers in LeverDict.itervalues():
        for l in Levers:
            if keyPressed and performAction:
                l.checkUse()
            l.justChanged = False
            SCREEN.blit(l.image,l.position())
            
    for Portals in PortalDict.itervalues():
        for p in Portals:
            if keyPressed and performAction:
                p.checkUse()
            SCREEN.blit(p.image,p.position())
            
    for goal in Goals:
        SCREEN.blit(goal.image,goal.position())
        
    for p in Players:
        if (keyPressed and p.toMove):
            p.move()
        p.teleported = False
        SCREEN.blit(p.image,p.position())
        
    for m in Movables:
        SCREEN.blit(m.image,m.position())  
        

def main():
    global levelNumber, levels, keyPressed, FPSCLOCK, performAction, portals
    levels, portals = readLevelsFile('levels.txt') #Populate the levels
    populateLevel(0) #Start at level 0
    FPSCLOCK = pygame.time.Clock()
    while True: #Main game loop
        #Reset player movement
        for p in Players:
            p.toMove = False
        performAction = False
        keyPressed = False
            
        #Handle the game events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                terminate()
                
            #Handle Keyboard events
            elif event.type == pygame.KEYDOWN: 
                keyPressed = True
                keys = pygame.key.get_pressed()
                #Player 1
                if keys[K_LEFT]:
                    player1.setDirection(LEFT)
                    if not keys[K_LSHIFT]:
                        player1.toMove = True
                elif keys[K_RIGHT]:
                    player1.setDirection(RIGHT)
                    if not keys[K_LSHIFT]:
                        player1.toMove = True
                elif keys[K_UP]:
                    player1.setDirection(UP)
                    if not keys[K_LSHIFT]:
                        player1.toMove = True
                elif keys[K_DOWN]:
                    player1.setDirection(DOWN)
                    if not keys[K_LSHIFT]:
                        player1.toMove = True
                #Player 2
                if keys[K_a]:
                    player2.setDirection(LEFT)
                    if not keys[K_LSHIFT]:
                        player2.toMove = True
                elif keys[K_d]:
                    player2.setDirection(RIGHT)
                    if not keys[K_LSHIFT]:
                        player2.toMove = True
                elif keys[K_w]:
                    player2.setDirection(UP)
                    if not keys[K_LSHIFT]:
                        player2.toMove = True
                elif keys[K_s]:
                    player2.setDirection(DOWN)
                    if not keys[K_LSHIFT]:
                        player2.toMove = True   
                        
                #Handle Actions and Level Navigation
                elif keys[K_b]:
                    if (levelNumber -1 >= 0):
                        levelNumber -= 1
                        populateLevel(levelNumber)
                elif keys[K_n]:
                    if (levelNumber + 1 < len(levels)):
                        levelNumber += 1
                        populateLevel(levelNumber)
                elif keys[K_r]:
                    populateLevel(levelNumber)
                elif keys[K_SPACE]:
                    performAction = True
                     
        #Check if the level is completed
        if (isLevelCompleted()):
            if (levelNumber + 1 < len(levels)):
                levelNumber += 1
                populateLevel(levelNumber)
            else:
                print "You beat the game!"
                terminate()
            
            #Update the display
        fillScreen()    
        pygame.display.update() 
        FPSCLOCK.tick(FPS)
            
if __name__ == '__main__':
    main()