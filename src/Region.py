import pygame

class Region:
    def __init__(self, x, y, radius, colour):
        self.x = x
        self.y = y
        self.radius = radius
        self.colour = colour
        
    def isWithin(self, other):
        return(self.x - other.x)**2 + (self.y - other.y)**2 < self.radius ** 2
    
    def display(self, screen):
        pygame.draw.circle(screen, self.colour, (self.x, self.y), self.radius)