from sublayer import SubLayer
import poller
from protocolo_enum import State, Character, State_Arq, CONTROLE_ARQ


class Arq(SubLayer):

    def __init__(self, fileobj=None, timeout=0):
        super().__init__(fileobj, timeout)
        self.buffer_tx = bytearray()
        self.buffer_rx = bytearray()
        self.__m = 0
        self.__n = 0
        self.__state = State_Arq.IDLE
        self.disable_timeout()

    def handle(self):
        pass

    def receive(self, dados):
        self.reload_timeout()
        self.buffer_rx = dados
        self.Arqfsm()


    def send(self, dados):
        if self.__state == State_Arq.IDLE:
            super().send(dados)
            self.buffer_tx = dados
            if self.__n == 0:
                self.criaquadro(CONTROLE_ARQ.DATA_0)
            else:
                self.criaquadro(CONTROLE_ARQ.DATA_1)
            self.__state = State_Arq.WAIT
            self.enable_timeout()
            self.reload_timeout()
        else:
            print('Aguarde, não está pronto para transmitir... pacote descatado\n')

    def Arqfsm(self):
        tipo = self.__obtemtipo(self.buffer_rx)
        if self.__state == State_Arq.IDLE:
            self.__idle(tipo)
        elif self.__state == State_Arq.WAIT:
            self.__wait(tipo)
        else:
            print("Estado inválido")

    def __obtemtipo(self, data: bytearray):
        return data[0] & 1 << 7 | data[0] & 1 << 3

    def __verifica_id_sessao(self, dados):
       return dados[1] == 0
    
    ##envia o ack para a camada inferior
    def __enviaACK(self, controle: CONTROLE_ARQ):
        quadro = bytearray()
        quadro.append(controle)
        quadro.append(0)  # reservado
        quadro.append(0)  # payload vazio
        self.get_lower(quadro)

    def __idle(self, tipo):
        if tipo == CONTROLE_ARQ.DATA_0.value:
            # Envia ack 0
            self.__enviaACK(CONTROLE_ARQ.ACK_0.value)
            if self.__m == 0:
                # consome
                self.consome()

                self.__m = 1

        elif tipo == CONTROLE_ARQ.DATA_1.value:
            # Envia ack 1
            self.__enviaACK(CONTROLE_ARQ.ACK_1.value)
            if self.__m == 1:
                # consome
                self.consome()
                self.__m = 0

    def __wait(self, tipo):
        if tipo == CONTROLE_ARQ.DATA_0.value:
            # Envia ack 0
            self.__enviaACK(CONTROLE_ARQ.ACK_0.value)
            if self.__m == 0:
                # consome
                self.consome()
                self.__m = 1
        elif tipo == CONTROLE_ARQ.DATA_1.value:
            # Envia ack 1
            self.__enviaACK(CONTROLE_ARQ.ACK_1.value)
            if self.__m == 1:
                # consome
                self.consome()
                self.__m = 0
        elif tipo == CONTROLE_ARQ.ACK_0.value:
            if self.__n == 0:
                self.__n = 1
                self.__state = State_Arq.IDLE
                self.disable_timeout()
        elif tipo == CONTROLE_ARQ.ACK_1.value:
            if self.__n == 1:
                self.__n = 0
                self.__state = State_Arq.IDLE
                self.disable_timeout()
                

    def criaquadro(self, controle: CONTROLE_ARQ):
        quadro = bytearray()
        
        if self.buffer_tx:
            quadro.extend(self.buffer_tx)
            quadro[0] |= controle.value
        else:
            quadro.append([controle.value])
        self.get_lower(quadro)

    # envia o quadro para a camada superior, retirando os dois primeiros bytes
    def consome(self):
        if self.__verifica_id_sessao(self.buffer_rx):
            self.get_upper(self.buffer_rx)

    def handle_timeout(self):
        super().handle_timeout()
        self.reload_timeout()
        if self.__n == 0:
            self.criaquadro(CONTROLE_ARQ.DATA_0)
        else:
            self.criaquadro(CONTROLE_ARQ.DATA_1)
