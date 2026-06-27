import asyncio
import websockets
import json


class ServidorWebSocket:
    """
    Classe responsável por gerenciar um servidor WebSocket simples.
    """

    def __init__(self, host="localhost", port=8765):
        """
        Inicializa o servidor com o endereço (host), a porta e um estado padrão.
        """
        self.host = host
        self.port = port
        self.estado_atual = "green"  # Define o estado inicial do servidor

    def atualizar_estado(self, novo_estado: str):
        """
        Atualiza o estado interno que o loop assíncrono vai ler e enviar.
        """
        self.estado_atual = novo_estado

    async def ws_handler(self, websocket):
        """
        Lida com a conexão de cada cliente. Monitora o estado atual e
        envia uma mensagem ao cliente sempre que houver uma mudança.
        """
        ultimo_estado_enviado = ""
        try:
            # Loop infinito para manter a conexão ativa e checando o estado
            while True:
                # Se o estado for diferente do último que enviamos, preparamos o envio
                if self.estado_atual != ultimo_estado_enviado:
                    # Converte o dicionário para uma string JSON
                    payload = json.dumps({"estado": self.estado_atual})

                    # Envia os dados para o cliente
                    await websocket.send(payload)

                    # Atualiza o controle para não enviar a mesma mensagem repetida
                    ultimo_estado_enviado = self.estado_atual

                # Pausa bem curta (50ms) para não sobrecarregar o processador (CPU)
                await asyncio.sleep(0.05)

        except websockets.exceptions.ConnectionClosed:
            # Se o cliente desconectar, encerra silenciosamente sem dar erro
            pass

    async def iniciar_servidor(self):
        """
        Inicia o servidor WebSocket para escutar novas conexões
        no host e porta configurados.
        """
        return websockets.serve(self.ws_handler, self.host, self.port)
