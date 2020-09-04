##CONTAINS PLAYER CLASS AND NON-PLAYER ENTITY CLASSES##
##(entities different from blocks in their ability to constantly update / move on own,##
## be drawn on top of darkness, and be quickly removed when dead (self.state == -1)##

import pygame
from pygame.locals import *
import random
import math

import lighting
import world

class Player(pygame.sprite.Sprite):
	def __init__(self, blockSize, windowSize):
		pygame.sprite.Sprite.__init__(self)
		self.block_s = blockSize
		self.width, self.height = int(.78*self.block_s), self.block_s-5

		self.spritesheet = pygame.image.load('playerActions.png')
		self.spritesheet = pygame.transform.scale(self.spritesheet, (self.height*13, self.height*13))
		#dictionary of indexes of certain actions, as on the 13x13 spritesheet
		self.action_dict = {'stop': [(0,0)],
			  'run': [(col+1, 0) for col in range(7)],
			  'jump': [(11,3)],
			  'fall': [(8,3)], 
			  'duck': [(9,0)],
			  'crawl': [(col+5, 1) for col in range(7)],
			  'hang': [(0,7)],
			  'climb': [(col, 7) for col in range(10)]
				}
		self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA) #redefined in self.setAction()
		self.rect = self.image.get_rect()
		self.action = 'stop'
		self.actionCount = 0
		self.faceLeft = False
		self.ducked = False

		self.x = windowSize[0]//2-self.block_s//2 #centered and immutable
		self.y = windowSize[1]//2-self.block_s//2 #centered and immutable
		self.rect.x = self.x
		self.rect.y = self.y
		self.xSpd = self.block_s//4
		self.jumpSpd = self.block_s//3
		self.gravity = 1 #very sensitive
		self.xVel = 0
		self.yVel = 0

		self.moveLeft = False
		self.moveRight = False
		self.jumps = 0
		self.isClimb = False

		self.dead = False

		self.collidedSides = {'top': False, 'bottom': False, 'right': False, 'left': False}
		self.touchedBlocks = {'top': None, 'bottom': None, 'right': None, 'left': None}

		#HELD ITEMS (rope is infinite)
		self.torches = [lighting.Torch() for i in range(6)]
		self.torches2 = []
		self.flares = 5
		self.bombs = 1
		self.swords = 1
		self.shovel = False
		self.treasures = 0
		self.killedSnakes = 0
		self.demoMode = False #gives infinite non-torch items

	def setAction(self):
		self.actionCount %= len(self.action_dict[self.action])
		startX, startY = (self.height-self.width)//2, 0
		actionIndex = self.action_dict[self.action][self.actionCount]
		self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
		self.image.blit(self.spritesheet, (0,0), (startX + self.height * actionIndex[0], startY + self.height * actionIndex[1], self.width, self.height))
		
		if self.faceLeft:
			self.image = pygame.transform.flip(self.image, True, False)

		self.actionCount += 1

	def getCollidedBlocks(self, STAGE): 
		#returns collided blocks in a set
		collided = set()
		for block in STAGE.stage:
			#collided is when rects intersect
			if self.rect.colliderect(block.rect): 
				collided.add(block)
		return collided
	
	def getTouchedBlocks(self, STAGE):
		#destructively modifies self.touchedBlocks
		self.touchedBlocks = {'top': None, 'bottom': None, 'right': None, 'left': None} #reset
		for block in STAGE.stage:
			if not block.transparent:
				#touched is when rects right next to each other, but not intersecting
				if (self.rect.bottom > block.rect.top and self.rect.bottom < block.rect.bottom) or \
					(self.rect.top > block.rect.top and self.rect.top < block.rect.bottom):
					if self.rect.right == block.rect.left:
						self.touchedBlocks['right'] = block
					elif self.rect.left == block.rect.right:
						self.touchedBlocks['left'] = block
				if (self.rect.left < block.rect.right and self.rect.left > block.rect.left) or \
					(self.rect.right < block.rect.right and self.rect.right > block.rect.left):
					if self.rect.bottom == block.rect.top:
						if self.touchedBlocks['bottom'] == None:
							self.touchedBlocks['bottom'] = block
						else:
							if self.faceLeft:
								if block.x < self.touchedBlocks['bottom'].x:
									self.touchedBlocks['bottom'] = block
							else:
								if block.x > self.touchedBlocks['bottom'].x:
									self.touchedBlocks['bottom'] = block
					elif self.rect.top == block.rect.bottom:
						if self.touchedBlocks['top'] == None:
							self.touchedBlocks['top'] = block
						else:
							if self.faceLeft:
								if block.x < self.touchedBlocks['top'].x:
									self.touchedBlocks['top'] = block
							else:
								if block.x > self.touchedBlocks['top'].x:
									self.touchedBlocks['top'] = block

	def move(self, STAGE, dx, dy):
		#reset collisions, and check again
		self.collidedSides = {'top': False, 'bottom': False, 'right': False, 'left': False}
		
		STAGE.scroll(dx, 0)
		collided = self.getCollidedBlocks(STAGE)
		for block in collided:
			if not block.transparent:
				if dx > 0:
					STAGE.scroll(block.rect.left - self.rect.right, 0)
					self.collidedSides['right'] = True
					self.xVel = 0
				elif dx <= 0: #less than or equal to favors going to the right when spawned
					STAGE.scroll(block.rect.right - self.rect.left, 0)
					self.collidedSides['left'] = True 
					self.xVel = 0

		STAGE.scroll(0, dy)
		collided = self.getCollidedBlocks(STAGE)
		for block in collided:
			if not block.transparent:
				if dy > 0:
					STAGE.scroll(0, block.rect.top - self.rect.bottom)
					self.collidedSides['bottom'] = True
					self.jumps = 1
					self.yVel = 0
				elif dy <= 0: #less than or equal to favors going down when spawned
					STAGE.scroll(0, block.rect.bottom - self.rect.top)
					self.collidedSides['top'] = True
		
		self.getTouchedBlocks(STAGE)

	def placeRope(self, STAGE, MSG_CODE):
		if not self.ducked:
			if self.touchedBlocks['bottom'] == None:
				MSG_CODE = max(MSG_CODE, 3) #stand on ground!
			else:
				startBlock = self.touchedBlocks['bottom']
				x = startBlock.x
				y = startBlock.y - self.block_s
				rectY = startBlock.rect.y - self.block_s
				ropesPlaced = 0
				while STAGE.map[int(y/self.block_s)][int(x/self.block_s)] == 0 or STAGE.map[int(y/self.block_s)][int(x/self.block_s)] == -1  and ropesPlaced < 100:
					STAGE.map[int(y/self.block_s)][int(x/self.block_s)] = -1
					STAGE.stage.add(world.Rope(x,y, startBlock.rect.x, rectY, self.block_s))
					y -= self.block_s
					rectY -= self.block_s
					ropesPlaced += 1
		else:
			MSG_CODE = max(MSG_CODE, 5) #stand up!
		return MSG_CODE
	
	def placeFlare(self, STAGE, MSG_CODE):
		if not self.ducked:
			if (self.flares > 0 or self.demoMode): 
				if self.touchedBlocks['bottom'] == None:
					MSG_CODE = max(MSG_CODE, 3) #stand on ground!
				else:
					startBlock = self.touchedBlocks['bottom']
					x = startBlock.x
					y = startBlock.y - self.block_s
					rectX = startBlock.rect.x
					rectY = startBlock.rect.y - self.block_s
					STAGE.map[int(y/startBlock.s)][int(x/startBlock.s)] = -1
					STAGE.stage.add(world.Flare(x,y, rectX, rectY, self.block_s))
					if not self.demoMode: self.flares -= 1
			else:
				MSG_CODE = max(MSG_CODE, 6) #no items left!
		else:
			MSG_CODE = max(MSG_CODE, 5) #stand up!
		return MSG_CODE

	def collect(self, STAGE, MSG_CODE):
		if not self.ducked:
			if self.faceLeft: dirs = ['left', 'right', 'top', 'bottom'] #priority of digging
			else: dirs = ['right', 'left', 'top', 'bottom']
			for dir in dirs:
				block = self.touchedBlocks[dir]
				if type(block) == world.Treasure:
					STAGE.map[int(block.y/block.s)][int(block.x/block.s)] = 0
					STAGE.stage.discard(block)
					STAGE.loot.discard(block)
					self.treasures += 1
					return MSG_CODE #return ensures only one block removed
				elif type(block) == world.Dirt:
					if (self.shovel or self.demoMode):
						STAGE.map[int(block.y/block.s)][int(block.x/block.s)] = 0
						STAGE.stage.discard(block)
					else:
						MSG_CODE = max(MSG_CODE, 4) #need shovel!
					return MSG_CODE
				elif type(block) == world.Chest:
					block.addItems(self)
					STAGE.map[int(block.y/block.s)][int(block.x/block.s)] = 0
					STAGE.stage.discard(block)
					STAGE.loot.discard(block)
		else:
			MSG_CODE = max(MSG_CODE, 5) #stand up!
		return MSG_CODE
	
	def placeBomb(self, STAGE, time, MSG_CODE):
		def bomb(dir): #if valid direction, places bomb and returns True
			block = self.touchedBlocks[dir]
			if (block != None and not block.transparent):
				explosion = Explosion(block)
				STAGE.entities.add(explosion)
				STAGE.entities.add(Bomb(time, block, explosion))
				print('bomb placed')
				return True
			return False
		
		def place():
			if not self.demoMode: self.bombs -= 1
		if not self.ducked:
			if (self.bombs > 0 or self.demoMode):
				if self.faceLeft:
					if bomb('left'): place()
					elif bomb('right'): place()
					elif bomb('bottom'): place()
					elif bomb('top'): place()
				else:
					if bomb('right'): place()
					elif bomb('left'): place()
					elif bomb('bottom'): place()
					elif bomb('top'): place()
			else:
				MSG_CODE = max(MSG_CODE, 6) #no more of this item!
		else:
			MSG_CODE = max(MSG_CODE, 5) #stand up!
		return MSG_CODE

	def scroll(self,dx, dy): #for scroll mode
		self.rect.x -= dx
		self.rect.y -= dy

