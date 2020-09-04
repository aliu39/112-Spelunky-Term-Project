## RUNS ALL FILES TOGETHER (ONLY ONE WITH NON-FUNCTION/CLASS CODE) ##
## STORES/INITIALIZES GAME PARAMETERS AND HANDLES TIMING + FLOW BETWEEN DIFFERENT SCREENS ##

import pygame, sys

from pygame.locals import *
pygame.init()

WINDOW_SIZE = (900, 600)
window = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
screen_width = WINDOW_SIZE[0]
screen_height = WINDOW_SIZE[1]

clock = pygame.time.Clock()
pygame.display.set_caption("Spelunky")

def loadText(text, font):
	textSurface = font.render(text, True, (255,153,51))
	return (textSurface, textSurface.get_rect())

def startScreen():
	import TXT
	runThisMode = True
	while runThisMode:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
			
			if event.type == MOUSEBUTTONDOWN:
				runThisMode = False
				helpScreen()
	
		window.fill((255,80,80))
		backImage = pygame.image.load('startScreen.png')
		backImage = pygame.transform.scale(backImage, WINDOW_SIZE)
		window.blit(backImage,(0,0))
		TXT.drawStartMsg(window, screen_width, screen_height)
		pygame.display.update()
		clock.tick(60)

def helpScreen():
	import TXT
	help1 = pygame.transform.scale(pygame.image.load('help1.png'), (screen_width-20, screen_height-20))
	help2 = pygame.transform.scale(pygame.image.load('help2.png'), (screen_width-20, screen_height-20))
	help3 = pygame.transform.scale(pygame.image.load('help3.png'), (screen_width-20, screen_height-20))
	screen = 0
	runThisMode = True
	while runThisMode:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
			if event.type == KEYDOWN:
				if event.key == K_h:
					runThisMode = False
				if event.key == K_LEFT:
					screen -= 1
					screen %= 3
				if event.key == K_RIGHT:
					screen += 1
					screen %= 3
		
		window.fill((0,0,0))
		if screen == 0:
			window.blit(help1, (10, 10))
		elif screen == 1:
			window.blit(help2, (10, 10))
		elif screen == 2:
			window.blit(help3, (10, 10))

		pygame.display.update()

def helpScreenSB():
	helpSB = pygame.transform.scale(pygame.image.load('helpSB.png'), (screen_width-20, screen_height-20))
	runThisMode = True
	while runThisMode:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
			if event.type == KEYDOWN:
				if event.key == K_h:
					runThisMode = False
		
		window.blit(helpSB, (10, 10))
		pygame.display.update()

def endScreen(timePassed, treasures, snakesKilled, died = False):
	import TXT
	if died: SCORE = 0
	else: SCORE = 3000 - timePassed//100 #subtract from ten minutes (measured in something..weird)
	displayScore = 0
	bonuses = treasures + snakesKilled
	bonus = 100 #points per treasure / snakeKilled
	finalScore = SCORE + bonus*bonuses
	print(timePassed, 'ms passed')
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
			if event.type == MOUSEBUTTONDOWN:
				runGame()
		window.fill((0,0,0))
		(displayScore, bonuses) = TXT.drawEndMsg(window, screen_width, screen_height, SCORE, displayScore, treasures, snakesKilled, bonuses, bonus, died)
		pygame.display.update()
		clock.tick(20)

