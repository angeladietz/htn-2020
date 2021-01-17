from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from time import sleep
import sys
from weakref import WeakKeyDictionary

class ClientChannel(Channel):
    """
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        self.nickname = "anonymous"
        Channel.__init__(self, *args, **kwargs)
    
    def Close(self):
        self._server.DelUser(self)
    
    ##################################
    ### Network specific callbacks ###
    ##################################
    
    def Network_pos(self, data):
        # print("updating pos")
        # print(data)
        self._server.SendUpdatedUserPos(data['name'], data['x'], data['y'], data['sound'], data['avatar'])
        # self._server.SendUsers()

    def Network_message(self, data):
        self._server.SendToAll({"action": "message", "message": data['message'], "who": self.nickname})
    
    def Network_nickname(self, data):
        self.nickname = data['nickname']
        self._server.SendNewUser(data['nickname'], data['x'], data['y'], data['sound'], data['avatar'])
        self._server.SendUsers()
 
class ArenaServer(Server):
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.users = WeakKeyDictionary()
        print('Server launched')

    def Connected(self, channel, addr):
        self.AddUser(channel)
        print("new connection")

    def AddUser(self, user):
        print("New User" + str(user.addr))
        self.users[user] = True
        # self.SendUsers()
        print("users", [u for u in self.users])
    
    def DelUser(self, user):
        print("Deleting User" + str(user.addr))
        del self.users[user]
        self.SendUsers()

    def SendNewUser(self, u_name, u_x, u_y, sound, avatar):
        self.SendToAll({"action": "newuser", "user": u_name, "x":u_x, "y":u_y, "sound": sound, "avatar" : avatar})

    def SendUpdatedUserPos(self, u_name, u_x, u_y, sound, avatar):
        self.SendToAll({"action": "updateuserpos", "user": u_name, "x":u_x, "y":u_y, "sound": sound, "avatar" : avatar})
    
    def SendUsers(self):
        self.SendToAll({"action": "users", "users": [u.nickname for u in self.users]})
    
    def SendToAll(self, data):
        [u.Send(data) for u in self.users]
    
    def Launch(self):
        while True:
            self.Pump()
            sleep(0.0001)
 
# get command line argument of server, port
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "host:port")
        print("e.g.", sys.argv[0], "localhost:31425")
    else:
        host, port = sys.argv[1].split(":")
        s = ArenaServer(localaddr=(host, int(port)))
        s.Launch()
