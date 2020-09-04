##CONTAINS LIGHTING EFFECT--TORCH ITEM CLASS AND DARKNESS FILTER CLASS (DRAWN ON TOP OF STAGE)##

import pygame
from pygame.locals import *

class DarkFilter(object): #change later to act different based on game mode

	def __init__(self, windowSize):
		self.windowSize = windowSize
		self.image = pygame.surface.Surface(self.windowSize)
		self.image.fill((0,0,0)) #black filter

	def update(self, player, flares): #ALSO UPDATES PlAYER TORCHES
		self.image = pygame.surface.Surface(self.windowSize)
		self.image.fill((0,0,0)) #black filter

		self.flareSize = Torch.st_size - 4
		for flare in flares:
			light = pygame.image.load('gradient.jpg')
			light = pygame.transform.scale(light, (flare.s*self.flareSize, flare.s*self.flareSize))
			self.image.blit(light, (flare.rect.x-(self.flareSize-1)//2*flare.s, flare.rect.y-(self.flareSize-1)//2*flare.s))

		if player.torches != []:
			currTorch = player.torches[-1]
			if currTorch.life == 0:
				player.torches.pop()
				self.update(player, flares) #recursively keeps looking for not-dead torches
			else:
				self.lightSize = currTorch.size #multiplied by playerDims #use odd num for proper centering
				light = pygame.image.load('gradient.jpg')
				light = pygame.transform.scale(light, (player.block_s*self.lightSize, player.block_s*self.lightSize))
				self.image.blit(light, (player.x-(self.lightSize-1)//2*player.block_s, player.y-(self.lightSize-1)//2*player.block_s))
			
class Torch(object): #holdable item (not drawn)
	st_size = 11 #standard initial size (odd num)
	expTime = 4000 #expires by one life every 4 seconds (based on original 20ms clock tick)
	def __init__(self):
		self.size = Torch.st_size #decrements by 2 until drops to 0. Directly used for lightSize
		self.life = Torch.st_size // 2 * 3

	def expire(self): #called in main by EXPIRETORCH event
		self.life -= 1
		if self.life < Torch.st_size//2-1:
			self.size -= 2
			if (self.size < 3):
				self.size = 0
		elif self.life < Torch.st_size:
			self.size = Torch.st_size - 2