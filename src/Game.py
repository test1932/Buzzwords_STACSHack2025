from Player import Player, NetPlayer, AIPlayerAttack, AIPlayerHold
from Wall import Wall
from Region import Region
import pygame
import math
import threading
import random
import json
import socket

pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 30)

def collides(first, other):
    intersects_x = abs(other.x - first.x) - (first.width / 2 + other.width / 2)
    intersects_y = abs(other.y - first.y) - (first.height / 2 + other.height / 2)
    intersects = intersects_x < 0 and intersects_y < 0
    return intersects, intersects_x > intersects_y

class Game:
    def __init__(self, playerPos):
        self.phase = "lobby"
        self.playerPos = playerPos
        self.settings = {
            "friendly_fire": True
        }
        
        self.remappings = {
            "space": " ",
            "backslash": "\\",
            "forward slash": "/",
            "semicolon": ";",
            "colon": ":",
            "comma": ",",
            "period": ".",
            "left parenthesis": "(",
            "right parenthesis": ")",
            "minus sign": "-"
        }
        
        self.words = open("../buzzwords.txt", "r").read().split("\n")
        self.words = list(filter(lambda x:x!="", self.words))
        self.teamWords = [[],[]]
        self.shownWords = [[],[]]
        self.teamProgress = [0,0] # to 1
        self.teams = [
            [
                Player(100, 500)
            ], 
            []
        ]
        
        self.walls = [
            Wall(225, 400, 50, 800), # left
            Wall(1175, 400, 50, 800), # right
            Wall(700, 25, 900, 50), # top
            Wall(700, 775, 900, 50), # bottom
            
            Wall(450, 250, 25, 150),
            Wall(450, 550, 25, 250),
            
            Wall(950, 550, 25, 150),
            Wall(950, 250, 25, 250),
            
            Wall(700, 250, 250, 25),
            Wall(700, 550, 250, 25),
            
            Wall(700, 150, 25, 200),
            Wall(700, 650, 25, 200)
        ]
        
        self.score_regions = [
            Region(700, 400, 100, (0,0,255)),
            Region(900, 600, 100, (0,0,255)),
            Region(500, 200, 100, (0,0,255))
        ]
        
        self.spawns = [
            Region(1150, 50, 200, (0,255,0)),
            Region(250, 750, 200, (0,255,0))
        ]
        
    def hide(self, word):
        words = word.split(" ")
        return " ".join(list(map(lambda x:"*" * len(x), words)))
    
    def init(self):
        # generate each team's words
        for i in range(len(self.teams)):
            self.teamWords[i] = random.sample(self.words, k = 10)
        for (i,team) in enumerate(self.teamWords):
            for (j,word) in enumerate(team):
                hiddenWord = self.hide(self.teamWords[i][j])
                self.shownWords[i].append(hiddenWord)
        print(self.teamWords)
        
        for i in range(len(self.teams)):
            for player in self.teams[i]:
                player.x = self.spawns[i].x
                player.y = self.spawns[i].y
        
        for team in self.teams:
            for player in team:
                if type(player) == NetPlayer:
                    thread = threading.Thread(target = player.netInputLoop)
                    thread.start()
        
    def update(self, timediff):
        if self.phase == "lobby":
            for key in self.teams[0][0].held_keys:
                if key == "return":
                    self.init()
                    self.phase = "game"
                elif key == "space":
                    if len(self.teams[0]) > len(self.teams[1]):
                        if random.random() > 0.5:
                            self.teams[1].append(AIPlayerAttack(1,1,self, 0))
                        else:
                            self.teams[1].append(AIPlayerHold(1, 1, self, 0))
                    else:
                        if random.random() > 0.5:
                            self.teams[0].append(AIPlayerAttack(1,1,self, 1))
                        else:
                            self.teams[0].append(AIPlayerHold(1, 1, self, 1))
            self.teams[0][0].held_keys = []
        
        for (i,team) in enumerate(self.teams):
            for player in team:
                if player.isTyping:
                    self.handleTypingMode(player, i)
                else:
                    self.handleActionMode(player, timediff)
                
        for team in self.teams:
            for player in team:
                if type(player) == AIPlayerAttack or type(player) == AIPlayerHold:
                    player.update(timediff)
                player.updateProjectiles(timediff)

        self.handleLetterGain(timediff)
        self.handleWallCollision()
        self.handlePlayerCollision()
        self.handleProjectileCollisions()
        
    def handleProjectileCollisions(self):
        for team in self.teams:
            for otherteam in self.teams:
                for player in team:
                    for otherplayer in otherteam:
                        self.handleProjectileCollisionsBetweenPlayers(player, otherplayer)
    
    def handleProjectileCollisionsBetweenPlayers(self, p1, p2):
        if p1 == p2:
            return
        to_remove_p1 = []
        to_remove_p2 = []
        for pr1 in p1.projectiles:
            for pr2 in p2.projectiles:
                if collides(pr1, pr2)[0]:
                    to_remove_p1.append(pr1)
                    to_remove_p2.append(pr2)
        for i in to_remove_p1:
            p1.projectiles.remove(i)
        for i in to_remove_p2:
            p2.projectiles.remove(i)
    
    def handleTypingMode(self, player, team_i):
        for key in player.held_keys:
            if key in self.remappings:
                player.typedWord += self.remappings[key]
            elif key == "backspace":
                player.typedWord = player.typedWord[:-1]
            elif key == "return":
                self.handleSubmission(player.typedWord, team_i)
                player.typedWord = ""
                player.isTyping = False
            else:
                player.typedWord = player.typedWord + key
        player.held_keys = []
    
    def handleSubmission(self, submission, team_i):
        for (i,word) in enumerate(self.teamWords[team_i]):
            if word.lower() == submission:
                self.shownWords[team_i][i] = submission
    
    def handleActionMode(self, player, timediff):
        for key in player.held_keys:
            # movement
            if key == "w":
                player.moveForwards(-150 * timediff)
            elif key == "s":
                player.moveForwards(150 * timediff)
            elif key == "a":
                player.rotate(2 * timediff)
            elif key == "d":
                player.rotate(-2 * timediff)
            elif key == "escape":
                player.isTyping = True
                player.typedWord = ""
                player.held_keys = []
                break
            elif key == "left shift":
                player.boost()
            elif key == "j":
                if player.y - player.mouseY == 0:
                    angle = 0
                else:
                    grad = (player.x - player.mouseX) / (player.y - player.mouseY)
                    angle = math.atan(grad)
                    if player.y > player.mouseY:
                        angle += math.pi
                player.shoot(angle, 250)
        
    def handleWallCollision(self):
        for team in self.teams:
            for player in team:
                for wall in self.walls:
                    self.handleCollision(player, wall)
                    
    def handlePlayerCollision(self):
        for team in self.teams:
            for player1 in team:
                for otherTeam in self.teams:
                    for player2 in otherTeam:
                        if player1 == player2:
                            continue
                        self.handlePCollision(player1, player2)
    
    def handlePCollision(self, p1, p2):
        Wall.handleCollision(p1, p2)
                    
    def handleCollision(self, player, wall):
        wall.handleCollision(player)
        to_remove = []
        for projectile in player.projectiles:
            # walls
            (intersects, isX) = collides(wall, projectile)
            if intersects:
                projectile.bounce(isX)
            if projectile.bounces == 0:
                to_remove.append(projectile)
            
            if not collides(player, projectile)[0]:
                projectile.isCollidable = True
            
            # players
            for (i,other_team) in enumerate(self.teams):
                for other_player in other_team:
                    if collides(other_player, projectile)[0]:
                        if projectile.isCollidable:
                            to_remove.append(projectile)
                            other_player.x = self.spawns[i].x
                            other_player.y = self.spawns[i].y
            
        for ob in to_remove:
            if ob in player.projectiles:
                player.projectiles.remove(ob)
    
    def handleLetterGain(self, timediff):
        for region in self.score_regions:
            counts = [0,0]
            for (i, team) in enumerate(self.teams):
                for player in team:
                    if region.isWithin(player):
                        counts[i] += 1
            if counts[0] > counts[1]:
                self.teamProgress[0] += timediff
            elif counts[1] > counts[0]:
                self.teamProgress[1] += timediff
        
        self.handleUnveilLetters()
        
    def handleUnveilLetters(self):
        for i in range(len(self.teams)):
            if self.teamProgress[i] > 1:
                self.teamProgress[i] = 0
                self.replaceNextLetter(i)
    
    def replaceNextLetter(self, i):
        words_indexes = list(range(len(self.shownWords[i])))
        random.shuffle(words_indexes)
        for word_i in words_indexes:
            charIndex = self.shownWords[i][word_i].find("*")
            if charIndex != -1:
                self.shownWords[i][word_i] = self.teamWords[i][word_i][:charIndex + 1] + \
                    self.hide(self.teamWords[i][word_i][charIndex + 1:])
                return
        self.winner = i + 1
        self.phase = "win"
    
    # display stuff
    def displayState(self, screen):
        if self.phase == "lobby":
            self.displayLobby(screen)
            return
        elif self.phase == "win":
            self.displayWin(screen)
            return
        self.displayRegions(screen)
        self.displaySpawns(screen)
        self.displayWalls(screen)
        self.displayPlayers(screen)
        self.displayWords(screen)
        self.displayTypedWord(screen)
        
    def displayWin(self, screen):
        screen.blit(font.render(f"Winner: {self.winner}", False, (0,0,0)), (200, 200))
        
    def displayLobby(self, screen):
        screen.blit(font.render("Lobby", False, (0,0,0)), (200, 200))
        screen.blit(font.render(str(len(self.teams[0])) + " vs " + str(len(self.teams[1])), False, (0,0,0)), (200, 250))
    
    def displayTypedWord(self, screen):
        pygame.draw.rect(screen, (200, 150, 150), pygame.Rect(200, 800, 1000, 100))
        w = self.teams[self.playerPos[0]][self.playerPos[1]].typedWord
        s = font.render(w, False, (0,0,0))
        screen.blit(s, (600, 850))
    
    def displaySpawns(self, screen):
        for spawn in self.spawns:
            spawn.display(screen)
        
    def displayRegions(self, screen):
        for region in self.score_regions:
            region.display(screen)
        
    def displayPlayers(self, screen):
        for team in self.teams:
            for player in team:
                player.display(screen)
                
    def displayWalls(self, screen):
        for wall in self.walls:
            wall.display(screen)
            
    def displayWords(self, screen):
        for (i, team) in enumerate(self.teams):
            x = 20 if i == 1 else 1220
            pygame.draw.rect(screen, (145, 200, 255), pygame.Rect(x-20, 0, 200, 900))
            
            for (j, word) in enumerate(self.shownWords[i]):
                sur = font.render(word, False, (0,0,0))
                screen.blit(sur, (x, j * 50 + 50))
                
            prog = font.render(str(round(self.teamProgress[i] * 100, 2)) + "%", False, (0,0,0))
            screen.blit(prog, (x, 750))
            
    def serialize(self):
        return {
            "teams": [[player.serialize() for player in team] for team in self.teams],
            "prog": self.teamProgress,
            "shown": self.shownWords
        }
        
    def deserialize(self, data):
        self.teams = [
            [Player(1,1).deserialize(p) for p in team]
            for team in data["teams"]
        ]
        self.teamProgress = data["prog"]
        self.shownWords = data["shown"]
        return self
    
    def lobbyListener(self, ip, port, MCAST_GRP, MCAST_PORT):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((ip, port))
        while True:
            print("listening on ",port)
            sock.listen()
            conn, addr = sock.accept()
            conn.sendall(bytes(json.dumps({"ip":MCAST_GRP,"port":MCAST_PORT}), "utf-8"))
            if len(self.teams[1]) < len(self.teams[0]):
                self.teams[1].append(NetPlayer(1,1,conn))
                conn.send(bytes(json.dumps([1,len(self.teams[1]) - 1]), "utf-8"))
            else:
                self.teams[0].append(NetPlayer(1,1,conn))
                conn.send(bytes(json.dumps([0,len(self.teams[0]) - 1]), "utf-8"))
            
    def multicastListener(self, msock):
        while True:
            multicast_str = msock.recv(10000).decode("utf-8")
            if multicast_str[:3] == "win":
                self.phase = "win"
                self.winner = int(multicast_str[3]) + 1
                break
            self.deserialize(json.loads(multicast_str))
            self.phase = "game"