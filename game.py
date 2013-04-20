# Author - Billy Tumey
# Created 4/18/2013

#------ Globals ------#
import random, sys, copy, os, pygame
from pygame.locals import *

FPS = 60
TITLE = "Push Rocks 'n Shit"
TILEHEIGHT = 32 #Tile size is 32x32
TILEWIDTH = 32 
SCREENHEIGHT = 9*TILEHEIGHT
SCREENWIDTH = 20*TILEWIDTH # 16:9 aspect ratio

#Initialize 
pygame.init()
pygame.display.set_caption(TITLE)
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))

#Dictionary Key Constants
Colors = ["green","purple","red","yellow"]
PortalNums = ["Portal1","Portal2","Portal3","Portal4"]

#Directional Constants
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

#Will be filled from the parsed file "levels.txt"
levels = []
levelNumber = 0

#Each Level contains these things
Buttons,Walls,Players,Movables,Goals = [],[],[],[],[]
PortalDict = {'Portal1': [], 'Portal2': [], 'Portal3': [], 'Portal4':[]}
SwitchDict = {'red': [], 'green': [], 'purple': [], 'yellow':[]}
player1,player2,player1Goal,player2Goal = None,None,None,None
keyPressed,performedAction = False, False

#CLASS DEFINITIONS

class Portal:
    def __init__(self,pos,portalNum):
        self.portalNum = portalNum
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load('portal.png')
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
                p.x = self.otherPortal.x 
                p.y = self.otherPortal.y
                p.teleported = True
                
class Switch:
    def __init__(self,pos,color):
        self.color = color
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load('switch{0}.png'.format(color))
        self.active = True
        appendToBucket(SwitchDict,color,self)
        
    def position(self):
        return (self.x,self.y)   
        
    def setStatus(self,active):
        if (self.active == True and active == False):
            self.image = pygame.image.load('tile.png')
            self.active = active
        elif (self.active == False and active == True):
            self.image = pygame.image.load('switch{0}.png'.format(self.color))
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
        self.image = pygame.image.load('wall.png')
        Walls.append(self)
    def position(self):
        return (self.x,self.y)
    
class Button:
    def __init__(self,pos,color):
        self.color = color
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load('button{0}.png'.format(color))
        Buttons.append(self)
    def position(self):
        return (self.x,self.y)

class Goal:
    def __init__(self,pos,color):
        self.x = pos[0]
        self.y = pos[1]
        self.image = pygame.image.load('goal{0}.png'.format(color))
        Goals.append(self)
    def position(self):
        return (self.x,self.y)

class Movable:
    def __init__(self,imageName,pos,playable):
        self.direction = None
        self.imageName = imageName
        self.x = pos[0]
        self.y = pos[1]
        self.playable = playable
        self.image = pygame.image.load('{0}.png'.format(imageName))
        self.toMove = False
        if playable:
            Players.append(self)
        else:
            Movables.append(self)
    
    def setDirection(self,direction):
        self.direction = direction
        if (self.playable and direction != None):
            self.image = pygame.image.load('{0}{1}.png'.format(self.imageName,direction))
          
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
                and (not self.checkSwitchCollisions(dx,dy)) )
            
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
    levels = []
    mapLines = []
    for lineNum in range(len(content)):
        line = content[lineNum].rstrip('\r\n')
        if '-' in line:
            #This is the comment of a the levels file
            pass
        if '%' in line: #This line is part of a level
            mapLines.append(line)
        elif line == '' and len(mapLines) > 0:
            levels.append(mapLines)
            mapLines = [] #reset it for the next level
    return levels
    
    
def resetGlobals():
    global Players,Movables,Goals,Walls,Buttons
    global PortalDict, SwitchDict
    global Colors, PortalNums
    global player1,player2,player1Goal,player2Goal
    player1,player2,player1Goal,player2Goal = None,None,None,None
    PortalDict = {'Portal1': [], 'Portal2': [], 'Portal3': [], 'Portal4':[]}
    SwitchDict = {'red': [], 'green': [], 'purple': [], 'yellow':[]}
    Players,Movables,Goals,Walls,Buttons = [],[],[],[],[]
    assert(set(Colors) == set(SwitchDict.keys()))
    assert(set(PortalNums) == set(PortalDict.keys()))    

