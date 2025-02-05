import sys
from protocolo_enum import OPERACAO_PROTO
import enquadramento

def main():
    arg1 = sys.argv[1]

    if len(sys.argv) > 3:
        print("Argumentos insuficientes. Uso: python main.py <Porta serial> <operação (opcional)>")
        sys.exit(1)
    else:
        try:
            arg2 = sys.argv[2]
        except IndexError:
            arg2 = ''

        if arg2 != OPERACAO_PROTO.ALL.value and arg2 != OPERACAO_PROTO.UNTILARQ.value and arg2 != OPERACAO_PROTO.UNTILENQ.value:
            print('Operação de ser untilArq ou untilArq')
        else:
            enquadramento.PPPJMV("/dev/pts/" + arg1, 12, operacao=arg2)

if __name__ == '__main__':
    main()
