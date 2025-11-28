from socket import *
import ssl
import base64
from dotenv import load_dotenv
import os

# Carrega variáveis
load_dotenv()

smtp_server = 'smtp.gmail.com'
smtp_port = 587

sender = os.getenv('SENDER')
password = os.getenv('PASSWORD')
receiver = os.getenv('RECEIVER')

image_path = 'imagem.png'

# cria socket e conecta (threeway-handshake, syn, syn-ack, ack)
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((smtp_server, smtp_port))

# https://serversmtp.com/smtp-error/

# Recebe saudação inicial (220)
resposta = sock.recv(2048)
print(resposta.decode())

# primeiro ehlo
sock.sendall(b'EHLO estudante\r\n')
resposta = sock.recv(2048)
print(resposta.decode())

# solicita STARTTLS
sock.sendall(b'STARTTLS\r\n')
resposta = sock.recv(2048)
print(resposta.decode())

# carrega as configuracoes de seguranca padrao do so
context = ssl.create_default_context()

# cria um novo socket seguro
# server_hostname verifica se o certificado digital que o servidor entregou realmente pertence a smtp.gmail.com
ssock = context.wrap_socket(sock, server_hostname=smtp_server)

# segundo ehlo, afinal, a comunicacao "resetou"
ssock.sendall(b'EHLO estudante\r\n')
resposta = ssock.recv(2048)
print(resposta.decode())

# solicitamos a autenticacao
ssock.sendall(b'AUTH LOGIN\r\n')
resposta = ssock.recv(2048)
print(resposta.decode())

# envia usuario
# o b indica que é uma string de bytes, \r\n equivalente ao enter
ssock.sendall(base64.b64encode(sender.encode()) + b'\r\n')
resposta = ssock.recv(2048)
print(resposta.decode())

# envia a senha
ssock.sendall(base64.b64encode(password.encode()) + b'\r\n')
resposta = ssock.recv(2048)
print(resposta.decode())

# servidor ira aceitar

# envelope (MAIL FROM / RCPT TO)
ssock.sendall(f'MAIL FROM:<{sender}>\r\n'.encode())
resposta = ssock.recv(2048)
print(resposta.decode())

ssock.sendall(f'RCPT TO:<{receiver}>\r\n'.encode())
resposta = ssock.recv(2048)
print(resposta.decode())

# comanda DATA avisa que acabou o envelope, tudo que enviar a partir de agora é conteúdo (cabeçalho, corpo, anexo)
ssock.sendall(b'DATA\r\n')
resposta = ssock.recv(2048)
print(resposta.decode())

# MIME (Multipurpose Internet Mail Extensions)
# boundary é como um muro que separa texto de anexo
# multipart/mixed avisa que o conteudo não é um texto so, e sim conteudo do tipo "mixed"
boundary = 'BOUNDARYPADRAO'
subject = "teste smtp"

# cabecalho
corpo = (
    f'Subject: {subject}\r\n'
    f'From: {sender}\r\n'
    f'To: {receiver}\r\n'
    'MIME-Version: 1.0\r\n'
    f'Content-Type: multipart/mixed; boundary={boundary}\r\n\r\n'
)

# conteudo, primeiro texto
corpo += (
    f'--{boundary}\r\n'
    'Content-Type: text/plain; charset="utf-8"\r\n'
    'olá\r\n\r\n'
)

# tratamento da imagem
try:
    # le a imagem em binario e transforma em base64
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
        # fatia em linhas de 76 caracteres
        linhas_b64 = '\r\n'.join([img_b64[i:i + 76] for i in range(0, len(img_b64), 76)])

    corpo += (
        f'--{boundary}\r\n'
        'Content-Type: image/png; name="imagem.png"\r\n'
        'Content-Transfer-Encoding: base64\r\n'
        'Content-Disposition: attachment; filename="imagem.png"\r\n\r\n'
        f'{linhas_b64}\r\n'
        f'--{boundary}--\r\n'
    )
except FileNotFoundError:
    print("nao achou")
    exit()

# finaliza com ponto final
corpo += '\r\n.\r\n'

ssock.sendall(corpo.encode())
resposta = ssock.recv(2048)
print(resposta.decode())

# se despede de forma educada
ssock.sendall(b'QUIT\r\n')
resposta = ssock.recv(2048)
print(resposta.decode())

ssock.close()