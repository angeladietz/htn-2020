import sys
from sys import stdin, exit
from _thread import *
import pygame
from pygame.locals import (
  RLEACCEL,
  K_UP,
  K_DOWN,
  K_LEFT,
  K_RIGHT,
  K_ESCAPE,
  KEYDOWN,
  QUIT,
)

from PodSixNet.Connection import ConnectionListener, connection
from time import sleep

class User(pygame.sprite.Sprite):
  def __init__(self):
    super(User, self).__init__()
    self.surf = pygame.Surface((50, 50))
    self.surf.fill((255, 255, 255))
    self.rect = self.surf.get_rect()

  # Move the sprite based on user keypresses
  def update(self, pressed_keys):
    if pressed_keys[K_UP]:
      self.rect.move_ip(0, -5)
    if pressed_keys[K_DOWN]:
      self.rect.move_ip(0, 5)
    if pressed_keys[K_LEFT]:
      self.rect.move_ip(-5, 0)
    if pressed_keys[K_RIGHT]:
      self.rect.move_ip(5, 0)

    # Keep player on the screen
    # if self.rect.left < 0:
    #   self.rect.left = 0
    # if self.rect.right > width:
    #   self.rect.right = width
    # if self.rect.top <= 0:
    #   self.rect.top = 0
    # if self.rect.bottom >= height:
    #   self.rect.bottom = height

class Arena(ConnectionListener):
    def __init__(self, host, port):
        pygame.init()
        self.Connect((host, port))
        print("Chat client started")
        print("Ctrl-C to exit")
        # get a nickname from the user before starting
        print("Enter your nickname: ")
        self.my_name = stdin.readline().rstrip("\n")
        # launch our threaded input loop
        # t = start_new_thread(self.InputLoop, ())

        width, height = 800, 600
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Arena")
        self.clock=pygame.time.Clock()
        self.users = {}
        self.font = pygame.font.SysFont(None, 32)

        self.me = User()
        self.users[self.my_name] = self.me
        connection.Send({"action": "nickname", "nickname": self.my_name, "x": self.me.rect.x, "y": self.me.rect.y})
        print("Client started")
        
    def update(self): 
        connection.Pump()
        self.Pump()
        # self.Send({"action": "hello", "message": "hello client!"})

        self.clock.tick(60)
        self.screen.fill((150,20,200))
        self.pressed_keys = pygame.key.get_pressed()
        self.me.update(self.pressed_keys)
        self.Send({"action": "pos", "name": self.my_name, "x":self.me.rect.x, "y":self.me.rect.y})
        self.users[self.my_name] = self.me

        for u_name, u_val in self.users.items():
          # label = self.font.render(u_name, 1, (0,0,0))
          self.screen.blit(u_val.surf, u_val.rect)
          self.screen.blit(self.font.render(u_name, 1, (0,0,0)), (u_val.rect.x, u_val.rect.y+15))
        
        # self.screen.blit(self.me.surf, self.me.rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        #update the screen
        pygame.display.flip()

    def InputLoop(self):
        # horrid threaded input loop
        # continually reads from stdin and sends whatever is typed to the server
        while 1:
            connection.Send({"action": "message", "message": stdin.readline().rstrip("\n")})
    
    #######################################
    ### Network event/message callbacks ###
    #######################################
    
    def Network_users(self, data):
        print("*** users: " + ", ".join([u for u in data['users']]))

    def Network_newuser(self, data):
        new_user = User()
        new_user.rect.x = data['x']
        new_user.rect.y = data['y']
        self.users[data['user']] = new_user
        print("new user", data)

    def Network_updateuserpos(self, data):
        # print("updating data for", data['user'])
        if data['user'] in self.users.keys():
            self.users[data['user']].rect.x = data['x']
            self.users[data['user']].rect.y = data['y']
    
    def Network_message(self, data):
        print(data['who'] + ": " + data['message'])

    def Network_connected(self, data):
        print("You are now connected to the server")
    
    def Network_error(self, data):
        print('error:', data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print('Server disconnected')
        exit()

# arena=Arena("localhost", "31425")
# while 1:
#     arena.update()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "host:port")
        print("e.g.", sys.argv[0], "localhost:31425")
    else:
        host, port = sys.argv[1].split(":")
        arena = Arena(host, int(port))
        while 1:
            arena.update()
            sleep(0.001)