class Bomb(pygame.sprite.Sprite):
	def __init__(self, time, block, explosion):
		pygame.sprite.Sprite.__init__(self)
		self.block = block
		self.explosion = explosion #corresponding hidden explosion
		self.image = pygame.Surface((self.block.s, self.block.s))
		self.image.fill((50,50,50))
		self.rect = self.image.get_rect()
		self.rect.x, self.rect.y = self.block.rect.x, self.block.rect.y
		self.timePlaced = time
		self.state = 0 #-1 is dead
	
	def update(self, time, STAGE, player):
		if self.state != -1:
			timePassed = time - self.timePlaced
			if timePassed % 1000 == 0:
				self.explosion.state = 1 #trigger explosion
				self.image.fill((255,255,255))
				self.state = -1
			elif timePassed % 100 == 0: #blink every .1 s
				if self.state == 1:
					self.image.fill((255,0,0))
					self.state = 0
				else:
					self.image.fill((50,50,50))
					self.state = 1
	
	def __eq__(self, other):
		return (isinstance(other, Bomb) and self.block == other.block)
	
	def __hash__(self):
		return hash((self.block.x, self.block.y))

class Explosion(pygame.sprite.Sprite):
	def __init__(self, block):
		self.block = block
		self.state = 0
		self.spriteX, self.spriteY = 0, 0
		self.s = self.block.s * 7 #make explosion a little bigger than just a block
		self.spritesheet = pygame.image.load('explosion.png')
		self.spritesheet = pygame.transform.scale(self.spritesheet, (self.s*4, self.s*4))
		self.image = pygame.Surface((self.s, self.s), pygame.SRCALPHA)
		self.rect = self.image.get_rect()
		self.rect.center = self.block.rect.center
		self.deathRect = pygame.Rect((0,0), (self.block.s*3, self.block.s*3)) 
		self.deathRect.center = self.block.rect.center #where the player gets killed (actual image is much bigger than displayed explosion)

	def update(self, time, STAGE, player):
		self.deathRect.center = self.block.rect.center
		if self.state == 1:
			if self.spriteY < 4:
				self.image = pygame.Surface((self.s, self.s), pygame.SRCALPHA)
				self.image.blit(self.spritesheet, (0,0), ((self.s-3) * self.spriteX, (self.s+1) * self.spriteY, self.s, self.s))
				self.image.set_colorkey((255,255,255)) #make background of sprite transparent
				self.spriteX += 1
				if self.spriteX >= 4:
					self.spriteX = 0
					self.spriteY += 1
			else:
				exploded = set() #set of removed coordinates
				row0, col0 = int(self.block.y/self.block.s), int(self.block.x/self.block.s)
				dirs = [(0,0), (0,1), (0,-1), (1,0), (-1,0), (-1, -1), (1,1), (-1, 1), (1, -1), (0,2), (0,-2), (2,0), (-2,0)]
				for dir in dirs:
					row = row0 + dir[1]
					col = col0 + dir[0]
					#cannot blow up stage borders
					if row > 0 and col > 0 and row < len(STAGE.map)-1 and col < len(STAGE.map[0])-1 and STAGE.map[row][col] != 0: 
						block = world.Block(col*self.block.s,row*self.block.s,self.block.s)
						STAGE.stage.discard(block)
						#loot NOT resistant to explosions!
						if STAGE.map[row][col] == 2 or STAGE.map[row][col] == 5:
							STAGE.loot.discard(block)
						elif STAGE.map[row][col] == 4:
							STAGE.spikes.discard(block)
						STAGE.map[row][col] = 0
				self.state = -1
			#kill player and snakes touching at apex of explosion
			if self.spriteY == 2:
				if player.rect.colliderect(self.deathRect) and not player.demoMode:
					player.dead = True
				for ent in STAGE.entities:
					if type(ent) == Snake:
						if ent.rect.colliderect(self.deathRect):
							ent.state = -1
							player.killedSnakes += 1

	def __eq__(self, other):
		return (isinstance(other, Explosion) and self.block == other.block)
	
	def __hash__(self):
		return hash((self.block.x, self.block.y))

