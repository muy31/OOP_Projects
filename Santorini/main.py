import sys
import argparse
import random
from pathlib import Path

class InvalidWorkerException(Exception):
    "Raised when user enters a character for a worker that doesn't exist"
    pass

class OpponentWorkerException(Exception):
    "Raised when user enters a character for a worker that is not their own"
    pass

class InvalidDirectionException(Exception):
    "Raised when user enters an invalid string for a direction"
    pass

class CannotMoveException(Exception):
    "Raised when a piece cannot move in the specified direction"
    pass

class CannotBuildException(Exception):
    "Raised when a piece cannot build in the specified direction (after moving)"
    pass

class Game:
    def initializeGame(self):

        arguments = ["human", "human", "off", "off"]
        for i in range(1, len(sys.argv)):
            arguments[i - 1] = sys.argv[i]
        
        #Undos Allowed
        if arguments[2] == "on":
            self.undos = True
            self.undosAllowed()
        else:
            self.undos = False

        self.gameMap = Map(5,5)
        
        #Player Types
        if arguments[0] == "heuristic":
            self.white = HeuristicPlayer(0)
        elif arguments[0] == "random":
            self.white = RandomPlayer(0)
        else:
            self.white = PlayerAgent(0)

        if arguments[1] == "heuristic":
            self.black = HeuristicPlayer(1)
        elif arguments[1] == "random":
            self.black = RandomPlayer(1)
        else:
            self.black = PlayerAgent(1)

        if arguments[3] == "on":
            self.showScore = True
        else:
            self.showScore = False

        a = Piece('A', 0, self.gameMap)
        a.setLocation((3, 1), self.gameMap)

        b = Piece('B', 0, self.gameMap)
        b.setLocation((1, 3), self.gameMap)

        y = Piece('Y', 1, self.gameMap)
        y.setLocation((1, 1), self.gameMap)

        z = Piece('Z', 1, self.gameMap)
        z.setLocation((3, 3), self.gameMap)

        #All the pieces on the board
        self.allPieces = [a, b, y, z]

        #How the pieces are allotted to each player
        self.players = {}
        self.players[0] = [a, b]
        self.players[1] = [y, z]

        self.gameMap.drawMap()
        

    def undosAllowed(self):
        GameState.initializeHistory()

    def getPiece(self, pieceID):
        for piece in self.allPieces:
            if piece.ID == pieceID:
                return piece
        raise InvalidWorkerException    

    def gameOverCheck(self):
        #Victory conditions
        for worker in self.allPieces:
            if self.gameMap.boardBuild[worker.location] >= 3:
                if worker.player == 0:
                    self.printTurn()
                    print("white has won")
                else:
                    self.printTurn()
                    print("black has won")
                return True
        #Loss conditions
        for playerID in range(2):
            numActions = 0
            for worker in self.players[playerID]:
                numActions += len(worker.possibleActions(self.gameMap))
            if numActions == 0:
                if playerID == 0:
                    self.printTurn()
                    print("black has won")
                else:
                    self.printTurn()
                    print("white has won")
                return True

        return False

    def printTurn(self):
        if self.playerTurn == self.white:
            name = "white (AB)"
        else:
            name = "blue (YZ)"

        if self.showScore:
            print("Turn: " + str(self.counter) + ", " + name + ", " + str(self.evaluateScores()))
        else:
            print("Turn: " + str(self.counter) + ", " + name)

    def runGame(self):
        self.counter = 1
        self.playerTurn = self.white
        GameState(self)

        while not self.gameOverCheck():

            self.printTurn()
            GameState(self)

            if self.undos:
                while True:
                    ip = input("undo, redo, or next\n")
                    if ip == "undo":
                        GameState.undoState(self)
                        self.gameMap.drawMap()
                        self.printTurn()
                    elif ip == "redo":
                        GameState.redoState(self)
                        self.gameMap.drawMap()
                        self.printTurn()
                    else:
                        break

            #Set turn for next round
            self.playerTurn.takeTurn(self)
            if self.playerTurn == self.white:
                self.playerTurn = self.black
            else:
                self.playerTurn = self.white

            self.gameMap.drawMap()
            self.counter += 1

    def evaluateScores(self):
        
        heightScore = 0
        centerScore = 0
        distanceScore = 0

        for worker in self.players[self.playerTurn.pID]:
            heightScore += game.gameMap.boardBuild[worker.location]

        centerScoreDict = {
            (0, 0): 0,
            (0, 1): 0,
            (0, 2): 0,
            (0, 3): 0,
            (0, 4): 0,
            (1, 0): 0,
            (1, 1): 1,
            (1, 2): 1,
            (1, 3): 1,
            (1, 4): 0,
            (2, 0): 0,
            (2, 1): 1,
            (2, 2): 2,
            (2, 3): 1,
            (2, 4): 0,
            (3, 0): 0,
            (3, 1): 1,
            (3, 2): 1,
            (3, 3): 1,
            (3, 4): 0,
            (4, 0): 0,
            (4, 1): 0,
            (4, 2): 0,
            (4, 3): 0,
            (4, 4): 0
            }

        #Center Score
        for worker in self.players[self.playerTurn.pID]:
            centerScore += centerScoreDict[worker.location]

        #Distance Score
        if self.playerTurn.pID == 0:
            enemyID = 1
        else:
            enemyID = 0
        for antiworker in self.players[enemyID]:
            bestdist = 1000
            for worker in self.players[self.playerTurn.pID]:
                dist = max(abs(antiworker.location[0] - worker.location[0]), abs(antiworker.location[1] - worker.location[1]))
                if dist < bestdist:
                    bestdist = dist
            distanceScore += bestdist

        return (heightScore, centerScore, 8 - distanceScore)
            
