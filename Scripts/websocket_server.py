import asyncio
import websockets
import json
import sounddevice as sd


class ServidorWebSocket:
    """
    Servidor WebSocket bidirecional: envia telemetria de áudio e
    responde a comandos do painel de configurações.
    """

    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.estado_atual = "green"
        self.volume_atual = 0.0
        self.novo_mic_id = None
        self.ganho_adicional = 0.0

    def atualizar_estado(self, novo_estado: str, volume: float = 0.0):
        self.estado_atual = novo_estado
        self.volume_atual = volume

    async def enviar_telemetria(self, websocket):
        """
        Task contínua que envia o estado e o volume em tempo real para a barra do HTML.
        """
        try:
            while True:
                payload = json.dumps(
                    {"estado": self.estado_atual, "volume": self.volume_atual}
                )
                await websocket.send(payload)
                await asyncio.sleep(0.05)  # Atualiza 20x por segundo
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            # Se der qualquer erro na montagem do JSON ou envio, avisa no terminal!
            print(f"\n[ERRO NO WEBSOCKET] Falha ao enviar dados para o HTML: {e}")

    async def ws_handler(self, websocket):
        """Lida com comandos recebidos da interface HTML."""
        task_envio = asyncio.create_task(self.enviar_telemetria(websocket))

        try:
            async for message in websocket:
                dados = json.loads(message)

                # Incorporando a lógica avançada do dispositivos.py
                if dados.get("comando") == "listar_microfones":
                    mics_unicos = {}

                    # Varre a lista iterando sobre as informações de cada hardware[cite: 4]
                    for i, dev in enumerate(sd.query_devices()):

                        # Filtra apenas os equipamentos que têm canais de entrada[cite: 10]
                        if dev["max_input_channels"] > 0:
                            nome = dev["name"]
                            # Busca a latência (delay). Caso o hardware não informe, assumimos um valor alto (999) para despriorizar
                            delay = dev.get("default_low_input_latency", 999.0)

                            # Lógica para evitar duplicatas:
                            # Se o nome já existe na lista, só substitui se o novo tiver um delay menor
                            if nome in mics_unicos:
                                if delay < mics_unicos[nome]["delay"]:
                                    mics_unicos[nome] = {
                                        "id": i,
                                        "nome": nome,
                                        "delay": delay,
                                    }
                            else:
                                # Se é a primeira vez vendo esse nome, adiciona na lista
                                mics_unicos[nome] = {
                                    "id": i,
                                    "nome": nome,
                                    "delay": delay,
                                }

                    # Remonta a lista em formato de array para enviar de volta ao HTML
                    lista_mics = [
                        {"id": info["id"], "nome": info["nome"]}
                        for info in mics_unicos.values()
                    ]

                    await websocket.send(json.dumps({"microfones": lista_mics}))

                elif dados.get("comando") == "trocar_microfone":
                    self.novo_mic_id = int(dados.get("id"))

                elif dados.get("comando") == "alterar_ganho":
                    self.ganho_adicional = float(dados.get("valor"))

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            task_envio.cancel()

    async def iniciar_servidor(self):
        return websockets.serve(self.ws_handler, self.host, self.port)
