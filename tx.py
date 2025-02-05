from serial import Serial

serial = Serial('/dev/pts/5', 9600, timeout=12)

flag = [0x7E]

conteudo = 'j'.encode('ASCII')

serial.write(flag)
serial.write(conteudo)
serial.write(conteudo)
serial.write(conteudo)
serial.write(conteudo)
serial.write(conteudo)
serial.write(flag)
