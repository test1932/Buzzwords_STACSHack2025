import pygame
import Game

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

pygame.init()

# Set the width and height of the screen [width, height]
size = (1000, 800)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("Buzzwords By Net")
done = False

clock = pygame.time.Clock()

game = Game.Game()

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
    
    

    screen.fill(WHITE)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()