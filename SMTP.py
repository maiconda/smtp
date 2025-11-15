from socket import *            # Para criar conexão TCP/IP direta
import ssl              # Para "upgrade" do socket para TLS (segurança/encriptação)
import base64           # Para codificar dados binários (imagem) em texto para SMTP
from dotenv import load_dotenv # Para ler variáveis do arquivo .env
import os               # Para acessar variáveis de ambiente

load_dotenv()           # Carrega variáveis do .env para os.environ (sem expor senhas no código)

smtp_server = 'smtp.gmail.com' # Endereço do servidor SMTP do Gmail
smtp_port = 587               # Porta 587 indicada para STARTTLS (negociação segura)

sender = os.getenv('SENDER')      # E-mail remetente (do arquivo .env)
password = os.getenv('PASSWORD')  # Senha de app do Gmail (do arquivo .env)
receiver = os.getenv('RECEIVER')  # E-mail destinatário (do arquivo .env)

image_path = 'imagem.jpg'         # Caminho do arquivo de imagem a anexar

# 1. Criando o socket TCP/IP básico e conectando ao servidor SMTP
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((smtp_server, smtp_port)) # Abre conexão TCP com o Gmail
sock.recv(2048)                       # Lê mensagem de saudação '220...' do servidor

# 2. Iniciando conversa SMTP (EHLO) e negociando segurança (STARTTLS)
sock.sendall(b'EHLO estudante\r\n')  # EHLO diz quem é o cliente e obtém capacidades do servidor
sock.recv(2048)                       # Recebe resposta (normalmente código 250)
sock.sendall(b'STARTTLS\r\n')        # Solicita "upgrade" de conexão para TLS (requisito do Gmail)
sock.recv(2048)                       # Resposta '220 2.0.0 Ready to start TLS' sinaliza pronto para segurar

# 3. "Upgrade" do socket: tornando seguro (TLS/SSL), obrigatório para Gmail
context = ssl.create_default_context()
ssock = context.wrap_socket(sock, server_hostname=smtp_server) # Envolve socket, mantendo autenticação de nome do servidor

# 4. Precisa reiniciar handshake EHLO depois do upgrade para TLS!
ssock.sendall(b'EHLO estudante\r\n') # Gmail exige nova identificação já sob conexão criptografada
ssock.recv(2048)

# 5. Autenticação SMTP: AUTH LOGIN (usuário e senha em base64)
ssock.sendall(b'AUTH LOGIN\r\n')                 # Inicia autenticação por login/senha
ssock.recv(2048)                                  # Resposta do servidor pedindo usuário (em base64)
ssock.sendall(base64.b64encode(sender.encode()) + b'\r\n')    # Envia usuário codificado
ssock.recv(2048)                                  # Resposta do servidor pedindo senha (em base64)
ssock.sendall(base64.b64encode(password.encode()) + b'\r\n')  # Envia senha codificada
ssock.recv(2048)                                  # "235 Authenticated" indica sucesso

# 6. Comandos SMTP de envelope: remetente e destinatário
ssock.sendall(f'MAIL FROM:<{sender}>\r\n'.encode())  # Inicia envelope do remetente
ssock.recv(2048)
ssock.sendall(f'RCPT TO:<{receiver}>\r\n'.encode())  # Inicia envelope do destinatário
ssock.recv(2048)
ssock.sendall(b'DATA\r\n')                           # Comando para enviar dados do e‑mail
ssock.recv(2048) # Resposta 354: pronto para receber conteúdo do e‑mail

# 7. Montando corpo MIME multipart manualmente (texto + imagem base64)
boundary = 'MIMEBOUNDARY12345'                       # Fronteira para separar partes do multipart
subject = "Teste SMTP manual com imagem"

corpo = (
    f'Subject: {subject}\r\n'
    f'From: {sender}\r\n'
    f'To: {receiver}\r\n'
    'MIME-Version: 1.0\r\n'
    f'Content-Type: multipart/mixed; boundary={boundary}\r\n\r\n'
)
corpo += (
    f'--{boundary}\r\n'
    'Content-Type: text/plain; charset="utf-8"\r\n\r\n'
    'Este e-mail tem uma imagem anexa.\r\n\r\n'
)
with open(image_path, 'rb') as f:    # Abre a imagem como bytes
    img_b64 = base64.b64encode(f.read()).decode() # Converte binário em base64
    # Quebra texto base64 em linhas de até 76 caracteres (recomendado por MIME)
    linhas_b64 = '\r\n'.join([img_b64[i:i+76] for i in range(0, len(img_b64), 76)])
corpo += (
    f'--{boundary}\r\n'
    'Content-Type: image/jpeg; name="imagem.jpg"\r\n'
    'Content-Transfer-Encoding: base64\r\n'
    'Content-Disposition: attachment; filename="imagem.jpg"\r\n\r\n'
    f'{linhas_b64}\r\n'
    f'--{boundary}--\r\n'                            # Finaliza o multipart
)
corpo += '\r\n.\r\n'  # Encerramento do SMTP: ponto em linha separada
ssock.sendall(corpo.encode())
ssock.recv(2048)  # Resposta do servidor sobre aceitação da mensagem

# 8. Quit: finaliza a sessão SMTP
ssock.sendall(b'QUIT\r\n')
ssock.recv(2048)
ssock.close()   # Fecha socket seguro
