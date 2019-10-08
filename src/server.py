#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver


# start /w pkgmgr /iu:"TelnetClient" - включение Telnet на Windows


class Handler(LineOnlyReceiver):
    factory: 'Server'
    login: str  # login:SOME_TEXT

    def connectionLost(self, reason=connectionDone):
        self.factory.clients.remove(self)
        print("Disconnected")

    def connectionMade(self):
        self.login = None
        self.factory.clients.append(self)
        print("Connected")

    def lineReceived(self, line: bytes):
        message = line.decode()

        if self.login is not None:
            message = f"<{self.login}>: {message}"
            #save current message to history
            self.save_history(message.encode())
            for user in self.factory.clients:
                if user is not self:
                    user.sendLine(message.encode())
        else:
            if message.startswith("login:"):
                login = message.replace("login:", "")
                #loop for connected users
                for user in self.factory.clients:
                    if user.login == login:
                        #duplicate login found
                        self.sendLine(f"Login {login} already used, try another one!".encode())
                        #disconnecting
                        self.transport.loseConnection()
                self.login = login
                print(f"New user: {login}")
                self.sendLine("Welcome!!!".encode())
                #send history
                self.send_history()
            else:
                self.sendLine("Wrong login!".encode())

    #save message to history
    def save_history(self, encoded_message):
        self.factory.history.append(encoded_message)
        #if history more 10 messages - remove first with index 0
        while len(self.factory.history) > 10:
            del self.factory.history[0]

    #send history to user
    def send_history(self):
        for encoded_message in self.factory.history:
            self.sendLine(encoded_message)

class Server(ServerFactory):
    protocol = Handler
    clients: list
    #list for history
    history: list

    def __init__(self):
        self.clients = []
        # init history
        self.history = []

    def startFactory(self):
        print("Server started...")

reactor.listenTCP(
    7410, Server()
)
reactor.run()