class GameState:

    history = []
    cursor = len(history)

    def initializeHistory():
        GameState.history = []
        GameState.cursor = len(GameState.history)

    def __init__(self, game):
        #Saves state
        self.boardBuild = game.gameMap.boardBuild.copy()
        self.pieceBoard = game.gameMap.pieces.copy()
        self.pieceLocations = []
        self.playerTurn = game.playerTurn
        self.counter = game.counter
        for piece in game.allPieces:
            self.pieceLocations.append((piece, piece.location))

        if GameState.cursor < len(GameState.history):
            GameState.history[GameState.cursor] = self
        else:
            GameState.history.append(self)

        GameState.cursor += 1

        if GameState.cursor < len(GameState.history):
            del GameState.history[GameState.cursor: len(GameState.history)]


    def restoreState(self, game):
               
        game.gameMap.boardBuild = self.boardBuild.copy()
        game.gameMap.pieces = self.pieceBoard.copy()
        game.playerTurn = self.playerTurn
        game.counter = self.counter
        for pieceL in self.pieceLocations:
            pieceL[0].setLocation(pieceL[1], game.gameMap)

    def undoState(game):
        if GameState.cursor >= 2:
            GameState.cursor -= 2
            GameState.history[GameState.cursor].restoreState(game)
            GameState.cursor += 1

    def redoState(game):
        if GameState.cursor < len(GameState.history):
            GameState.history[GameState.cursor].restoreState(game)
            GameState.cursor += 1


