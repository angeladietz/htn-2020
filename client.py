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
import math
import random

class User(pygame.sprite.Sprite):
  def __init__(self, avatar):
    super(User, self).__init__()
    
    self.avatar = avatar
    print(self.avatar)
    # self.surf = pygame.image.load(self.avatar).convert()
    if (self.avatar == "img/girl.png"):
        self.surf = pygame.image.load(self.avatar).convert()
        self.surf.set_colorkey((247,247,247), RLEACCEL)
    elif (self.avatar == "img/dog.png"):
        self.surf = pygame.image.load(self.avatar).convert()
        self.surf.set_colorkey((246,246,246), RLEACCEL)
    else:
        self.surf = pygame.image.load(self.avatar)
    self.surf = pygame.transform.scale(self.surf,(100,100))
    #self.surf.fill((255, 255, 255))
    self.rect = self.surf.get_rect()
    self.sound = None

  # Move the sprite based on user keypresses
  def update(self, pressed_keys, width, height):
    if pressed_keys[K_UP]:
      self.rect.move_ip(0, -5)
    if pressed_keys[K_DOWN]:
      self.rect.move_ip(0, 5)
    if pressed_keys[K_LEFT]:
      self.rect.move_ip(-5, 0)
    if pressed_keys[K_RIGHT]:
      self.rect.move_ip(5, 0)

    #Keep player on the screen
    if self.rect.left < 0:
      self.rect.left = 0
    if self.rect.right > width:
      self.rect.right = width
    if self.rect.top <= 0:
      self.rect.top = 0
    if self.rect.bottom >= height:
      self.rect.bottom = height

  def set_user_song(self, song):
    self.sound = song

class Arena(ConnectionListener):
    def __init__(self, host, port):
        pygame.mixer.pre_init(44100, -16, 2, 4096)
        pygame.init()
        self.Connect((host, port))

        print("Chat client started")
        print("Ctrl-C to exit")
        # get a nickname from the user before starting
        print("Enter your nickname: ")
        self.my_name = stdin.readline().rstrip("\n")        
        song = input("Enter your song: \n")

        self.width = 870
        self.height = 535
        self.background = pygame.image.load("img/workspace.jpg")
        self.background = pygame.transform.scale(self.background, (self.width, self.height))
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Arena")
        self.clock=pygame.time.Clock()


        self.users = {}
        self.user_channels = {}
        self.font = pygame.font.SysFont(None, 32)
        
        self.avatars = ["girl.png" , "cool-guy.png", "dog.png"]
        avatar = "img/" + random.choice(self.avatars)
        self.me = User(avatar)
        self.users[self.my_name] = self.me
        self.me.set_user_song(song)
        self.should_play_music = False
        while pygame.mixer.find_channel() is None:
          pygame.mixer.set_num_channels(pygame.mixer.get_num_channels()+1)
        self.user_channels[self.my_name] = pygame.mixer.find_channel()
        if self.should_play_music:
            self.user_channels[self.my_name].play(pygame.mixer.Sound("sounds/" + self.me.sound))
            
        # pygame.mixer.music.play(-1)
        connection.Send({"action": "nickname", "nickname": self.my_name, "x": self.me.rect.x, "y": self.me.rect.y, "sound": song, "avatar": self.me.avatar })
        print("Client started")
    
    # def getAvatar(self):
    #     for avatar in self.avatars:
    #       if (self.avatars[avatar] == False):
    #         myavatar = 

    def update(self): 
        connection.Pump()
        self.Pump()
        # self.Send({"action": "hello", "message": "hello client!"})

        self.clock.tick(60)
        self.screen.blit(self.background, (0,0))
        self.pressed_keys = pygame.key.get_pressed()
        self.me.update(self.pressed_keys, self.width, self.height)
        self.Send({"action": "pos", "name": self.my_name, "x":self.me.rect.x, "y":self.me.rect.y, "sound": self.me.sound, "avatar" : self.me.avatar})
        self.users[self.my_name] = self.me

        for u_name, u_val in self.users.items():
          # label = self.font.render(u_name, 1, (0,0,0))
          self.screen.blit(u_val.surf, u_val.rect)
          self.screen.blit(self.font.render(u_name, 1, (0,0,0)), (u_val.rect.x, u_val.rect.y+100))

        #update the volume of each channel
        
        for u_name, u_val in self.users.items():
            if u_name == self.my_name:
                self.user_channels[self.my_name].set_volume(0.1)
            else:
              #find distance between self and u_name
              #anything more than 400 away is 0, anything closer than 20 is 1.0
              distance = math.hypot(abs(self.me.rect.x - u_val.rect.x), abs(self.me.rect.y - u_val.rect.y))
              volume = 1.0
              if distance > 400:
                volume = 0
              elif distance < 20:
                volume = 1.0
              else:
                volume = 1 - ((distance - 20) / 380)
              self.user_channels[u_name].set_volume(volume)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        #update the screen
        pygame.display.flip()

    #######################################
    ### Network event/message callbacks ###
    #######################################
    
    def Network_first(self, data):
      if data['status'] == True:
        self.should_play_music = True
        for user, channel in self.user_channels.items():
            print(self.users[user].sound)
            channel.play(pygame.mixer.Sound("sounds/" +self.users[user].sound))

    def Network_users(self, data):
        #TODO: if we have a user which is not in data, delete it
        user_names = list(self.users.keys())
        print(user_names)
        for u in data['users']:
            if u in user_names:
                user_names.remove(u)

        #everyone left in user_names are users who left the arena
        for old_user in user_names:
            # stop their channel
            # remove them from self.users
            if old_user in self.user_channels:
                self.user_channels[old_user].stop()
                del self.user_channels[old_user]
            if old_user in self.users:
                del self.users[old_user]

        print("*** users: " + ", ".join([u for u in data['users']]))

    def Network_newuser(self, data):
        new_user = User(data['avatar'])
        new_user.rect.x = data['x']
        new_user.rect.y = data['y']
        new_user.sound = data['sound']
        while pygame.mixer.find_channel() is None:
          pygame.mixer.set_num_channels(pygame.mixer.get_num_channels()+1)
        self.user_channels[data['user']] = pygame.mixer.find_channel()
        if self.should_play_music:
            self.user_channels[data['user']].play(pygame.mixer.Sound("sounds/" + new_user.sound))
        self.users[data['user']] = new_user
        print("new user", data)

    def Network_updateuserpos(self, data):
        # print("updating data for", data['user'])
        if data['user'] in self.users.keys():
            self.users[data['user']].rect.x = data['x']
            self.users[data['user']].rect.y = data['y']
        else:
          self.Network_newuser(data)
    
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