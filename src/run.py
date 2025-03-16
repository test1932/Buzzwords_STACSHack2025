import pygame
from Game import Game
import time
import sys
import socket
import threading
import json

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

pygame.init()

# Set the width and height of the screen [width, height]
size = (1400, 900)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Buzzwords By Net")
done = False

clock = pygame.time.Clock()

held_keys = set()
last_time = time.time()

isServer = sys.argv[1].lower() == "server"
ip = sys.argv[2]
port = int(sys.argv[3])

if isServer:
    MCAST_GRP = '224.1.2.3'
    MCAST_PORT = 5007
    msock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    msock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    pos = [0,0]
    
    game = Game(pos)
    networkListener = threading.Thread(target = game.lobbyListener, \
        args=[ip, port, MCAST_GRP, MCAST_PORT])
    networkListener.start()
    
else:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    conn = sock
    time.sleep(0.5)
    data = sock.recv(1024).decode("utf-8")
    
    i = data.find("}") + 1
    pos = json.loads(data[i:])

    MCAST_INFO = json.loads(data[:i])
    msock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        msock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except AttributeError:
        pass
    msock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32) 
    msock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    host = socket.gethostbyname(socket.gethostname())
    msock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
    msock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, 
                    socket.inet_aton(MCAST_INFO["ip"]) + socket.inet_aton(host))
    msock.bind((MCAST_INFO["ip"],MCAST_INFO["port"]))
    
    game = Game(pos)
    
    multicastThread = threading.Thread(target = game.multicastListener, args=[msock])
    multicastThread.start()

player = game.teams[0][0]
    
def sendKey(c, isDown):
    conn.sendall(bytes(json.dumps({
        "type":"keydown" if isDown else "keyup", 
        "key":c,
        "mouse":pygame.mouse.get_pos()
    }), "utf-8"))



while not done:
    screen.fill(WHITE)
    events = pygame.event.get()
    
    if isServer:
        time_diff = time.time() - last_time
        last_time = time.time()
        
        for event in events:
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                player.held_keys.append(pygame.key.name(event.key))
            elif event.type == pygame.KEYUP and \
                    pygame.key.name(event.key) in player.held_keys:
                player.held_keys.remove(pygame.key.name(event.key))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                player.held_keys.append("j")
                mousePos = pygame.mouse.get_pos()
                player.mouseX = mousePos[0]
                player.mouseY = mousePos[1]
            elif event.type == pygame.MOUSEBUTTONUP and "j" in player.held_keys:
                player.held_keys.remove("j")
        
        game.update(time_diff)
        if game.phase == "game":
            msock.sendto(bytes(json.dumps(game.serialize()), "utf-8"), (MCAST_GRP, MCAST_PORT))
        elif game.phase == "win":
            msock.sendto(bytes(f"win{game.winner}", "utf-8"), (MCAST_GRP, MCAST_PORT))
        game.displayState(screen)
    
    else:
        for event in events:
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                sendKey(pygame.key.name(event.key), True)
            elif event.type == pygame.KEYUP:
                sendKey(pygame.key.name(event.key), False)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                sendKey("j", True)
            elif event.type == pygame.MOUSEBUTTONUP:
                sendKey("j", False)
        
        game.displayState(screen)
    
    pygame.display.flip()
    clock.tick(60)
pygame.quit()