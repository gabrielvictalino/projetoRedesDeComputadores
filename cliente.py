import socket
from threading import Timer

HOST = "127.0.0.1"  # endereço do servidor (localhost)
PORT = 5000  # porta do servidor

def calcular_checksum(payload):
    return sum(ord(c) for c in payload) % 256

def montar_pacote(seq, payload):
    checksum = calcular_checksum(payload)
    return f"DATA;seq={seq};payload={payload};checksum={checksum}"

def validar_pacote(campos):
    payload = campos.get("payload", "")
    checksum_recebido = int(campos.get("checksum", -1))
    checksum_calculado = calcular_checksum(payload)
    return checksum_recebido == checksum_calculado

def fragmentar_texto(texto, tam_bloco=4):  # divide o texto em blocos de tamanho 4 para facilitar o envio
    return [texto[i:i+tam_bloco] for i in range(0, len(texto), tam_bloco)]

def enviar_linha(sock, mensagem
                 ):
    sock.sendall((mensagem + "\n").encode("utf-8"))

def enviar_lote(comeco_do_envio, janela, pacotes, cliente_socket):
    """Envia uma janela completa de pacotes e aguarda ACK da janela inteira"""
    print(f"\n[CLIENTE] Enviando lote da janela: índices {comeco_do_envio} a {min(comeco_do_envio + janela - 1, len(pacotes) - 1)}")
    
    # Envia toda a janela
    for i in range(comeco_do_envio, min(comeco_do_envio + janela, len(pacotes))):
        enviar_linha(cliente_socket, pacotes[i])
        print(f"  [CLIENTE] Enviado: {pacotes[i]}")
    
    # Aguarda o ACK da janela inteira
    return esperarAckOuNack_gbn(cliente_socket, pacotes, len(pacotes))

def esperarAckOuNack_gbn(cliente_socket, pacotes, total_pacotes):
    """Aguarda ACK/NACK do servidor - ACK confirma TODA a janela"""
    cliente_socket.settimeout(5)
    try:
        resposta = cliente_socket.recv(1024).decode("utf-8").strip()
        print(f"[CLIENTE] Recebi: {resposta}")
    except socket.timeout:
        print(f"[CLIENTE] TIMEOUT ao aguardar ACK da janela")
        return None

    # Analisa resposta
    if resposta.startswith("NACK"):
        partes = resposta.split()
        if len(partes) >= 2:
            nack_seq = int(partes[1])
            print(f"[CLIENTE] NACK recebido - retransmitir a partir de seq={nack_seq}")
            return f"NACK {nack_seq}"
    
    elif resposta.startswith("ACK"):
        partes = resposta.split(",")
        partes1 = partes[0].split()
        if len(partes1) > 1:
            seq_confirmado = int(partes1[1])
            print(f"[CLIENTE] ACK recebido - janela confirmada até seq={seq_confirmado}")
            return f"ACK {seq_confirmado}"
    
    return None

def enviar_lote_rs(pacotes, indices, cliente_socket):
    """Envia pacotes individuais para RS"""
    for i in indices:
        if i < len(pacotes):
            enviar_linha(cliente_socket, pacotes[i])
            print(f"  [CLIENTE-RS] Enviado: {pacotes[i]}")

def receber_acks_rs(cliente_socket, confirmados, base, fim_janela, total_pacotes):
    """Recebe múltiplos ACKs e marca pacotes como confirmados"""
    cliente_socket.settimeout(2)
    acks_recebidos = 0
    
    try:
        while True:
            try:
                resposta = cliente_socket.recv(1024).decode("utf-8").strip()
                if not resposta:
                    break
                    
                if resposta.startswith("ACK") and "END" not in resposta:
                    partes = resposta.split()
                    seq_confirmado = int(partes[1])
                    indice = seq_confirmado // 4
                    
                    if 0 <= indice < total_pacotes:
                        confirmados[indice] = True
                        print(f"[CLIENTE-RS] ✓ Confirmado pacote {indice} (seq={seq_confirmado})")
                        acks_recebidos += 1
            except socket.timeout:
                break
    except Exception as e:
        print(f"[CLIENTE-RS] Erro ao receber ACKs: {e}")
    
    return acks_recebidos

    

