from sublayer import SubLayer
import poller
from protocolo_enum import State_Session, Role, CONTROLE_SESSION
from random import randrange

class Sessao(SubLayer):

    def __init__(self, fileobj=None, timeout=0):
        super().__init__(fileobj, timeout)
        self.buffer_rx = bytearray()
        self.__state = State_Session.DISC
        self.__role = None
        self.__idSessao = None
        self.disable_timeout()
        
    def handle(self):
        pass
    def __send_message_control(self, tipo:CONTROLE_SESSION):
        msg = bytearray()
        msg.append(tipo.value)
        msg.append(self.__idSessao)
        self.get_lower(msg)
    
    def __send_message_dados(self, dados):
        msg = bytearray()
        msg.append(CONTROLE_SESSION.DATA.value)
        msg.append(self.__idSessao)
        # Append dados
        for bit in dados:
            msg.append(bit)
        self.reload_timeout()
        self.get_lower(msg)
      
    def send(self, dados):
        #Caso a digite '!DR' será enviado o comando DR para a outra ponta
        if dados[:-1].decode('utf8') == "a!DR":
            self.__send_message_control(CONTROLE_SESSION.DR)
            self.__state = State_Session.HALF1
            return
        #caso digite '!fail' a conexão será perdida sem avisar o outro lado
        if dados[:-1].decode('utf8') == "a!Fail":
            self.__idSessao = None
            self.__role = None
            self.__state = State_Session.DISC
            return
         
        if self.__role == None: 
            print('Estabelecendo conexão, aguarde...')
            self.disable_upper() # Desabilita superior até que estabeleça sessão
            self.__role = Role.INICIADOR
            self.__state = State_Session.WAIT
            self.__idSessao = 0 #randrange(256)
            # Envia CR
            self.__send_message_control(CONTROLE_SESSION.CR)
            self.reload_timeout()
            self.enable_timeout() # start e habilita timeout       
            
        elif self.__role == Role.INICIADOR:      
            if self.__state != State_Session.HALF1:
                self.__send_message_dados(dados)       
        else:
            if self.__state != State_Session.HALF1:
                self.__send_message_dados(dados)

    def SessionFsmPassive(self, dados):
        tipo = self.__obtemtipo(dados)
        if self.__state == State_Session.CONN_PASSIVO:
            self.__conn_passivo(tipo, dados)
        elif self.__state == State_Session.HALF1:
            self.__half1(tipo,dados) 
        elif self.__state == State_Session.HALF2:
            self.__half2(tipo)    
        
    def SessionFsmInit(self, dados):
        tipo = self.__obtemtipo(dados)
        if self.__state == State_Session.CONN_INICIADOR:
            self.__conn_iniciador(tipo, dados)
        elif self.__state == State_Session.WAIT:
            self.__wait(tipo)
        elif self.__state == State_Session.HALF1:
            self.__half1(tipo, dados) 
        elif self.__state == State_Session.HALF2:
            self.__half2(tipo)    

    def __obtemtipo(self, data: bytearray):
        return data[0] & 1 << 0 | data[0] & 1 << 1 | data[0] & 1 << 2

    def __disc(self):
        print("Conexão encerrada.")
        self.__state = State_Session.DISC
        self.__idSessao = None
        self.__role = None
        self.disable_timeout()

    def __wait(self, tipo:int):
        # Verificar se foi recebido um CC
        # Caso positivo: Envia CC e muda o estado e avisa a adaptação que está conectado, caso negativo: faz nada
        if tipo == CONTROLE_SESSION.CC.value:
           self.__send_message_control(CONTROLE_SESSION.CC)
           self.enable_upper()
           print('Conexão estabelecida!')
           self.__state = State_Session.CONN_INICIADOR  
        
    def __conn_iniciador(self, tipo, dados):
      # Pode receber: DATA, KA, DR
      # Se recebe DATA notifica upper - OK
      # Se recebe KA faz um Reload no timeout
      # Se recebe DR envia DR e muda para o estado Half2 - OK
      if tipo == CONTROLE_SESSION.DATA.value:
          self.get_upper(dados[2:])
      elif tipo == CONTROLE_SESSION.DR.value:
          self.__send_message_control(CONTROLE_SESSION.DR)
          self.__state = State_Session.HALF2   
    
    def __conn_passivo(self, tipo, dados):
      # Recebe DATA, CC, KA, DR
      # Se recebe DATA notifica upper
      # Se recebe KA, da um reload no timeout
      # Se recebe CC, faz nada
      # Se recebe DR, envia DR e muda de estado para HALF2 
       if tipo == CONTROLE_SESSION.DATA.value:
          self.get_upper(dados[2:])
       elif tipo == CONTROLE_SESSION.DR.value:
          self.__send_message_control(CONTROLE_SESSION.DR)
          self.__state = State_Session.HALF2 
       elif tipo == CONTROLE_SESSION.CC.value:
          self.__state = State_Session.CONN_PASSIVO
           
    
    def __half1(self, tipo,dados):
      # Se recebe DR manda DC e vai para o estado DISC - Ok
      # Fail vem de cima, Timeout trata fora da maquina de estados
      # SE recebe DATA notifica Upper - Ok
      if tipo == CONTROLE_SESSION.DR.value:
          self.__send_message_control(CONTROLE_SESSION.DC)
          self.__disc()
      elif tipo == CONTROLE_SESSION.DATA.value:
          self.get_upper(dados[2:])   
      
    
    def __half2(self, tipo):
      # Se recebe DR volta para o estado DISC
      # Fail vem de cima, Timeout trata fora da maquina de estados  
      if tipo == CONTROLE_SESSION.DC.value:
          self.__disc()
    
    def receive(self, dados):
       if self.__role == Role.INICIADOR:
           self.reload_timeout()
           self.SessionFsmInit(dados)
       elif self.__role == None:
           self.__role = Role.PASSIVO
           self.__idSessao = dados[1]
           self.__state = State_Session.CONN_PASSIVO
           self.__send_message_control(CONTROLE_SESSION.CC) # Envia CC 
           self.enable_timeout() # Habilita timeout
       else:
           self.reload_timeout()
           self.SessionFsmPassive(dados)
        
       self.enable_timeout()
    # Envia o quadro para a camada superior, retirando os dois primeiros bytes
    def consome(self, dados):
        self.get_upper(dados[2:])

    def handle_timeout(self):
        super().handle_timeout()
        self.__disc()