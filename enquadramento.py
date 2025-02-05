from sublayer import SubLayer
import poller
from serial import Serial
from protocolo_enum import State, Character, OPERACAO_PROTO
from arq import Arq
import sys
from sessao import Sessao
from CRC import checkFCS, criarFCS

class Enquadramento(SubLayer):

    def __init__(self, serial: Serial, timeout: float):
        super().__init__(serial, timeout=timeout)
        self.__serial = serial
        self.__state = State.IDLE
        self.__buffer = bytearray()
        self.enable_timeout()


    def handle(self):
        self.reload_timeout()
        self.handle_fsm()

    def handle_fsm(self):
        read = self.__serial.read(1)
        self.reload_timeout()
        if self.__state == State.IDLE:
            self.state_idle(read)
        elif self.__state == State.PREP:
            self.state_prep(read)
        elif self.__state == State.ESC:
            self.state_esc(read)
        elif self.__state == State.RX:
            self.state_rx(read)
        else:
            print("Estado inválido")

    def state_idle(self, read: bytes):
        if read == Character.FLAG.value:
            self.__buffer.clear()
            self.__state = State.PREP

    def state_prep(self, read):
        if read == Character.ESC.value:
            self.__state = State.ESC

        elif read != Character.FLAG.value:
            self.__buffer.append(ord(read))
            self.__state = State.RX

    def state_esc(self, read):

        if read == Character.FLAG.value or read == Character.ESC.value:

            self.__state = State.IDLE
            self.__buffer.clear
        else:
            self.__state = State.RX
            self.__buffer.append((ord(read) ^ 32))

    def state_rx(self, read) -> bool:
        if read == Character.FLAG.value:
            self.__state = State.IDLE
            if checkFCS(self.__buffer):
                self.__buffer.pop()
                self.__buffer.pop()
                self.get_upper(self.__buffer)
            self.__buffer.clear()

        elif read == Character.ESC.value and len(self.__buffer) <= 1025:
            self.__state = State.ESC
        elif len(self.__buffer) <= 1025:
            self.__buffer.append(ord(read))
        else:
            self.__buffer.clear()
            self.__state = State.IDLE

    def send(self, dados: bytes):
        # Envia os dados pela serial
        # iterar os 1024 dados, verifica se há um caractere especial e adiciona o esc
        dados = dados.split(b'\n')[0]
        
        quadro = bytearray()
        quadro.append(ord(Character.FLAG.value))
        for bit in dados:
            character = bytes([bit])
            if character == Character.FLAG.value or character == Character.ESC.value:
                quadro.append(ord(Character.ESC.value))
                quadro.append(ord(character) ^ 32)
            else:
                quadro.append(ord(character))


        for bit in criarFCS(dados):
            character = bytes([bit])
            if character == Character.FLAG.value or character == Character.ESC.value:
                quadro.append(ord(Character.ESC.value))
                quadro.append(ord(character) ^ 32)
            else:
                quadro.append(ord(character))
                
        quadro.append(ord(Character.FLAG.value))
        self.__serial.write(quadro)


    def receive(self, dados):
        pass

    def handle_timeout(self):
        super().handle_timeout()
        self.__buffer.clear()
        self.__state = State.IDLE
        


class Adaptacao(SubLayer):
    def __init__(self, input: sys.stdin, timeout: float, operacao=''):
        super().__init__(input, timeout=timeout)
        self.__input = input
        self.__operacao = operacao

    def send(self, dados):
        pass

    def receive(self, dados: bytes):
        print('RX:', dados.decode('utf8'))


    def handle(self):
        # lê uma linha do teclado
        dados = self.__input.readline()
        

        # adicionado o IDPROTO e bits necessários para desligar camadas antes dos dados para enviar para a camada superior
        idproto = '-'

        if self.__operacao == '':
            pass
        elif self.__operacao == OPERACAO_PROTO.UNTILARQ.value or self.__operacao == OPERACAO_PROTO.UNTILENQ.value:
            idproto = idproto + '--'


        dados = idproto + dados
        dados = dados.encode('utf8')


        # envia os dados para a subcamada inferior
        self.get_lower(dados)


class PPPJMV:

    def __init__(self, serial_port: str, timeout: int, baud_rate=9600, operacao='' ) -> None:
        sch = poller.Poller()
        self.serial = Serial(serial_port, baud_rate, timeout=timeout)

        if operacao == '':
            
            callback_enquadramento = Enquadramento(serial=self.serial, timeout=1)
            callback_arq = Arq(timeout=3)
            callback_sessao = Sessao(timeout=timeout)
            callback_adaptacao = Adaptacao(input=sys.stdin, timeout=timeout)
            
            callback_sessao.connect(callback_adaptacao)
            callback_arq.connect(callback_sessao)
            callback_enquadramento.connect(callback_arq)
            
            sch.adiciona(callback_enquadramento)
            sch.adiciona(callback_arq)
            sch.adiciona(callback_adaptacao)
            sch.adiciona(callback_sessao)

            
        elif operacao == 'untilEnq':

            callback_enquadramento = Enquadramento(serial=self.serial, timeout=1)
            callback_adaptacao = Adaptacao(input=sys.stdin, timeout=timeout, operacao=operacao)
            
            callback_enquadramento.connect(callback_adaptacao)
            
            sch.adiciona(callback_enquadramento)
            sch.adiciona(callback_adaptacao)
            
        elif operacao == 'untilArq':


            callback_enquadramento = Enquadramento(serial=self.serial, timeout=1)
            callback_arq = Arq(timeout=3)
            callback_adaptacao = Adaptacao(input=sys.stdin, timeout=timeout, operacao=operacao)
            
            callback_arq.connect(callback_adaptacao)
            callback_enquadramento.connect(callback_arq)
            
            sch.adiciona(callback_enquadramento)
            sch.adiciona(callback_arq)
            sch.adiciona(callback_adaptacao)
            

        sch.despache()
