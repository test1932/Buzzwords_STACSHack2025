import pygame
from Player import Player

class Wall:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def display(self, screen):
        pygame.draw.rect(screen, (200,100,100), pygame.Rect(
            self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
        ))
        
    def handleCollision(self, player):
        p_width = player.image.get_rect().width
        p_height = player.image.get_rect().height
        
        intersects_x = abs(player.x - self.x) - (self.width / 2 + p_width / 2)
        intersects_y = abs(player.y - self.y) - (self.height / 2 + p_height / 2)
        
        if not (intersects_x < 0 and intersects_y < 0):
            return
        
        if intersects_x > intersects_y:
            if player.x < self.x:
                player.x = min(player.x, self.x - self.width / 2 - p_width / 2)
            else:
                player.x = max(player.x, self.x + self.width / 2 + p_width / 2)
            
        else:
            if player.y < self.y:
                player.y = min(player.y, self.y - self.height / 2 - p_height / 2)
            else:
                player.y = max(player.y, self.y + self.height / 2 + p_height / 2)