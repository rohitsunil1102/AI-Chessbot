
# main driver file
# used to handle user input
# displays the current gamestate object.

import pygame as p
import ChessEngine, SmartMoveFinder
from StockfishEngine import StockfishEngine
WIDTH = HEIGHT = 512
DIMENSION = 8 # 8 x 8 board
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
BOARD_LEFT = 24
BOARD_TOP = 24
WINDOW_WIDTH = WIDTH + BOARD_LEFT * 2
STATUS_TOP = HEIGHT + BOARD_TOP * 2
NAVY = (8, 17, 38)
PANEL = (16, 31, 59)
CARD = (21, 42, 78)
CARD_HOVER = (29, 57, 101)
CARD_BORDER = (49, 82, 132)
WHITE_TEXT = (240, 246, 255)
MUTED_TEXT = (163, 183, 211)
ACCENT = (93, 207, 222)
LIGHT_SQUARE = (190, 211, 237)
DARK_SQUARE = (25, 54, 100)


# initialize a global dict of images. called only once in the main

def loadImages():
    pieces = ["wp","wR","wN","wB","wK","wQ","bp","bR","bN","bB","bK","bQ"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/"+piece+".png"),(SQ_SIZE,SQ_SIZE))
    # image can be accesed by calling from IMAGES dict


def chooseMode(screen, clock, font):
    titleFont = p.font.SysFont("Bahnschrift", 40, True)
    subtitleFont = p.font.SysFont("Segoe UI", 17)
    switchFont = p.font.SysFont("Segoe UI", 19, True)
    detailFont = p.font.SysFont("Segoe UI", 16)
    smallFont = p.font.SysFont("Bahnschrift", 14, True)
    art = loadSelectionArt()
    mode = "beginner"
    switchRect = p.Rect(56, 290, WINDOW_WIDTH - 112, 68)
    playRect = p.Rect(WINDOW_WIDTH // 2 - 105, 424, 210, 56)
    while True:
        screen.fill(NAVY)
        p.draw.rect(screen, PANEL, p.Rect(0, 0, WINDOW_WIDTH, 12))
        p.draw.rect(screen, ACCENT, p.Rect(0, 0, 118, 12))
        screen.blit(art, art.get_rect(center=(WINDOW_WIDTH // 2, 365)))
        kicker = smallFont.render("AI-Chessbot", True, ACCENT)
        title = titleFont.render("Choose your opponent", True, WHITE_TEXT)
        subtitle = subtitleFont.render("Pick a mode to start a new game", True, MUTED_TEXT)
        screen.blit(kicker, kicker.get_rect(center=(WINDOW_WIDTH // 2, 130)))
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 174)))
        screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 212)))
        mouse = p.mouse.get_pos()
        p.draw.rect(screen, PANEL, switchRect, border_radius=17)
        halfWidth = switchRect.width // 2
        activeRect = p.Rect(
            switchRect.x + (halfWidth if mode == "stockfish" else 0) + 5,
            switchRect.y + 5, halfWidth - 10, switchRect.height - 10,
        )
        p.draw.rect(screen, ACCENT if mode == "beginner" else CARD_HOVER, activeRect, border_radius=13)
        p.draw.rect(screen, CARD_BORDER, switchRect, 2, border_radius=17)
        beginnerColor = NAVY if mode == "beginner" else MUTED_TEXT
        stockfishColor = WHITE_TEXT if mode == "stockfish" else MUTED_TEXT
        beginnerLabel = switchFont.render("Beginner", True, beginnerColor)
        stockfishLabel = switchFont.render("Stockfish", True, stockfishColor)
        screen.blit(beginnerLabel, beginnerLabel.get_rect(center=(switchRect.x + halfWidth // 2, switchRect.centery)))
        screen.blit(stockfishLabel, stockfishLabel.get_rect(center=(switchRect.x + halfWidth + halfWidth // 2, switchRect.centery)))

        detail = "Depth 2 material search" if mode == "beginner" else "Powered by the Stockfish chess engine"
        detailText = detailFont.render(detail, True, MUTED_TEXT)
        screen.blit(detailText, detailText.get_rect(center=(WINDOW_WIDTH // 2, 390)))
        playHover = playRect.collidepoint(mouse)
        p.draw.rect(screen, ACCENT if playHover else CARD_HOVER, playRect, border_radius=12)
        playLabel = switchFont.render("Start game", True, NAVY)
        screen.blit(playLabel, playLabel.get_rect(center=playRect.center))
        footer = smallFont.render("Click the switch or use Left / Right, then press Enter", True, MUTED_TEXT)
        screen.blit(footer, footer.get_rect(center=(WINDOW_WIDTH // 2, 520)))
        p.display.flip()
        for event in p.event.get():
            if event.type == p.QUIT:
                return None
            if event.type == p.KEYDOWN:
                if event.key in (p.K_LEFT, p.K_1, p.K_KP1):
                    mode = "beginner"
                elif event.key in (p.K_RIGHT, p.K_2, p.K_KP2):
                    mode = "stockfish"
                elif event.key in (p.K_RETURN, p.K_SPACE):
                    return mode
            if event.type == p.MOUSEBUTTONDOWN:
                if switchRect.collidepoint(event.pos):
                    mode = "stockfish" if mode == "beginner" else "beginner"
                elif playRect.collidepoint(event.pos):
                    return mode
        clock.tick(MAX_FPS)


def loadSelectionArt():
    source = p.image.load("pieces.jpg").convert()
    image = p.transform.smoothscale(source, (560, 600))
    art = p.Surface(image.get_size(), p.SRCALPHA)
    for y in range(image.get_height()):
        for x in range(image.get_width()):
            red, green, blue, _ = image.get_at((x, y))
            brightness = (red + green + blue) // 3
            alpha = max(0, min(82, int((235 - brightness) * 0.38)))
            art.set_at((x, y), (112, 155, 204, alpha))
    return art


def moveToUci(move):
    files = "abcdefgh"
    promotion = "q" if move.isPawnPromotion else ""
    return (files[move.startCol] + str(8 - move.startRow) +
            files[move.endCol] + str(8 - move.endRow) + promotion)


def uciToMove(uci, validMoves):
    for move in validMoves:
        if moveToUci(move) == uci:
            return move
    return None

#The main driver
#will ahndle user input and updating graphics

def main():
    p.init()
    screen = p.display.set_mode((WINDOW_WIDTH, STATUS_TOP + 100))
    clock = p.time.Clock()
    screen.fill(NAVY)
    loadImages() #only once befor while loop
    font = p.font.SysFont("Segoe UI", 24, True, False)
    mode = chooseMode(screen, clock, font)
    if mode is None:
        p.quit()
        return
    engine = None
    if mode == "stockfish":
        try:
            engine = StockfishEngine()
        except (OSError, RuntimeError) as exc:
            screen.fill(NAVY)
            message = font.render("Stockfish unavailable: " + str(exc)[:55], True, WHITE_TEXT)
            hint = font.render("Press any key to return to mode selection", True, MUTED_TEXT)
            screen.blit(message, message.get_rect(center=(WINDOW_WIDTH // 2, 270)))
            screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 320)))
            p.display.flip()
            waiting = True
            while waiting:
                for event in p.event.get():
                    if event.type == p.QUIT:
                        p.quit()
                        return
                    if event.type == p.KEYDOWN or event.type == p.MOUSEBUTTONDOWN:
                        waiting = False
                clock.tick(MAX_FPS)
            main()
            return
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves() 
    moveMade = False # flag variable for when a move is made
    animate = False # flag variable for animations
    running = True
    gameOver = False
    sqSelected = () # no square initially selected (row,col)
    playerClicks = [] # keeps track of player clicks (2 tuples)
    playerOne = True # If a human is playing white -> True
    playerTwo = False # same concept for black
    currentScore = 0
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handlers
            elif e.type == p.MOUSEBUTTONDOWN:
                humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos() # (x,y) position of the mouse
                    col = (location[0] - BOARD_LEFT)//SQ_SIZE
                    row = (location[1] - BOARD_TOP)//SQ_SIZE
                    if not (0 <= col < DIMENSION and 0 <= row < DIMENSION):
                        continue
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
            if moveMade:
                if animate:
                    animateMoves(gs.moveLog[-1], screen, gs.board, clock)
                validMoves = gs.getValidMoves()
                moveMade = False
                animate = False

        # Decide from the live board state, once per frame after processing events.
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        if running and not gameOver and not humanTurn and validMoves:
            if mode == "beginner":
                AIMove, currentScore = SmartMoveFinder.findBestMoveMinMax(gs, validMoves)
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
            else:
                uciMoves = [moveToUci(move) for move in gs.moveLog]
                bestUci = engine.best_move(uciMoves)
                currentScore = engine.score_white_pawns(gs.whiteToMove)
                AIMove = uciToMove(bestUci, validMoves) if bestUci else None

            if AIMove is not None:
                gs.makeMove(AIMove)
                animateMoves(gs.moveLog[-1], screen, gs.board, clock)
                validMoves = gs.getValidMoves()


        drawGameState(screen, gs, validMoves, sqSelected)

        # display the score
        screen.fill(NAVY, p.Rect(0, STATUS_TOP, WINDOW_WIDTH, 100))  # Clear the bottom area
        modeText = "Beginner / Depth 2" if mode == "beginner" else "Stockfish"
        scoreLabel = f"{currentScore:+.1f}" if mode == "stockfish" else str(currentScore)
        scoreText = font.render(f"{modeText}   Score: {scoreLabel}", True, WHITE_TEXT)
        screen.blit(scoreText, (10, STATUS_TOP + 10))

        # Draw evaluation bar
        evalBarHeight = 20
        evalBarWidth = WIDTH
        evalBarTop = STATUS_TOP + 50
        whiteEval = max(0, min(evalBarWidth, int((currentScore + 10) / 20 * evalBarWidth)))
        p.draw.rect(screen, LIGHT_SQUARE, p.Rect(BOARD_LEFT, evalBarTop, whiteEval, evalBarHeight))
        p.draw.rect(screen, DARK_SQUARE, p.Rect(BOARD_LEFT + whiteEval, evalBarTop, evalBarWidth - whiteEval, evalBarHeight))
        p.draw.rect(screen, CARD_BORDER, p.Rect(BOARD_LEFT, evalBarTop, evalBarWidth, evalBarHeight), 1)  # Border


        if gs.checkMate:
            gameOver = True
            if gs.whiteToMove:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(ACCENT)
                screen.blit(s,(BOARD_LEFT + SQ_SIZE*gs.whiteKingLocation[1],BOARD_TOP + SQ_SIZE*gs.whiteKingLocation[0]))
            else:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(ACCENT)
                screen.blit(s,(BOARD_LEFT + SQ_SIZE*gs.blackKingLocation[1],BOARD_TOP + SQ_SIZE*gs.blackKingLocation[0]))
        if gs.staleMate:
            gameOver = True
            if gs.whiteToMove:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(ACCENT)
                screen.blit(s,(BOARD_LEFT + SQ_SIZE*gs.whiteKingLocation[1],BOARD_TOP + SQ_SIZE*gs.whiteKingLocation[0]))
            else:
                s = p.Surface((SQ_SIZE,SQ_SIZE))
                s.set_alpha(100)
                s.fill(ACCENT)
                screen.blit(s,(BOARD_LEFT + SQ_SIZE*gs.blackKingLocation[1],BOARD_TOP + SQ_SIZE*gs.blackKingLocation[0]))
        clock.tick(MAX_FPS)
        p.display.flip()
    if engine:
        engine.close()
    p.quit()
#drawGameState() -> responsible for all the graphics in the current game state

# highlight square selected and moves for the selected piece
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"): #sqSelected is a piece that can be moved
            # highlight the selected square
            s = p.Surface((SQ_SIZE,SQ_SIZE))
            s.set_alpha(100) # 0 - 255(opaque)
            s.fill(ACCENT)
            screen.blit(s, (BOARD_LEFT + c*SQ_SIZE, BOARD_TOP + r*SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color((255, 207, 91)))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s,(BOARD_LEFT + SQ_SIZE*move.endCol, BOARD_TOP + SQ_SIZE*move.endRow))


def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen) #draw squares on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen,gs.board) #draw pieces on the squares of the board

def drawBoard(screen):
    global colors
    # Keep the status panel and evaluation bar visible during move animation.
    screen.fill(NAVY, p.Rect(0, 0, WINDOW_WIDTH, STATUS_TOP))
    colors = [LIGHT_SQUARE, DARK_SQUARE]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen,color,p.Rect(BOARD_LEFT + c*SQ_SIZE,BOARD_TOP + r*SQ_SIZE,SQ_SIZE,SQ_SIZE))
    labelFont = p.font.SysFont("Bahnschrift", 14, True, False)
    for r in range(DIMENSION):
        labelRect = p.Rect(2, BOARD_TOP + r*SQ_SIZE + SQ_SIZE//2 - 10, BOARD_LEFT - 4, 20)
        p.draw.rect(screen, PANEL, labelRect, border_radius=5)
        number = labelFont.render(str(8-r), True, ACCENT)
        screen.blit(number, number.get_rect(center=labelRect.center))
    for c, fileName in enumerate("abcdefgh"):
        labelRect = p.Rect(BOARD_LEFT + c*SQ_SIZE + SQ_SIZE//2 - 10, HEIGHT + BOARD_TOP + 2, 20, BOARD_TOP - 4)
        p.draw.rect(screen, PANEL, labelRect, border_radius=5)
        letter = labelFont.render(fileName, True, ACCENT)
        screen.blit(letter, letter.get_rect(center=labelRect.center))

def drawPieces(screen,board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece],p.Rect(BOARD_LEFT + c*SQ_SIZE,BOARD_TOP + r*SQ_SIZE,SQ_SIZE,SQ_SIZE))

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
        endSquare = p.Rect(BOARD_LEFT + move.endCol*SQ_SIZE,BOARD_TOP + move.endRow*SQ_SIZE,SQ_SIZE,SQ_SIZE)
        p.draw.rect(screen,color,endSquare)
        # draw captured piece onto square
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw the moving piece
        screen.blit(IMAGES[move.pieceMove], p.Rect(BOARD_LEFT + c*SQ_SIZE,BOARD_TOP + r*SQ_SIZE,SQ_SIZE,SQ_SIZE))
        p.display.flip()
        clock.tick(120)

if __name__ == "__main__":
    main()
