##STORES LENGTHY TEXT/IMAGE BLITTING CODE TO KEEP OTHER FILES CLEANER##

import pygame
from pygame.locals import *

smallText = pygame.font.Font(None, 30)
largeText = pygame.font.Font(None,120)

def loadText(text, font, color=(255,153,51)):
	textSurface = font.render(text, True, color)
	return (textSurface, textSurface.get_rect())

def drawStartMsg(window, screen_width, screen_height):
    textSurface, textRect = loadText("Click to start" ,smallText)
    textRect.center = ((screen_width//2),(screen_height*9//10))
    window.blit(textSurface, textRect)

def drawEndMsg(window, screen_width, screen_height, SCORE, displayScore, treasures, snakesKilled, bonuses, bonus, died):
    if died:
        textSurface = largeText.render('YOU DIED!!', True, (255,153,51))
        textRect = textSurface.get_rect()
        textRect.center = ((screen_width//2),(screen_height*1//6))
        window.blit(textSurface, textRect)

    textSurface = largeText.render(f'SCORE: {displayScore}', True, (255,153,51))
    textRect = textSurface.get_rect()
    textRect.center = ((screen_width//2),(screen_height//3))
    window.blit(textSurface, textRect)

    if SCORE - displayScore < 50 and SCORE - displayScore > 0:
        displayScore += 10
    elif displayScore < SCORE:
        displayScore += 50
    elif bonuses > 0:
        displayScore += bonus
        bonuses -= 1 #bonuses is changed while treasures and snakesKilled aren't
        smallText = pygame.font.Font(None,50)
        textSurface = smallText.render('BONUS!', True, (255,153,51))
        textRect = textSurface.get_rect()
        textRect.center = ((screen_width//2),(screen_height*3//4))
        window.blit(textSurface, textRect)
        pygame.time.delay(500)
    else:
        smallText = pygame.font.Font(None,50)
        textSurface = smallText.render(f'Treasures collected: {treasures}', True, (255,153,51))
        textRect = textSurface.get_rect()
        textRect.center = ((screen_width//2),(screen_height*5//8))
        window.blit(textSurface, textRect)
        textSurface = smallText.render(f'Snakes killed: {snakesKilled}', True, (255,153,51))
        textRect = textSurface.get_rect()
        textRect.center = ((screen_width//2),(screen_height*6//8))
        window.blit(textSurface, textRect)
        textSurface = smallText.render('Click to play again', True, (255,153,51))
        textRect = textSurface.get_rect()
        textRect.center = ((screen_width//2),(screen_height*7//8))
        window.blit(textSurface, textRect)
    
    return (displayScore, bonuses)

#load outside of function to reduce lag
block_s = 45
iconBackground = pygame.transform.scale(pygame.image.load('white.png'), (block_s, block_s))
torchImg = pygame.transform.scale(pygame.image.load('torch.png'), (block_s, block_s))
flareImg = pygame.transform.scale(pygame.image.load('flare.png'), (block_s, block_s))
bombImg = pygame.transform.scale(pygame.image.load('bomb.png'), (block_s, block_s))
swordImg = pygame.transform.scale(pygame.image.load('sword.png'), (int(320/613*block_s), block_s))
swordShift = int((1-(320/613))*block_s/2)
shovelImg = pygame.transform.scale(pygame.image.load('shovel.png'), (block_s, block_s))
treasureImg = pygame.transform.scale(pygame.image.load('treasure.png'), (block_s, block_s))

def icons(player, block_s=45): #returns image
    #only load these images once, unless block size changes
    totalImage = pygame.Surface((block_s*11, block_s), pygame.SRCALPHA)
    torches, flares, bombs, swords, hasShovel, treasures = len(player.torches), player.flares, player.bombs, player.swords, player.shovel, player.treasures
    x = 0
    if torches > 0:
        totalImage.blit(iconBackground, (x,0))
        totalImage.blit(torchImg, (x,0))
        x += block_s
        totalImage.blit(iconBackground, (x,0))
        num = pygame.transform.scale(loadText(str(torches), largeText, (0,0,0))[0], (block_s, block_s))
        totalImage.blit(num, (x, 0))
        x += block_s
    if flares > 0:
        totalImage.blit(iconBackground, (x,0))
        totalImage.blit(flareImg, (x,0))
        x += block_s
        totalImage.blit(iconBackground, (x,0))
        num = pygame.transform.scale(loadText(str(flares), largeText, (0,0,0))[0], (block_s, block_s))
        totalImage.blit(num, (x, 0))
        x += block_s
    if bombs > 0:
        totalImage.blit(iconBackground, (x,0))
        totalImage.blit(bombImg, (x,0))
        x += block_s
        totalImage.blit(iconBackground, (x,0))
        num = pygame.transform.scale(loadText(str(bombs), largeText, (0,0,0))[0], (block_s, block_s))
        totalImage.blit(num, (x, 0))
        x += block_s
    if swords > 0:
        totalImage.blit(iconBackground, (x,0))
        totalImage.blit(swordImg, (x+swordShift,0))
        x += block_s
        totalImage.blit(iconBackground, (x,0))
        num = pygame.transform.scale(loadText(str(swords), largeText, (0,0,0))[0], (block_s, block_s))
        totalImage.blit(num, (x, 0))
        x += block_s
    if hasShovel:
        totalImage.blit(iconBackground, (x,0))
        totalImage.blit(shovelImg, (x,0))
        x += block_s
    if treasures > 0:
        totalImage.blit(iconBackground, (x,0))
        totalImage.blit(treasureImg, (x,0))
        x += block_s
        totalImage.blit(iconBackground, (x,0))
        num = pygame.transform.scale(loadText(str(treasures), largeText, (0,0,0))[0], (block_s, block_s))
        totalImage.blit(num, (x, 0))
        x += block_s
    
    return totalImage

msg0 = pygame.transform.scale(loadText("Press 'H' for help!", largeText,(255,255,255))[0], (block_s*7, block_s))
msg1 = pygame.transform.scale(loadText("Crouch with down arrow to hide!", largeText,(255,255,255))[0], (block_s*7, block_s))
msg2 = pygame.transform.scale(loadText("TAKE COVER!", largeText,(255,255,255))[0], (block_s*7, block_s))
msg3 = pygame.transform.scale(loadText("Stand on the ground!", largeText,(255,255,255))[0], (block_s*7, block_s))
msg4 = pygame.transform.scale(loadText("Need a shovel!", largeText,(255,255,255))[0], (block_s*7, block_s))
msg5 = pygame.transform.scale(loadText("Stand up!", largeText,(255,255,255))[0], (block_s*7, block_s))
msg6 = pygame.transform.scale(loadText("No more of this item!", largeText,(255,255,255))[0], (block_s*7, block_s))
demoMsg1 = pygame.transform.scale(loadText("DEMO MODE", largeText,(255,255,255))[0], (block_s*5, block_s))
modeMsg1 = pygame.transform.scale(loadText("PAUSED", largeText,(255,255,255))[0], (block_s*5, block_s))
modeMsg2 = pygame.transform.scale(loadText("SANDBOX MODE", largeText,(255,255,255))[0], (block_s*5, block_s))
        
def drawGameMsg(window, msgCode, block_s=45):
    msgBackground = pygame.transform.scale(pygame.image.load('black.png'), (block_s*7, block_s))
    if msgCode == 0: msgBackground.blit(msg0, (0,0)) #these messages have priority. ex: 5 overrides 3. 
    elif msgCode == 1: msgBackground.blit(msg1, (0,0)) #also all msgs 3+ override 0-2 and stay for a delayed period
    elif msgCode == 2: msgBackground.blit(msg2, (0,0))
    elif msgCode == 3: msgBackground.blit(msg3, (0,0))
    elif msgCode == 4: msgBackground.blit(msg4, (0,0))
    elif msgCode == 5: msgBackground.blit(msg5, (0,0))
    elif msgCode == 6: msgBackground.blit(msg6, (0,0))
    window.blit(msgBackground, (window.get_width()-(block_s*7), 0))

def drawDemoMsg(window, block_s=45):
    msgBackground = pygame.transform.scale(pygame.image.load('black.png'), (block_s*5, block_s))
    msgBackground.blit(demoMsg1, (0,0))
    window.blit(msgBackground, (window.get_width()-(block_s*5), window.get_height()-block_s))

def drawModeMsg(window, msgCode, block_s=45):
    msgBackground = pygame.transform.scale(pygame.image.load('black.png'), (block_s*5, block_s))
    if msgCode == 1: msgBackground.blit(modeMsg1, (0,0))
    elif msgCode == 2: msgBackground.blit(modeMsg2, (0,0))
    window.blit(msgBackground, (0, window.get_height()-block_s))

