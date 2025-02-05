from enum import Enum


class State(Enum):
    IDLE = 0
    PREP = 1
    ESC = 2
    RX = 3


class Character(Enum):
    FLAG = b'~'
    ESC = b'}'


class State_Arq(Enum):
    IDLE = 0
    WAIT = 1


class CONTROLE_ARQ(Enum):
    DATA_0 = 0b00000000  # 0000 0000
    DATA_1 = 0b00001000  # 0000 0100
    ACK_0 = 0b10000000  # 1000 0000
    ACK_1 = 0b10001000  # 1000 0100

class State_Session(Enum):
    DISC = 0
    WAIT = 1
    CONN_INICIADOR = 2
    CONN_PASSIVO = 3
    HALF1 = 4
    HALF2 = 5

class Role(Enum):
    INICIADOR = 1
    PASSIVO = 2 
    
class CONTROLE_SESSION(Enum):
    DATA = 0b000
    CR = 0b100
    CC = 0b101
    DR = 0b110
    DC = 0b111
    KA = 0b011

class OPERACAO_PROTO(Enum):
    ALL = ''
    UNTILARQ = 'untilArq'
    UNTILENQ = 'untilEnq'
