import math
import pygame
import time
from Projectile import Projectile
import json

class Player:
    WIDTH = 30
    HEIGHT = 40
    image = pygame.image.load("../assets/Player.png")
    image = pygame.transform.scale(image, (WIDTH, HEIGHT))
    COOLDOWN = 0.5
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = Player.WIDTH
        self.height = Player.HEIGHT
        
        self.angle = 0 # radians
        self.image = Player.image
        self.projectiles = []
        self.last_shot = time.time()
        
        self.held_keys = []
        self.mouseX = 0
        self.mouseY = 0
        self.isTyping = False
        self.typedWord = ""
        
    def display(self, screen):
        img_width = self.image.get_rect().width
        img_height = self.image.get_rect().height
        screen.blit(self.image, (self.x - 0.5 * img_width, self.y - 0.5 * img_height))
        for projectile in self.projectiles:
            projectile.display(screen)
        
    def moveForwards(self, value):
        self.x += math.sin(self.angle) * value
        self.y += math.cos(self.angle) * value

    def rotate(self, value):
        self.angle += value
        self.image = pygame.transform.rotate(Player.image, self.angle * 180 / math.pi)
        
    def shoot(self, angle, value):
        if time.time() - self.last_shot < Player.COOLDOWN:
            return
        self.last_shot = time.time()
        if len(self.projectiles) < 5:
            vx = math.sin(angle) * value
            vy = math.cos(angle) * value
            self.projectiles.append(Projectile(self.x, self.y, vx, vy, 2))
    
    def updateProjectiles(self, timediff):
        for projectile in self.projectiles:
            projectile.x += projectile.vx * timediff
            projectile.y += projectile.vy * timediff
    
    def serialize(self):
        return {
            "x": self.x,
            "y": self.y,
            "angle":self.angle,
            "projectiles": [projectile.serialize() for projectile in self.projectiles],
            "typing":self.isTyping,
            "word":self.typedWord
        }
        
    def deserialize(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.angle = data["angle"]
        self.projectiles = [Projectile(1,1,1,1,1).deserialize(p) for p in data["projectiles"]]
        self.rotate(0)
        self.isTyping = data["typing"]
        self.typedWord = data["word"]
        return self
        
# murder bot 5000
class AIPlayer(Player):
    def __init__(self, x, y, game, opponent_team_i):
        super().__init__(x, y)
        self.game = game
        self.opponent_team_i = opponent_team_i
        
    def update(self, timediff):
        e1 = self.game.teams[self.opponent_team_i][0]
        for e in self.game.teams[self.opponent_team_i]:
            if (e.x - self.x)**2 + (e.y - self.y)**2 < (e1.x - self.x)**2 + (e1.y - self.y)**2:
                e1 = e
        if self.y - e1.y == 0:
            angle = 0
        else:
            grad = (self.x - e1.x) / (self.y - e1.y)
            angle = math.atan(grad)
            if self.y > e1.y:
                angle += math.pi
        self.shoot(angle, 250)
        
        if self.angle < angle:
            self.rotate(2 * timediff)
        else:
            self.rotate(-2 * timediff)
        
        self.moveForwards(150 * timediff)
    
class NetPlayer(Player):
    def __init__(self, x, y, conn):
        super().__init__(x, y)
        self.conn = conn
    
    def netInputLoop(self):
        while True:
            datas = self.getNetInput()
            for data in datas:
                self.mouseX = data["mouse"][0]
                self.mouseY = data["mouse"][1]
                if data["type"] == "keydown":
                    self.held_keys.append(data["key"])
                elif data["type"] == "keyup" and data["key"] in self.held_keys:
                    self.held_keys.remove(data["key"])
    
    def getNetInput(self):
        data = self.conn.recv(1024).decode("utf-8")
        datas = data.split("}{")
        if len(datas) > 1:
            for i in range(len(datas)-1):
                datas[i] = datas[i] + "}"
            for i in range(1,len(datas)):
                datas[i] = "{" + datas[i]
        return list(map(lambda x:json.loads(x), datas))
    