def appendToBucket(Dict, key, val):
    temp = Dict[key]
    temp.append(val)
    Dict[key] = temp
        
#Fills the map with the proper objects needed to display the level
def populateLevel(levelNumber):
    global player1,player2,player1Goal,player2Goal
    resetGlobals()
    x,y = 0,0
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
                
            #Ensure that all maps have corresponding Portals!
            elif col == "P": #Portal 1
                Portal((x,y),"Portal1")
            elif col == "p": #Portal 1 End
                Portal((x,y),"Portal1")
              
            x += TILEWIDTH
        y += TILEHEIGHT
        x = 0
        
    assertLevelCorrectness()
    
    #Match up all the Portals    
    for Portals in PortalDict.itervalues():
        for p in Portals:
            p.findOtherPortal()
            
def assertLevelCorrectness():
    try:
        assert((player1 != None) and (player2 != None))
    except AssertionError:
        print "Assertion Error on Level {0}".format(levelNumber)
        print "Need to have Player 1 and Player 2 placed on the map."
        terminate()
              
    try:
        assert((player1Goal != None) and (player2Goal != None))
    except AssertionError:
        print "Assertion Error on Level {0}".format(levelNumber)
        print "Need to have Player 1 Goal and Player 2 Goal on the map."
        terminate()    
                    
def isLevelCompleted():
    return ( (player1.position() == player1Goal.position()) 
             and (player2.position() == player2Goal.position()) )

def floodTiles():
    tile = pygame.image.load('tile.png')
    for x in range(0,SCREENWIDTH,TILEWIDTH):
        for y in range(0,SCREENHEIGHT,TILEHEIGHT):
            SCREEN.blit(tile,(x,y))
            
def fillScreen():
    floodTiles()
    
    for wall in Walls:
        SCREEN.blit(wall.image,wall.position())
        
    for SwitchList in SwitchDict.itervalues():
        for switch in SwitchList:
            switch.checkStatus()
            SCREEN.blit(switch.image,switch.position())
            
    for button in Buttons:
        SCREEN.blit(button.image,button.position())
        
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
    global levelNumber, levels, keyPressed, FPSCLOCK, performAction
    levels = readLevelsFile('levels.txt') #Populate the levels
    populateLevel(0) #Start at level 0
    FPSCLOCK = pygame.time.Clock()
    while True: #Main game loop
        #Reset player movement
        for p in Players:
            p.setDirection(None)
            p.toMove = False
        performAction = False
        keyPressed = False
            
        #Handle the game events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                terminate()
            
            #Handle Keyboard
            elif event.type == pygame.KEYDOWN:
                #Player 1 uses Arrows
                keyPressed = True
                if event.key == K_LEFT:
                    player1.setDirection(LEFT)
                    player1.toMove = True
                elif event.key == K_RIGHT:
                    player1.setDirection(RIGHT)
                    player1.toMove = True
                elif event.key == K_UP:
                    player1.setDirection(UP)
                    player1.toMove = True
                elif event.key == K_DOWN:
                    player1.setDirection(DOWN)
                    player1.toMove = True
                #Player 2 uses WSAD
                elif event.key == K_a:
                    player2.setDirection(LEFT)
                    player2.toMove = True
                elif event.key == K_d:
                    player2.setDirection(RIGHT)
                    player2.toMove = True
                elif event.key == K_w:
                    player2.setDirection(UP)
                    player2.toMove = True
                elif event.key == K_s:
                    player2.setDirection(DOWN)
                    player2.toMove = True
                elif event.key == K_SPACE:
                    performAction = True
                    
                if event.key == K_n: #Next Level
                    if (levelNumber + 1 < len(levels)):
                        levelNumber += 1
                        populateLevel(levelNumber)
                elif event.key == K_b: #Previous Level
                    if (levelNumber - 1 >= 0 ):
                        levelNumber -= 1
                        populateLevel(levelNumber)
                elif event.key == K_r:
                    populateLevel(levelNumber) #Reset Level
                    
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