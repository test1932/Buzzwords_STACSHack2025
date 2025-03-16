import pygame

class Projectile:
    WIDTH = 10
    HEIGHT = 10
    image = pygame.image.load("../assets/Projectile.png")
    image = pygame.transform.scale(image, (WIDTH, HEIGHT))
    
    def __init__(self, x, y, vx, vy, bounces_left):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.width = Projectile.WIDTH
        self.height = Projectile.HEIGHT
        self.image = Projectile.image
        self.bounces = bounces_left
        self.isCollidable = False
        
    def display(self, screen):
        screen.blit(self.image, (self.x - Projectile.WIDTH / 2, self.y - Projectile.HEIGHT / 2))
        
    def bounce(self, is_x):
        if is_x:
            self.vx *= -1
        else:
            self.vy *= -1
        self.bounces -= 1
        return self.bounces < 0
    
    def serialize(self):
        return {
            "x": self.x,
            "y": self.y
        }
        
    def deserialize(self, data):
        self.x = data["x"]
        self.y = data["y"]
        return self