def runGame():
	#INITIALIZE GAME
	blocks_per_window = 18 #length wise
	block_s = screen_width // blocks_per_window 
	sandbox_block_s = block_s
	STAGE_SIZE = (90,60)
	numSnakes = 10 #too many lags the game a significant amount

	import world
	import entity
	import lighting
	import physics
	import TXT

	STAGE = world.Stage(STAGE_SIZE[1],STAGE_SIZE[0],block_s,numSnakes)
	STAGE.newStage()
	STAGE.furnish()
	STAGE.spawnSnakes()
	player = entity.Player(block_s, WINDOW_SIZE)

	EXPIRETORCH = pygame.USEREVENT + 1
	pygame.time.set_timer(EXPIRETORCH, lighting.Torch.expTime) 
	DARK = True
	darkness = lighting.DarkFilter(WINDOW_SIZE)

	SANDBOXMODE = False
	SCROLLMODE = False
	DX, DY = 0,0 #for sandbox scrolling
	TIMEPASSED = 0 #ms
	
	MSG_CODE = 0
	LAST_MSG_TIME = None
	LAST_MSG = None

	def redrawGameWindow():
		#draw stage
		window.fill((0,0,0))#(210,180,140)) #tan
		
		flares = []
		for block in STAGE.stage:
			if type(block) != world.Flare:
				window.blit(block.image, (block.rect.x, block.rect.y))
			else:
				flares.append(block) #flares drawn later, over dark

		if not SANDBOXMODE:
			#lighting effect here
			if DARK:
				darkness.update(player, flares) #update lighting
				window.blit(darkness.image, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
		
		#draw flares
		for block in flares:
			window.blit(block.image, (block.rect.x, block.rect.y))

		#entities drawn over darkness so still visible when torch dead
		for ent in STAGE.entities:
			window.blit(ent.image, (ent.rect.x, ent.rect.y))

		window.blit(player.image, (player.rect.x, player.rect.y))

		window.blit(TXT.icons(player), (0,0)) #icon display

		if player.demoMode: TXT.drawDemoMsg(window) #messages display (game message called elsewhere)
		if SCROLLMODE: TXT.drawModeMsg(window, 1) 
		elif SANDBOXMODE: TXT.drawModeMsg(window, 2)
		else: TXT.drawGameMsg(window, MSG_CODE)
		pygame.display.update()

	while True:
		if SANDBOXMODE:
			d = 15
			(x,y) = pygame.mouse.get_pos()
			if x < 100:
				STAGE.scroll(-1*d,0)
				DX -= d
			elif x > WINDOW_SIZE[0] - 100:
				STAGE.scroll(d,0)
				DX += d
			if y < 100:
				STAGE.scroll(0,-1*d)
				DY -= d
			elif y > WINDOW_SIZE[1] - 100:
				STAGE.scroll(0,d)
				DY += d
			
			#EVENT LOOP / CONTROLS
			for event in pygame.event.get(): 
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == KEYDOWN:
					if event.key == K_s: #exit sandbox
						STAGE.scroll(-1*DX, -1*DY)
						DX,DY=0,0
						STAGE.changeSize(block_s)
						STAGE.spawnSnakes()
						SANDBOXMODE = False
					if event.key == K_DOWN: #zoom out
						sandbox_block_s = int(sandbox_block_s/1.25)
						STAGE.changeSize(sandbox_block_s, DX, DY)
					if event.key == K_UP: #zoom in
						sandbox_block_s = int(sandbox_block_s*1.25)
						STAGE.changeSize(sandbox_block_s, DX, DY)
					if event.key == K_h:
						helpScreenSB()
					
					#semi-automatic generation
					if event.key == K_RIGHT: #make new stage
						STAGE.newStage()
						STAGE.changeSize(sandbox_block_s, DX, DY)
					if event.key == K_SPACE: #make pathways and spawn special blocks
						STAGE.furnish()
						STAGE.changeSize(sandbox_block_s, DX, DY)

					#manual generation
					if event.key == K_r: #new completely random map
						STAGE = world.Stage(STAGE_SIZE[1],STAGE_SIZE[0],block_s,numSnakes)
						STAGE.changeSize(sandbox_block_s, DX, DY)
					if event.key == K_g: #game of life step
						STAGE.step()
						STAGE.changeSize(sandbox_block_s, DX, DY)
					if event.key == K_d: #clears out stage, basically
						STAGE.rmvD()
						STAGE.changeSize(sandbox_block_s, DX, DY)
					if event.key == K_f: #fills first room to upper left
						STAGE.fillRoom()
						STAGE.changeSize(sandbox_block_s, DX, DY)
					
		elif SCROLLMODE:
			d = 20
			#scroll with mouse
			(x,y) = pygame.mouse.get_pos()
			if x < 100:
				STAGE.scroll(-1*d,0)
				player.scroll(-1*d,0)
				DX -= d
			elif x > WINDOW_SIZE[0] - 100:
				STAGE.scroll(d,0)
				player.scroll(d,0)
				DX += d
			if y < 100:
				STAGE.scroll(0,-1*d)
				player.scroll(0,-1*d)
				DY -= d
			elif y > WINDOW_SIZE[1] - 100:
				STAGE.scroll(0,d)
				player.scroll(0,d)
				DY += d

			#EVENT LOOP / CONTROLS
			for event in pygame.event.get(): 
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == KEYDOWN:
					if event.key == K_SPACE: #exit scrollmode
						STAGE.scroll(-1*DX, -1*DY)
						player.scroll(-1*DX, -1*DY)
						DX,DY=0,0
						SCROLLMODE = False
					if event.key == K_h:
						helpScreen()
		else:
			TIMEPASSED += 20 
			#I measured the average tick of one loop to be about 20ms on avg early on,
			#but now its more like 100ms. I kept the increments of 20 though.
			if MSG_CODE < 3:
				MSG_CODE = 0
			elif LAST_MSG_TIME == None or LAST_MSG != MSG_CODE:
				LAST_MSG_TIME = TIMEPASSED
				LAST_MSG = MSG_CODE
			else:
				if (TIMEPASSED - LAST_MSG_TIME) // 200 > 0: #delay if last message was a single-trigger message
					MSG_CODE = 0
					LAST_MSG_TIME = None

			#update player
			(DX,DY, MSG_CODE) = physics.updatePlayer(player, STAGE, DX, DY, block_s, blocks_per_window, MSG_CODE)

			#update/remove entities
			removed = set()
			for ent in STAGE.entities:
				if type(ent) == entity.Bomb:
					MSG_CODE = max(MSG_CODE, 2) #take cover!
				if ent.state == -1:
					removed.add(ent)
				else:
					ent.update(TIMEPASSED, STAGE, player)
			for ent in removed:
				STAGE.entities.discard(ent)
			
			#remove spikes without floor / kill player and snakes if touching
			removed = set()
			for spike in STAGE.spikes:
				if spike.checkRemove(STAGE): removed.add(spike)
				if player.rect.colliderect(spike.rect) and player.rect.bottom == spike.rect.bottom and not player.demoMode:
					player.dead = True
				for ent in STAGE.entities:
					if type(ent) == entity.Snake:
						if ent.rect.colliderect(spike.rect) and ent.rect.bottom >= spike.rect.centery:
							ent.state = -1
							player.killedSnakes += 1
			for spike in removed:
				STAGE.stage.discard(spike)
				STAGE.spikes.discard(spike)

			#CHECK DIE
			if player.dead:
				pygame.time.wait(500)
				endScreen(TIMEPASSED, player.treasures, player.killedSnakes, True)

			#CHECK WIN (temporary)
			for block in STAGE.exitBlocks:
				if player.rect.colliderect(block.rect): 
					endScreen(TIMEPASSED, player.treasures, player.killedSnakes)

			#EVENT LOOP / CONTROLS
			for event in pygame.event.get(): 
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				
				if event.type == KEYDOWN:
					if event.key == K_LEFT:
						player.moveLeft = True
					if event.key == K_RIGHT:
						player.moveRight = True
					if event.key == K_UP:
						touchingRope = False
						touchedRope = None
						for block in player.getCollidedBlocks(STAGE):
							if isinstance(block, world.Rope):
								touchingRope = True
								touchedRope = block
								player.isClimb = True
						if player.isClimb:
							STAGE.scroll(touchedRope.rect.centerx-player.rect.centerx, 0)
							player.ducked = False
							player.touchedBlocks['bottom'] = None
							player.yVel = -1*player.jumpSpd
						elif player.jumps > 0:
							player.jumps -= 1
							player.ducked = False
							player.touchedBlocks['bottom'] = None
							player.yVel = -1*player.jumpSpd

					if event.key == K_DOWN:
						touchingRope = False
						touchedRope = None
						for block in player.getCollidedBlocks(STAGE):
							if isinstance(block, world.Rope):
								touchingRope = True
								touchedRope = block
								player.isClimb = True
						if player.isClimb:
							STAGE.scroll(touchedRope.rect.centerx-player.rect.centerx, 0)
							player.ducked = False
							player.yVel = player.jumpSpd
						elif player.jumps > 0:
							player.ducked = not player.ducked
					
					if event.key == K_r:
						MSG_CODE = player.placeRope(STAGE, MSG_CODE)

					if event.key == K_t:
						temp = player.torches
						player.torches = player.torches2
						player.torches2 = temp
					
					if event.key == K_f:
						MSG_CODE = player.placeFlare(STAGE, MSG_CODE)
					
					if event.key == K_g:
						MSG_CODE = player.collect(STAGE, MSG_CODE)
					
					if event.key == K_b:
						MSG_CODE = player.placeBomb(STAGE, TIMEPASSED, MSG_CODE)
					
					if event.key == K_d: #demo mode
						player.demoMode = not player.demoMode
					
					if event.key == K_s:
						sandbox_block_s = block_s
						STAGE.entities = set() #so snakes don't teleport
						SANDBOXMODE = True
					
					if event.key == K_SPACE:
						SCROLLMODE = True
					
					if event.key == K_h:
						helpScreen()

					if event.key == K_RETURN and player.demoMode:
						endScreen(TIMEPASSED, player.treasures, player.killedSnakes)

				if event.type == KEYUP:
					if event.key == K_LEFT:
						player.moveLeft = False
					if event.key == K_RIGHT:
						player.moveRight = False
					if event.key == K_UP:
						if player.yVel < 0:
							if player.isClimb:
								player.yVel = 0
							else:
								player.yVel //= 2
					if event.key == K_DOWN:
						if player.isClimb and player.yVel > 0:
							player.yVel = 0
				
				if event.type == pygame.MOUSEBUTTONDOWN:
					DARK = not DARK

				if DARK:
					if event.type == EXPIRETORCH:
						if player.torches != []:
							player.torches[-1].expire()
					
		redrawGameWindow()
		clock.tick(60) #100ms, approx.

startScreen()
runGame()