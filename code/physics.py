##CONTAINS PLAYER PHYSICS UPDATE TO KEEP ENTITY AND MAIN CLEANER##
#Also see: entity.Player.getCollidedSides() and entity.Player.getTouchedBlocks()
#Snake version of this function is in Snake class (.update())
import world
import entity

def updatePlayer(player, STAGE, DX, DY, block_s, blocks_per_window, MSG_CODE):

    #left and right velocity and change direction / climb
    if player.moveLeft:
        player.xVel = -1*player.xSpd
        player.faceLeft = True
        player.isClimb = False
    elif player.moveRight:
        player.xVel = player.xSpd
        player.faceLeft = False
        player.isClimb = False
    else:
        player.xVel = 0
    
    #ensure player only climbs on rope
    if player.isClimb:
        touchingRope = False
        for block in player.getCollidedBlocks(STAGE):
            if isinstance(block, world.Rope):
                touchingRope = True
        if not touchingRope: player.isClimb = False

    #top collision momentum halting
    if player.collidedSides['top']:
        player.yVel //= 2

    #gravity
    if not (player.touchedBlocks['bottom'] != None or player.isClimb):
        player.yVel += player.gravity
    
    #scroll so player can view stage better when moving against terrain
    viewScrollVel = block_s//9
    scrollBackVel = block_s//2
    botBlock = player.touchedBlocks['bottom']
    snakesNear = False
    for ent in STAGE.entities:
        if type(ent) == entity.Snake and abs(ent.rect.centerx - player.rect.centerx) <= 225 and abs(ent.rect.centery - player.rect.centery) <= 150:
            snakesNear = True #prevents scrolling when ducking has to be used to avoid snakes
            MSG_CODE = max(MSG_CODE, 1) #send back snake msg
    if (player.action == 'duck' or player.action == 'crawl') and not snakesNear: 
        if DY < block_s*(blocks_per_window//6):
            player.scroll(0, viewScrollVel)
            STAGE.scroll(0, viewScrollVel)
            DY += viewScrollVel
    elif player.collidedSides['right'] and botBlock != None and not botBlock.transparent:
        if DX < block_s*(blocks_per_window//6):
            player.scroll(viewScrollVel,0)
            STAGE.scroll(viewScrollVel,0)
            DX += viewScrollVel
    elif player.collidedSides['left'] and botBlock != None and not botBlock.transparent:
        if DX > -1*block_s*(blocks_per_window//6):
            player.scroll(-1*viewScrollVel,0)
            STAGE.scroll(-1*viewScrollVel,0)
            DX -= viewScrollVel
    elif DY != 0:
        if abs(DY) < scrollBackVel: scrollBackVel = DY * -1
        elif DY > 0: scrollBackVel *= -1
        player.scroll(0,scrollBackVel)
        STAGE.scroll(0,scrollBackVel)
        DY += scrollBackVel
    elif DX != 0:
        if abs(DX) < scrollBackVel: scrollBackVel = DX * -1
        elif DX > 0: scrollBackVel *= -1
        player.scroll(scrollBackVel, 0)
        STAGE.scroll(scrollBackVel, 0)
        DX += scrollBackVel
    
    #actually move (taking stage collision into account) 
    player.move(STAGE, player.xVel, player.yVel)

    #change actions
    if player.yVel > 10:
        player.ducked = False

    if player.isClimb:
        if player.yVel == 0:
            player.action = 'hang'
        else:
            player.action = 'climb'
    elif player.yVel < 0:
        player.action = 'jump'
    elif player.ducked:
        if player.xVel != 0:
            player.action = 'crawl'
        else:
            player.action = 'duck'
    else:
        if player.yVel > 1: #yVel swaps between 0 and 1 when on platform
            player.action = 'fall'
        elif player.xVel != 0:
            player.action = 'run'
        else:
            player.action = 'stop'

    #actually change actions (animate)
    player.setAction()

    return (DX,DY, MSG_CODE)