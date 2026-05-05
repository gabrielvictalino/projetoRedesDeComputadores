# Projeto de Infraestrutura de Comunicação

## Descrição

Este projeto implementa uma infraestrutura básica de comunicação entre um cliente e um servidor utilizando sockets TCP/IP em Python. O objetivo é demonstrar os conceitos fundamentais de programação de redes aprendidos em sala de aula.

## Arquitetura

O projeto segue o modelo cliente-servidor com duas aplicações principais:

- **Servidor** (servidor.py): Aguarda por conexões de clientes na porta 5000 (localhost), recebe mensagens de handshake e responde com uma confirmação.
- **Cliente** (cliente.py): Conecta-se ao servidor, realiza um handshake negociando o modo de operação e tamanho máximo de mensagens, e fecha a conexão após receber a resposta.

## Funcionalidades

### Handshake

O cliente inicia a comunicação com um handshake contendo:

- **Modo de operação**: Go-Back-N (GBN)
- **Tamanho máximo de mensagem**: 100 bytes

Formato da mensagem: `HANDSHAKE;modo=GBN;maxlen=100`

### Comunicação

- Estabelecimento de conexão TCP entre cliente e servidor
- Troca de mensagens com confirmação
- Encerramento adequado da conexão

## Tecnologias Utilizadas

- **Python**
- **Socket API (biblioteca importada)**
- **IPv4 (AF_INET)**
- **TCP (SOCK_STREAM)**

## Como Executar

### 1. Iniciar o Servidor

```
python servidor.py
```

Output esperado:

```
servidor iniciado em 127.0.0.1:5000
```

### 2. Executar o Cliente (abrir outro terminal)

```
python cliente.py
```

Output esperado:

```
conectado ao servidor em 127.0.0.1:5000
[CLIENTE] Enviei para o servidor: HANDSHAKE;modo=GBN;maxlen=100
[CLIENTE] Recebi do servidor: Mensagem recebida com sucesso!
conexão encerrada
```

## Estrutura do Projeto

```
projetoRedesDeComputadores/
├── cliente.py        # Cliente TCP/IP
├── servidor.py       # Servidor TCP/IP
└── README.md         # Este arquivo
```

## Conceitos de Redes Implementados

- **Socket**: Interface para comunicação em rede
- **Bind**: Associação de um socket a um endereço IP e porta
- **Listen/Accept**: Servidor aguardando e aceitando conexões
- **Handshake**: (aperto de mãos) Negociação de parâmetros entre cliente e servidor
- **Codificação UTF-8**: Conversão entre caracteres e bytes
- **Go-Back-N (GBN)**: Protocolo de controle de fluxo para transmissão confiável

## Relatório de uso de IA

### Entrega 1
O uso da IA foi restrito somente a pesquisas sobre a biblioteca "socket", sendo essa indispensável para o desenvolvimento da aplicação.

### Entrega 2
Utilizamos a IA para:
1) debuggar
2) entender conceitos relacionados ao conteúdo exposto em sala e como aplicá-los no projeto
3) estruturação e organização de código