from poller import Callback


class SubLayer(Callback):
    def __init__(self, fileobj=None, timeout=0):
        super().__init__(fileobj, timeout)
        self.__lower = None
        self.__upper = None

    def send(self, dados):
        pass

    def receive(self, dados):
        pass

    def connect(self, uplayer: 'SubLayer'):
        self.__upper = uplayer
        uplayer.__lower = self

    def get_upper(self, dados: bytes):
        return self.__upper.receive(dados)

    def get_lower(self, dados: bytes):
        return self.__lower.send(dados)

    def disable_upper(self):
        self.__upper.disable()  
        self.__upper.disable_timeout()
    def enable_upper(self):
        self.__upper.enable() 
        self.__upper.enable_timeout()