class Snake(pygame.sprite.Sprite):
	def __init__(self, block):
		pygame.sprite.Sprite.__init__(self)
		self.block = block
		self.block_s = block.s
		self.width, self.height = self.block_s, self.block_s

		self.spritesheet = pygame.image.load('snakeActions.png')
		self.spritesheet = pygame.transform.scale(self.spritesheet, (self.height*11, self.height*2))
		#dictionary of indexes of certain actions, as on the 2x11 spritesheet
		self.action_dict = {'patrol': [(col,0) for col in range(11)],
			  'chase': [(col, 1) for col in range(7)],
				}
		self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA) #redefined in self.setAction()
		self.rect = self.image.get_rect()
		self.action = 'patrol'
		self.actionCount = 0
		left = random.randint(0,1)
		self.faceLeft = left

		self.x = self.block.x
		self.y = self.block.y
		self.rect.x = self.block.rect.x
		self.rect.y = self.block.rect.y - self.block_s
		self.xSpd = self.block_s//10
		self.chaseSpd = self.block_s//6
		self.jumpSpd = self.block_s//3
		self.gravity = 3 #very sensitive
		self.xVel = self.xSpd
		if self.faceLeft: self.xSpd *= -1
		self.yVel = 0

		self.moveLeft = False
		self.moveRight = False
		self.jumps = 0

		self.collidedSides = {'top': False, 'bottom': False, 'right': False, 'left': False}
		self.botBlock = None
		self.oldBotBlock = None
		self.repeatBotBlocks = 0
		self.state = 0

	def setAction(self):
		self.actionCount %= len(self.action_dict[self.action])
		startX, startY = (self.height-self.width)//2, 0
		actionIndex = self.action_dict[self.action][self.actionCount]
		self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
		self.image.blit(self.spritesheet, (0,0), (startX + self.height * actionIndex[0], startY + self.height * actionIndex[1], self.width, self.height))
		
		if self.faceLeft:
			self.image = pygame.transform.flip(self.image, True, False)

		self.actionCount += 1
			
	def getCollidedBlocks(self, STAGE): 
		#returns collided blocks in a set
		collided = set()
		self.botBlock = None #reset
		for block in STAGE.stage:
			if not block.transparent:
				#collided is when rects intersect
				if self.rect.colliderect(block.rect): 
					collided.add(block)
				
				#touched is when rects right next to each other, but not intersecting
				if (self.xVel < 0 and self.rect.left <= block.rect.right and self.rect.left >= block.rect.left) or \
					(self.xVel > 0 and self.rect.right <= block.rect.right and self.rect.right >= block.rect.left):
					if abs(self.rect.bottom - block.rect.top) <= 2:
						if self.botBlock == None:
							self.botBlock = block
						else:
							if self.faceLeft:
								if block.x < self.botBlock.x:
									self.botBlock = block
							else:
								if block.x > self.botBlock.x:
									self.botBlock = block
		return collided

	def move(self, STAGE, dx, dy):
		#reset collisions, and check again
		self.collidedSides = {'top': False, 'bottom': False, 'right': False, 'left': False}
		
		self.rect.x += dx
		collided = self.getCollidedBlocks(STAGE)
		for block in collided:
			if not block.transparent:
				if dx > 0:
					self.rect.right = block.rect.left
					self.collidedSides['right'] = True
				elif dx <= 0:
					self.rect.left = block.rect.right
					self.collidedSides['left'] = True 

		self.rect.y += dy
		collided = self.getCollidedBlocks(STAGE)
		for block in collided:
			if not block.transparent:
				if dy > 0:
					self.rect.bottom = block.rect.top
					self.collidedSides['bottom'] = True
					self.jumps = 1
					self.yVel = 0
				elif dy <= 0:
					self.rect.top = block.rect.bottom
					self.collidedSides['top'] = True

	def update(self, time, STAGE, player): #similar to player physics update
		dxPlayer = self.rect.centerx - player.rect.centerx #distances from player
		dyPlayer = self.rect.centery - player.rect.centery

		#chase player when in range
		if not player.ducked and abs(dxPlayer) <= 225 and abs(dyPlayer) <= 150: #1/4 of screen
			self.state = 1
			self.repeatBotBlocks = 0
			
		if self.state == 1:
			if dxPlayer <= -1*self.block_s:
				self.xVel = self.chaseSpd
			elif dxPlayer >= self.block_s:
				self.xVel = self.chaseSpd * -1
			else:
				if dxPlayer > 0: self.faceLeft = True
				elif dxPlayer < 0: self.faceLeft = False
			
			if dyPlayer >= self.block_s*2//3 and self.jumps > 0 and self.yVel == 0: #snakes cannot jump in the air
				self.yVel = self.jumpSpd * -1
				self.jumps = 0
			
			#turn off
			if (player.ducked or abs(dxPlayer) > 225 or abs(dyPlayer) > 150): #1/4 of screen
				if self.xVel < 0: self.xVel = self.xSpd * -1
				else: self.xVel = self.xSpd
				self.state = 0

		#top collision momentum halting
		if self.collidedSides['top']:
			self.yVel = 0

		#gravity
		if self.state == 1:	
			if not self.collidedSides['bottom']:
				self.yVel += self.gravity
		elif (self.yVel != 0):
			self.yVel = self.block_s//4 #quickly fall down if turned off and in the air
		#in patrol mode, don't fall
		else:
			if self.collidedSides['right'] or self.collidedSides['left']:
				self.xVel *= -1
			elif self.botBlock == None:
				self.xVel *= -1
		
			#track botBlocks--if same one repeated without another one, stop moving (on top of one block)
			if self.botBlock == self.oldBotBlock: 
				self.repeatBotBlocks += 1
			elif self.botBlock != None: 
				self.oldBotBlock = self.botBlock
				self.repeatBotBlocks = 0
			
			if self.repeatBotBlocks > 20:
				self.repeatBotBlocks = 0
				self.xVel = 0
				
		#change facing
		if self.xVel > 0:
			self.faceLeft = False
		elif self.xVel < 0:
			self.faceLeft = True
		
		#move (taking stage collision into account) 
		self.move(STAGE, self.xVel, self.yVel)

		#change actions
		if self.state == 0: self.action = 'patrol'
		elif self.state == 1: self.action = 'chase'

		#actually change actions (animate)
		self.setAction()

		#kill player if chasing and collide, or kill self if player has sword
		if self.state == 1 and player.rect.colliderect(self.rect):
			if player.swords > 0:
				self.state = -1
				player.killedSnakes += 1
				if not player.demoMode: player.swords -= 1
			else:
				if not player.demoMode: player.dead = True

	def __eq__(self, other):
		return (isinstance(other, Snake) and self.block == other.block)
	
	def __hash__(self):
		return hash((self.block.x, self.block.y))