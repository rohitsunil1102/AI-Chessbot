
class GameState():
    def __init__(self):
        # 8 by 8 board -> 2-D list
        # each element has 2 characters (colour and piece)
        self.board = [
            ["bR","bN","bB","bQ","bK","bB","bN","bR"],
            ["bp","bp","bp","bp","bp","bp","bp","bp"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["wp","wp","wp","wp","wp","wp","wp","wp"],
            ["wR","wN","wB","wQ","wK","wB","wN","wR"],
        ]
        self.moveFunctions = {"p":self.getPawnMoves,"R":self.getRookMoves,"N":self.getKnightMoves,"B":self.getBishopMoves,"K":self.getKingMoves,"Q":self.getQueenMoves,}
        self.whiteToMove = True
        self.moveLog = []
        self.enpassantPossibleLog = [()]
        self.whiteKingLocation = (7,4)
        self.blackKingLocation = (0,4)
        self.checkMate = False
        self.staleMate = False
        self.enpassantPossible = ()
        self.currentCastleRights = CastleRights(True,True,True,True)
        self.castleRightsLog = [CastleRights(self.currentCastleRights.wks,self.currentCastleRights.bks,self.currentCastleRights.wqs,self.currentCastleRights.bqs)]
    
    def makeMove(self, move):
        self.enpassantPossibleLog.append(self.enpassantPossible)
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMove
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove
        if move.pieceMove == "wK":
            self.whiteKingLocation = (move.endRow,move.endCol)
        elif move.pieceMove == "bK":
            self.blackKingLocation = (move.endRow,move.endCol)
        # pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMove[0] + "Q"

        # en-passant move
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--"
        if move.pieceMove[1] == "p" and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow)//2, move.endCol)
        else:
            self.enpassantPossible = ()
        
        # Move the rook as part of castling.
        if move.isCastleMove:
            if move.endCol - move.startCol == 2: # king side castle
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1] 
                self.board[move.endRow][move.endCol + 1] = "--"
            
            else: # queen side castle
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]
                self.board[move.endRow][move.endCol - 2] = "--"
        # update the castling rights whenever there is a rook or king move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastleRights.wks,self.currentCastleRights.bks,self.currentCastleRights.wqs,self.currentCastleRights.bqs))


    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0],self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0],self.blackKingLocation[1])
    def squareUnderAttack(self,r,c):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves()
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                self.whiteToMove = not self.whiteToMove
                return True
        self.whiteToMove = not self.whiteToMove
        return False
    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMove
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove
            if move.pieceMove == "wK":
                self.whiteKingLocation = (move.startRow,move.startCol)
            elif move.pieceMove == "bK":
                self.blackKingLocation = (move.startRow,move.startCol)
            # undo en-passant move
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = "--"
                self.board[move.startRow][move.endCol] = move.pieceCaptured
            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]

            # undo castling rights
            self.castleRightsLog.pop()
            previousCastleRights = self.castleRightsLog[-1]
            # Keep the history entry immutable while future moves update rights.
            self.currentCastleRights = CastleRights(
                previousCastleRights.wks,
                previousCastleRights.bks,
                previousCastleRights.wqs,
                previousCastleRights.bqs,
            )


            # undo the castle moves
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: # king side
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else: # queen side
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"
            self.checkMate = False
            self.staleMate = False   

    def updateCastleRights(self, move):
        if move.pieceMove == "wK":
            self.currentCastleRights.wks = False
            self.currentCastleRights.wqs = False
        elif move.pieceMove == "bK":
            self.currentCastleRights.bks = False
            self.currentCastleRights.bqs = False

        # A rook loses its side's right when it moves from its original square
        # or when it is captured on that square.
        self.removeCastleRightForRookAt(move.pieceMove, move.startRow, move.startCol)
        self.removeCastleRightForRookAt(move.pieceCaptured, move.endRow, move.endCol)

    def removeCastleRightForRookAt(self, piece, row, col):
        if piece == "wR" and row == 7:
            if col == 0:
                self.currentCastleRights.wqs = False
            elif col == 7:
                self.currentCastleRights.wks = False
        elif piece == "bR" and row == 0:
            if col == 0:
                self.currentCastleRights.bqs = False
            elif col == 7:
                self.currentCastleRights.bks = False


    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRights = CastleRights(self.currentCastleRights.wks,self.currentCastleRights.bks,self.currentCastleRights.wqs,self.currentCastleRights.bqs)
        moves = self.getAllPossibleMoves()
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0],self.whiteKingLocation[1],moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0],self.blackKingLocation[1],moves)
        # Exclude moves that leave the moving side's king in check.
        for i in range(len(moves)-1,-1,-1):
            self.makeMove(moves[i])
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undoMove()  
        if len(moves) == 0:
            if self.inCheck():
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        
        self.enpassantPossible = tempEnpassantPossible
        self.currentCastleRights = tempCastleRights
        return moves

    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r,c,moves)
        return moves
    
    def getPawnMoves(self,r,c,moves):
        if self.whiteToMove:
            if self.board[r-1][c] == "--":
                moves.append(Move((r,c),(r-1,c),self.board))
                if r == 6 and self.board[r-2][c] == "--":
                    moves.append(Move((r,c),(r-2,c),self.board))
            if c-1 >= 0:
                if self.board[r-1][c-1][0] == "b":
                    moves.append(Move((r,c),(r-1,c-1),self.board))
                elif (r-1,c-1) == self.enpassantPossible and self.board[r][c-1] == "bp":
                    moves.append(Move((r,c),(r-1,c-1),self.board, isEnpassantMove = True))
            if c+1 <= 7:
                if self.board[r-1][c+1][0] == "b":
                    moves.append(Move((r,c),(r-1,c+1),self.board))
                elif (r-1,c+1) == self.enpassantPossible and self.board[r][c+1] == "bp":
                    moves.append(Move((r,c),(r-1,c+1),self.board, isEnpassantMove = True))
        else:
            if self.board[r+1][c] == "--":
                moves.append(Move((r,c),(r+1,c),self.board))
                if r == 1 and self.board[r+2][c] == "--":
                    moves.append(Move((r,c),(r+2,c),self.board))
            if c-1 >= 0:
                if self.board[r+1][c-1][0] == "w":
                    moves.append(Move((r,c),(r+1,c-1),self.board))
                elif (r+1,c-1) == self.enpassantPossible and self.board[r][c-1] == "wp":
                    moves.append(Move((r,c),(r+1,c-1),self.board, isEnpassantMove = True))
            if c+1 <= 7:
                if self.board[r+1][c+1][0] == "w":
                    moves.append(Move((r,c),(r+1,c+1),self.board))
                elif (r+1,c+1) == self.enpassantPossible and self.board[r][c+1] == "wp":
                    moves.append(Move((r,c),(r+1,c+1),self.board, isEnpassantMove = True))

            

    def getRookMoves(self,r,c,moves):
        directions = ((-1,0),(0,-1),(1,0),(0,1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1,8):
                endRow = r + d[0]*i
                endCol = c + d[1]*i
                if 0 <= endRow < 8  and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        moves.append(Move((r,c),(endRow,endCol),self.board))
                    elif enemyColor == endPiece[0]:
                        moves.append(Move((r,c),(endRow,endCol),self.board))
                        break
                    else:
                        break
                else:
                    break

    def getKnightMoves(self,r,c,moves):
        knightMoves = ((-2,-1),(-2,1),(2,-1),(2,1),(1,-2),(1,2),(-1,-2),(-1,2))
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + knightMoves[i][0]
            endCol = c + knightMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    moves.append(Move((r,c),(endRow,endCol),self.board))


    def getBishopMoves(self,r,c,moves):
        directions = ((-1,-1),(-1,1),(1,-1),(1,1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1,8):
                endRow = r + d[0]*i
                endCol = c + d[1]*i
                if 0 <= endRow < 8  and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        moves.append(Move((r,c),(endRow,endCol),self.board))
                    elif enemyColor == endPiece[0]:
                        moves.append(Move((r,c),(endRow,endCol),self.board))
                        break
                    else:
                        break
                else:
                    break


    def getQueenMoves(self,r,c,moves):
        self.getRookMoves(r,c,moves)
        self.getBishopMoves(r,c,moves)

    def getKingMoves(self,r,c,moves):
        kingMoves = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    moves.append(Move((r,c),(endRow,endCol),self.board))
        

    def getCastleMoves(self,r,c,moves):
        homeRow = 7 if self.whiteToMove else 0
        king = "wK" if self.whiteToMove else "bK"
        if (r, c) != (homeRow, 4) or self.board[r][c] != king:
            return
        if self.squareUnderAttack(r,c):
            return 
        if (self.whiteToMove and self.currentCastleRights.wks) or (not self.whiteToMove and self.currentCastleRights.bks):
            self.getKingsideCastleMoves(r,c,moves)
        if (self.whiteToMove and self.currentCastleRights.wqs) or (not self.whiteToMove and self.currentCastleRights.bqs):
            self.getQueensideCastleMoves(r,c,moves)

    def getKingsideCastleMoves(self,r,c,moves):
        rook = "wR" if self.whiteToMove else "bR"
        if self.board[r][7] == rook and self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if not self.squareUnderAttack(r,c+1) and not self.squareUnderAttack(r,c+2):
                moves.append(Move((r,c),(r,c+2),self.board,isCastleMove = True))


    def getQueensideCastleMoves(self,r,c,moves):
        rook = "wR" if self.whiteToMove else "bR"
        if self.board[r][0] == rook and self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--":
            if not self.squareUnderAttack(r,c-1) and not self.squareUnderAttack(r,c-2):
                moves.append(Move((r,c),(r,c-2),self.board,isCastleMove = True))

class CastleRights():
    def __init__(self,wks,bks,wqs,bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


    


class Move():
    def __init__(self, startSq, endSq, board, isEnpassantMove = False, isCastleMove = False):
        self.ranksToRows = {"1":7,"2":6,"3":5,"4":4,"5":3,"6":2,"7":1,"8":0}
        self.rowsToRanks = {v:k for k,v in self.ranksToRows.items()}
        self.filesToCols = {"a":0,"b":1,"c":2,"d":3,"e":4,"f":5,"g":6,"h":7}
        self.colsToFiles = {v:k for k,v in self.filesToCols.items()}
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMove = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        # en-passant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wp" if self.pieceMove == "bp" else "bp"
        # pawn promotion
        self.isPawnPromotion = False
        if (self.pieceMove == "wp" and self.endRow == 0) or (self.pieceMove == "bp" and self.endRow == 7):
            self.isPawnPromotion = True

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        self.isCastleMove = isCastleMove
    def __eq__(self, other):
        if isinstance(other , Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow,self.startCol) + self.getRankFile(self.endRow,self.endCol)

    def getRankFile(self,r,c):
        return self.colsToFiles[c]  + self.rowsToRanks[r]

