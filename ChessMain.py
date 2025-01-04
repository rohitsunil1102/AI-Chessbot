
# main driver file
# used to handle user input
# displays the current gamestate object.

import pygame as p 
import ChessEngine, SmartMoveFinder
WIDTH = HEIGHT = 512
DIMENSION = 8 # 8 x 8 board
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


# initialize a global dict of images. called only once in the main

def loadImages():
    pieces = ["wp","wR","wN","wB","wK","wQ","bp","bR","bN","bB","bK","bQ"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/"+piece+".png"),(SQ_SIZE,SQ_SIZE))
    # image can be accesed by calling from IMAGES dict

#The main driver
#will ahndle user input and updating graphics

def main():
    p.init()
    screen = p.display.set_mode((WIDTH,HEIGHT + 100))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves() 
    moveMade = False # flag variable for when a move is made
    animate = False # flag variable for animations
    loadImages() #only once befor while loop
    running = True
    gameOver = False
    sqSelected = () # no square initially selected (row,col)
    playerClicks = [] # keeps track of player clicks (2 tuples)
    playerOne = True # If a human is playing white -> True
    playerTwo = False # same concept for black
    currentScore = 0
    font = p.font.SysFont("Arial", 24, True, False)
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handlers
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos() # (x,y) position of the mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col): # same square selected
                        sqSelected = ()
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected) # append both first and second clicks
                    if len(playerClicks) == 2: # after second click
                        move = ChessEngine.Move(playerClicks[0],playerClicks[1],gs.board)
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                print(move.getChessNotation())
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # undo a move
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                if e.key == p.K_r:
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
            # AI move finder logic:
            if not gameOver and not humanTurn:
                AIMove, currentScore = SmartMoveFinder.findBestMove(gs, validMoves)
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True


            if moveMade:
                if animate:
                    animateMoves(gs.moveLog[-1], screen, gs.board, clock)
                validMoves = gs.getValidMoves()
                moveMade = False
                animate = False


        drawGameState(screen, gs, validMoves, sqSelected)

        # display the score
        screen.fill(p.Color("white"), p.Rect(0, HEIGHT, WIDTH, 100))  # Clear the bottom area
        scoreText = font.render(f"Score: {currentScore}", True, p.Color("Black"))
        screen.blit(scoreText, (10, HEIGHT + 10))

        # Draw evaluation bar
        evalBarHeight = 20
        evalBarWidth = WIDTH
        evalBarTop = HEIGHT + 50
        whiteEval = int((currentScore + 10) / 20 * evalBarWidth)  # Normalize score to fit eval bar
        p.draw.rect(screen, p.Color("white"), p.Rect(0, evalBarTop, whiteEval, evalBarHeight))
        p.draw.rect(screen, p.Color("black"), p.Rect(whiteEval, evalBarTop, evalBarWidth - whiteEval, evalBarHeight))
        p.draw.rect(screen, p.Color("gray"), p.Rect(0, evalBarTop, evalBarWidth, evalBarHeight), 1)  # Border


        if gs.checkMate:
            gameOver = True
            if gs.whiteToMove:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(p.Color("red"))
                screen.blit(s,(SQ_SIZE*gs.whiteKingLocation[1],SQ_SIZE*gs.whiteKingLocation[0]))
            else:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(p.Color("red"))
                screen.blit(s,(SQ_SIZE*gs.blackKingLocation[1],SQ_SIZE*gs.blackKingLocation[0]))
        if gs.staleMate:
            gameOver = True
            if gs.whiteToMove:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(p.Color("orange"))
                screen.blit(s,(SQ_SIZE*gs.whiteKingLocation[1],SQ_SIZE*gs.whiteKingLocation[0]))
            else:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(p.Color("orange"))
                screen.blit(s,(SQ_SIZE*gs.blackKingLocation[1],SQ_SIZE*gs.blackKingLocation[0]))
        clock.tick(MAX_FPS)
        p.display.flip()
#drawGameState() -> responsible for all the graphics in the current game state

# highlight square selected and moves for the selected piece
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"): #sqSelected is a piece that can be moved
            # highlight the selected square
            s = p.Surface((SQ_SIZE,SQ_SIZE))
            s.set_alpha(100) # 0 - 255(opaque)
            s.fill(p.Color("blue"))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color("yellow"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s,(SQ_SIZE*move.endCol, SQ_SIZE*move.endRow))


def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen) #draw squares on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen,gs.board) #draw pieces on the squares of the board

def drawBoard(screen):
    global colors
    colors = [p.Color("white"),p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen,color,p.Rect(c*SQ_SIZE,r*SQ_SIZE,SQ_SIZE,SQ_SIZE))

def drawPieces(screen,board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece],p.Rect(c*SQ_SIZE,r*SQ_SIZE,SQ_SIZE,SQ_SIZE))

# animation of pieces and moves

def animateMoves(move, screen, board, clock):
    global colors
    coords = [] # list of columns
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesforSquare = 10 # frames per square
    frameCount = (abs(dR) + abs(dC))*framesforSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase piece moved from ending square
        color = colors[(move.endRow + move.endCol)%2]
        endSquare = p.Rect(move.endCol*SQ_SIZE,move.endRow*SQ_SIZE,SQ_SIZE,SQ_SIZE)
        p.draw.rect(screen,color,endSquare)
        # draw captured piece onto square
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw the moving piece
        screen.blit(IMAGES[move.pieceMove], p.Rect(c*SQ_SIZE,r*SQ_SIZE,SQ_SIZE,SQ_SIZE))
        p.display.flip()
        clock.tick(120)

if __name__ == "__main__":
    main()