def main():

    # cria socket TCP/IP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # conecta ao servidor
    cliente_socket.connect((HOST, PORT))
    print(f"conectado ao servidor em {HOST}:{PORT}")

    # exemplo de mensagem de handshake
    modo_operacao = input("Digite o modo de operação a ser trabalhado: (GBN)/(RS) ")  # Go-Back-N  ou repetição seletiva.
    tamanho_max = 100

    # formato: HANDSHAKE;modo=GBN;maxlen=100
    handshake_msg = f"HANDSHAKE;modo={modo_operacao}"
    enviar_linha(cliente_socket, handshake_msg)
    print(f"[CLIENTE] Enviei para o servidor: {handshake_msg}")

    # aguarda resposta do servidor
    data = cliente_socket.recv(1024)
    resposta = data.decode("utf-8").strip()
    resposta_separada = resposta.split("!")
    respostaSeparadaJanela = resposta_separada[1].split(":")
    respostaSeparadaJanela = respostaSeparadaJanela[1]

    print(f"[CLIENTE] Recebi do servidor: {resposta}\n")

    # leitura da mensagem do usuário
    texto = input("Digite a mensagem a ser enviada (min de 30 caracteres): ")
    if len(texto) < 30:
        print("A mensagem deve conter pelo menos 30 caracteres.")
        cliente_socket.close()
        return

    # divide o texto em blocos de até 4 caracteres (carga útil máxima)
    blocos = fragmentar_texto(texto, tam_bloco=4)
    total_pacotes = len(blocos)

    print(f"[CLIENTE] Texto será enviado em {total_pacotes} pacotes.\n")

    arrPacotes = []
    seq=0
    for i, payload in enumerate(blocos):
        # exemplo: DATA;seq=0;total=10;payload=ABCD
        arrPacotes.append(montar_pacote(seq,payload)) 
        seq= seq+4

    totalmenteConfirmado = False
    comeco_envio = 0
    tamanhoJaEnviado = 0
    janela = int(respostaSeparadaJanela)
    
    if modo_operacao == "RS":
        print(f"[CLIENTE] Iniciando Repetição Seletiva. Janela: {janela} pacotes\n")
        confirmados = [False] * total_pacotes
        base = 0
        tentativas_max = 5
        
        while base < total_pacotes:
            fim_janela = min(base + janela, total_pacotes)
            indices_nao_confirmados = [i for i in range(base, fim_janela) if not confirmados[i]]
            
            print(f"[CLIENTE-RS] Enviando janela: índices {base} a {fim_janela - 1}")
            enviar_lote_rs(arrPacotes, indices_nao_confirmados, cliente_socket)
            
            # Aguarda múltiplos ACKs com timeout
            acks = receber_acks_rs(cliente_socket, confirmados, base, fim_janela, total_pacotes)
            print(f"[CLIENTE-RS] Recebido {acks} ACK(s) nesta iteração\n")
            
            # Avança base enquanto há confirmações na sequência
            while base < total_pacotes and confirmados[base]:
                base += 1
                
        print("[CLIENTE] Todos os pacotes foram enviados!")

    else:  # GBN
        print(f"[CLIENTE] Iniciando Go-Back-N. Janela: {janela} pacotes")
        comeco_envio = 0
        tentativas = 0
        max_tentativas = 3
        
        while comeco_envio < len(arrPacotes):
            tentativas += 1
            if tentativas > max_tentativas:
                print("[CLIENTE] Máximo de tentativas excedido!")
                break
            
            # Verifica se é a última janela (pode ser incompleta)
            eh_ultima_janela = (comeco_envio + janela) >= len(arrPacotes)
            
            # Envia uma janela
            resposta = enviar_lote(comeco_envio, janela, arrPacotes, cliente_socket)
            
            # Se é última janela, pode ter timeout (esperando ACK que nunca vem para janela incompleta)
            # Nesse caso, simplismo enviar END
            if eh_ultima_janela and resposta is None:
                print(f"[CLIENTE] Última janela (incompleta) enviada. Enviando END...")
                enviar_linha(cliente_socket, "END")
                comeco_envio = len(arrPacotes)  # Marca como completo
                break
            
            if resposta is None:
                # Timeout - retransmite a mesma janela
                print(f"[CLIENTE] Timeout, retransmitindo a janela...")
                tentativas += 1
                continue
            
            if resposta.startswith("ACK"):
                # Janela confirmada, avança
                seq_confirmado = int(resposta.split()[-1])
                novo_comeco = seq_confirmado // 4  # Converte seq a índice
                
                if novo_comeco > comeco_envio:
                    comeco_envio = novo_comeco
                    tentativas = 0  # Reset contador de tentativas
                    print(f"[CLIENTE] Progresso: agora nos índices {comeco_envio}+")
                else:
                    # Sem progresso, tenta novamente
                    tentativas += 1
            
            elif resposta.startswith("NACK"):
                # NACK - retransmite a janela desde o ponto do NACK
                nack_seq = int(resposta.split()[-1])
                comeco_envio = nack_seq // 4  # Converte seq a índice
                tentativas = 0
                print(f"[CLIENTE] Retransmitindo a partir do índice {comeco_envio}")
        
        print("[CLIENTE] Todos os pacotes foram enviados!")
        

    # depois de todos os pacotes terem sido enviados, envia uma mensagem de fim
    enviar_linha(cliente_socket, "END")
    print(f"[CLIENTE] Enviei mensagem de fim: END")
    
    try:
        data = cliente_socket.recv(1024)
        resposta = data.decode("utf-8").strip()
        print(f"[CLIENTE] Recebi a mensagem do servidor: {resposta}")
        
        # fecha o socket
        if "END" in resposta or "ACK" in resposta:
            cliente_socket.close()
            print("conexão encerrada com sucesso!")
        else:
            cliente_socket.close()
            print("conexão encerrada")
    except Exception as e:
        print(f"[CLIENTE] Erro ao receber resposta final: {e}")
        cliente_socket.close()

if __name__ == "__main__":
    main()