class Piece:
    
    def __init__(self, pieceID, player, map):
        self.ID = pieceID
        self.player = player
        self.location = (0, 0)
        map.pieces[self.location] = self.ID

    def setLocation(self, nLocus, map):
        map.pieces[self.location] = None
        self.location = nLocus
        map.pieces[self.location] = self.ID

    def possibleActions(self, map):
        movements = ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']
        possibleMoves = []

        initialLocation = self.location

        for move in movements:
            value = self.canMovePiece(move, map)
            if value[0]:
                for buildDir in movements:
                    nextL = map.applyDirection(value[1], buildDir)
                    if map.locationInBounds(nextL) and not map.locationOccupied(nextL) and map.boardBuild[nextL] < 4:
                        possibleMoves.append((move, buildDir))

        return possibleMoves
              
    def canMovePiece(self, dir, map):
        nextLocation = map.applyDirection(self.location, dir)
        if not map.locationInBounds(nextLocation):
            return (False, nextLocation)
        elif map.locationOccupied(nextLocation):
            return (False, nextLocation)
        elif map.boardBuild[nextLocation] - map.boardBuild[self.location] > 1:
            return (False, nextLocation)
        else:
            return (True, nextLocation)
        
    def movePiece(self, dir, map):
        nextLocation = map.applyDirection(self.location, dir)
        if not map.locationInBounds(nextLocation):
            raise CannotMoveException
        elif map.locationOccupied(nextLocation):
            raise CannotMoveException
        elif map.boardBuild[nextLocation] - map.boardBuild[self.location] > 1:
            raise CannotMoveException
        else:
            self.setLocation(nextLocation, map)
        
    def build(self, dir, map):
        nextLocation = map.applyDirection(self.location, dir)
        if not map.locationInBounds(nextLocation):
            raise CannotBuildException
        elif map.locationOccupied(nextLocation):
            raise CannotBuildException
        elif map.boardBuild[nextLocation] >= 4:
            raise CannotBuildException
        else:
            map.boardBuild[nextLocation] += 1

class Map:
    """
    This class constructs and stores the board state and any othe ruseful information for the game.
    """

    def drawMap(self):
        rowStr = "+--+--+--+--+--+"
        print(rowStr)
        for i in range(self.rows):
            st = ""
            for j in range(self.cols):
                if self.pieces[(i,j)] == None:
                    st += "|" + str(self.boardBuild[(i,j)]) + " "
                else:
                    st += "|" + str(self.boardBuild[(i,j)]) + str(self.pieces[(i,j)])
            st += '|'
            print(st)
            print(rowStr)


    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.allBoardLocations = []
        
        self.boardBuild = {}
        self.pieces = {}
        for i in range(rows):
            for j in range(cols):
                self.allBoardLocations.append((i, j))
                self.boardBuild[(i, j)] = 0
                self.pieces[(i,j)] = None

    def applyDirection(self, location, dir):
        dir = dir.upper()
        if dir == 'N':
            return (location[0] - 1, location[1])
        elif dir == 'S':
            return (location[0] + 1, location[1])
        elif dir == 'E':
            return (location[0], location[1] + 1)
        elif dir == 'W':
            return (location[0], location[1] - 1)
        elif dir == 'NE':
            return (location[0] - 1, location[1] + 1)
        elif dir == 'SE':
            return (location[0] + 1, location[1] + 1)
        elif dir == 'SW':
            return (location[0] + 1, location[1] - 1)
        elif dir == 'NW':
            return (location[0] - 1, location[1] - 1)
        else:
            raise InvalidDirectionException

    def locationInBounds(self, locus):
        return locus in self.allBoardLocations

    def locationOccupied(self, locus):
        if self.locationInBounds(locus):
            return not (self.pieces[locus] == None)
        else:
            raise CannotMoveException

class PlayerAgent:

    def __init__(self, playerID):
        self.pID = playerID

    def takeTurn(self, game):
        
        while True:
            try:
                ip = input("Select a worker to move\n")
                p = game.getPiece(ip.upper())
                if p not in game.players[self.pID]:
                    raise OpponentWorkerException
                break
            except InvalidWorkerException:
                print("Not a valid worker")
            except OpponentWorkerException:
                print("That is not your worker")

        while True:
            try:
                ip = input("Select a direction to move (n, ne, e, se, s, sw, w, nw)\n")
                p.movePiece(ip, game.gameMap)
                break
            except InvalidDirectionException:
                print("Not a valid direction")
            except CannotMoveException:
                print("Cannot move " + ip)

        while True:
            try:
                ip = input("Select a direction to build (n, ne, e, se, s, sw, w, nw)\n")
                p.build(ip, game.gameMap)
                break
            except InvalidDirectionException:
                print("Not a valid direction")
            except CannotBuildException:
                print("Cannot build " + ip)

