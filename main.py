import sys
import asyncio
import numpy as np
import sounddevice as sd

from Scripts.ciclos_audio import CiclosAudio
from Scripts.websocket_server import ServidorWebSocket

# Configurações do Microfone e Áudio
DEVICE_ID = 18
SAMPLE_RATE = 48000
CHANNELS = 1
BLOCK_SIZE = 1440

# Configurações de Processamento de Som
NOISE_GATE = 0.001
DIGITAL_GAIN = 5.0
ATTACK = 0.1
RELEASE = 0.9
MAX_BAR_LENGTH = 50

# Variáveis globais do módulo main
volume_suavizado = 0.0
audio = CiclosAudio()
ws_server = ServidorWebSocket()


def callback(indata: np.ndarray, frames: int, time, status: sd.CallbackFlags) -> None:
    """
    Função chamada automaticamente pela biblioteca sounddevice
    sempre que um novo bloco de áudio (chunk) estiver disponível.
    """
    global volume_suavizado

    # Exibe erros na captura de áudio, se houver
    if status:
        print(status, file=sys.stderr)

    # Amplifica o sinal de áudio e garante que não passe dos limites (-1.0 a 1.0)
    sinal_amplificado = np.clip(indata * DIGITAL_GAIN, -1.0, 1.0)

    # Calcula o volume médio do bloco de áudio (RMS)
    rms = np.sqrt(np.mean(sinal_amplificado**2))

    # Aplica um "portão de ruído": ignora sons muito baixos (ruído de fundo)
    if rms < NOISE_GATE:
        rms = 0.0

    # Converte o volume para uma escala mais fácil de ler (0 a 100)
    volume_bruto = rms * 100

    # Suaviza o volume para que as mudanças não sejam bruscas (Efeito Attack/Release)
    if volume_bruto > volume_suavizado:
        volume_suavizado = (volume_suavizado * ATTACK) + (volume_bruto * (1 - ATTACK))
    else:
        volume_suavizado = (volume_suavizado * RELEASE) + (volume_bruto * (1 - RELEASE))

    # Passa o volume bruto para a classe de lógica decidir se alguém está falando
    status_evento = audio.processar(volume_bruto)

    # Ponte de comunicação: Passa o estado de cor atualizado para o servidor WebSocket
    ws_server.atualizar_estado(audio.estado_websocket)

    # Cria uma barra de visualização em texto para o terminal (tamanho máximo definido)
    tamanho_barra = min(int(volume_suavizado), MAX_BAR_LENGTH)
    barra = "#" * tamanho_barra

    # Linha de log do terminal comentada para não poluir a tela
    # print(
    #     f"\r{status_evento} [{barra:<{MAX_BAR_LENGTH}}] {volume_suavizado:05.2f} (WS: {audio.estado_websocket})",
    #     end="",
    #     flush=True,
    # )


async def main_async() -> None:
    """
    Função principal assíncrona. Inicia o servidor WebSocket e a
    escuta do microfone simultaneamente.
    """
    # print(f"Iniciando escuta no dispositivo {DEVICE_ID}...")
    # print("Servidor WebSocket rodando em ws://localhost:8765")
    # print("Pressione [Ctrl+C] para sair")

    try:
        # Inicia o servidor WebSocket para rodar em background
        servidor = await ws_server.iniciar_servidor()

        # Configura e abre o canal de escuta do microfone
        stream = sd.InputStream(
            device=DEVICE_ID,
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            callback=callback,
            blocksize=BLOCK_SIZE,
        )

        # Mantém o microfone e o servidor WebSocket ativos
        with stream:
            async with servidor:
                # Mantém o programa rodando indefinidamente (aguardando um evento futuro que nunca chega)
                await asyncio.Future()

    except Exception as e:
        # Captura e exibe qualquer erro inesperado durante a execução
        print(f"\n[ERRO] Falha: {e}")


if __name__ == "__main__":
    """
    Ponto de entrada do script. Roda a função main_async dentro de um loop asyncio.
    """
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        # Encerra o programa silenciosamente caso o usuário aperte Ctrl+C
        # print("\nPrograma encerrado pelo usuário (Ctrl+C).")
        pass