class RandomPlayer(PlayerAgent):

    def takeTurn(self, game):
        possibleActions = []

        for worker in game.players[self.pID]:
            wPos = worker.possibleActions(game.gameMap)
            for a in wPos:
                possibleActions.append((worker, a[0], a[1]))

        action = random.choice(possibleActions)
        action[0].movePiece(action[1], game.gameMap)
        action[0].build(action[2], game.gameMap)

        print(action[0].ID + "," + action[1].lower() + "," + action[2].lower())

class HeuristicPlayer(PlayerAgent):

    def takeTurn(self, game):
        possibleActions = []

        for worker in game.players[self.pID]:
            wPos = worker.possibleActions(game.gameMap)
            for a in wPos:
                possibleActions.append((worker, a[0], a[1]))

        bestScore = -1000000
        bestAction = None

        for action in possibleActions:
            hScore = self.evaluateStateAfterAction(game, action)
            if(hScore > bestScore):
                bestScore = hScore
                bestAction = action

        #Do the best action
        bestAction[0].movePiece(bestAction[1], game.gameMap)
        bestAction[0].build(bestAction[2], game.gameMap)

        print(action[0].ID + "," + action[1].lower() + "," + action[2].lower())

    def evaluateStateAfterAction(self, game, action):
        
        #Store prev data
        pieceLocation = action[0].location
        gameBoard = game.gameMap.boardBuild.copy()
        pieceBoard = game.gameMap.pieces.copy()

        #Do action
        action[0].movePiece(action[1], game.gameMap)
        action[0].build(action[2], game.gameMap)
        gameScore = 0
        heightScore = 0
        centerScore = 0
        distanceScore = 0

        #Check if game over because of this move
        #Victory conditions
        for worker in game.allPieces:
            if worker.player == self.pID:
                heightScore += game.gameMap.boardBuild[worker.location]
            if game.gameMap.boardBuild[worker.location] >= 3:
                if worker.player == self.pID:
                    gameScore += 1000
                else:
                    gameScore += -1000
        #Loss conditions
        for playerID in range(2):
            numActions = 0
            for worker in game.players[playerID]:
                numActions += len(worker.possibleActions(game.gameMap))
            if numActions == 0:
                if playerID == self.pID:
                    gameScore += -1000
                else:
                    gameScore -= 1000

        centerScoreDict = {
            (0, 0): 0,
            (0, 1): 0,
            (0, 2): 0,
            (0, 3): 0,
            (0, 4): 0,
            (1, 0): 0,
            (1, 1): 1,
            (1, 2): 1,
            (1, 3): 1,
            (1, 4): 0,
            (2, 0): 0,
            (2, 1): 1,
            (2, 2): 2,
            (2, 3): 1,
            (2, 4): 0,
            (3, 0): 0,
            (3, 1): 1,
            (3, 2): 1,
            (3, 3): 1,
            (3, 4): 0,
            (4, 0): 0,
            (4, 1): 0,
            (4, 2): 0,
            (4, 3): 0,
            (4, 4): 0
            }

        #Center Score
        for worker in game.players[self.pID]:
            centerScore += centerScoreDict[worker.location]

        #Distance Score
        if self.pID == 0:
            enemyID = 1
        else:
            enemyID = 0
        for antiworker in game.players[enemyID]:
            bestdist = 1000
            for worker in game.players[self.pID]:
                dist = max(abs(antiworker.location[0] - worker.location[0]), abs(antiworker.location[1] - worker.location[1]))
                if dist < bestdist:
                    bestdist = dist
            distanceScore += bestdist

        finalScore = gameScore + heightScore * 3 + centerScore * 2 - distanceScore

        #Undo stuff
        action[0].setLocation(pieceLocation, game.gameMap)
        game.gameMap.boardBuild = gameBoard

        return finalScore



#Driver code 
game = Game()
game.initializeGame()
game.runGame()

    



        