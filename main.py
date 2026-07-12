import sys
import time
import asyncio
import threading
import numpy as np
import sounddevice as sd

from Scripts.ciclos_audio import CiclosAudio
from Scripts.websocket_server import ServidorWebSocket
from Scripts.db_client import ClienteTimescaleDB

# Configurações do Microfone e Áudio
DEVICE_ID = 21
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
banco_dados = ClienteTimescaleDB()

# Passa o DEVICE_ID para o cliente do banco de dados
banco_dados = ClienteTimescaleDB(id_microfone=DEVICE_ID)

# Variáveis de Controle para o Banco de Dados
estado_anterior = "green"
tempo_inicio_estado = time.time()
ultimo_envio_baseline = time.time()
soma_volume_baseline = 0.0
ciclos_baseline = 0

# Rastreia o pico de volume de forma independente
pico_estado_atual = 0.0


def callback(
    indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags
) -> None:
    """
    Função chamada automaticamente pela biblioteca sounddevice
    sempre que um novo bloco de áudio (chunk) estiver disponível.
    """
    global volume_suavizado, pico_estado_atual
    global estado_anterior, tempo_inicio_estado
    global ultimo_envio_baseline, soma_volume_baseline, ciclos_baseline

    if status:
        print(status, file=sys.stderr)

    # Amplifica e calcula RMS
    sinal_amplificado = np.clip(indata * DIGITAL_GAIN, -1.0, 1.0)
    rms = np.sqrt(np.mean(sinal_amplificado**2))

    if rms < NOISE_GATE:
        rms = 0.0

    volume_bruto = rms * 100

    # Rastreia o maior volume registrado durante este estado atual
    pico_estado_atual = max(pico_estado_atual, volume_bruto)

    # Suaviza o volume
    if volume_bruto > volume_suavizado:
        volume_suavizado = (volume_suavizado * ATTACK) + (volume_bruto * (1 - ATTACK))
    else:
        volume_suavizado = (volume_suavizado * RELEASE) + (volume_bruto * (1 - RELEASE))

    # Define se alguém está falando e pega o estado (cor) atual
    status_evento = audio.processar(volume_bruto)
    estado_atual = audio.estado_websocket

    # Atualiza o WebSocket (Frontend)
    ws_server.atualizar_estado(estado_atual)

    # Lógica de integração com o banco de dados
    agora = time.time()

    #  Captura de Eventos (Mudança de Estado para Amarelo/Vermelho)
    if estado_atual != estado_anterior:
        duracao = agora - tempo_inicio_estado

        # Se acabou de sair de um estado de alerta, salva o evento
        if estado_anterior in ["yellow", "red"]:
            pico_para_salvar = pico_estado_atual

            # Envia para o banco em uma Thread separada (não trava o áudio)
            threading.Thread(
                target=banco_dados.registrar_evento,
                args=(estado_anterior.upper(), pico_para_salvar, duracao),
                daemon=True,
            ).start()

        # Reseta o cronômetro para o novo estado
        estado_anterior = estado_atual
        tempo_inicio_estado = agora

        # Reseta o pico para começar a medir o volume do novo estado
        pico_estado_atual = volume_bruto

    # Lógica do Baseline (O pulso Verde)
    if estado_atual == "green":
        soma_volume_baseline += volume_bruto
        ciclos_baseline += 1

        # Se passou 1 minuto (60 segundos) no verde, envia a média
        if (agora - ultimo_envio_baseline) >= 60.0:
            volume_medio = (
                soma_volume_baseline / ciclos_baseline if ciclos_baseline > 0 else 0
            )

            # Envia o baseline em uma Thread separada
            threading.Thread(
                target=banco_dados.registrar_baseline, args=(volume_medio,), daemon=True
            ).start()

            # Zera os contadores para o próximo minuto
            ultimo_envio_baseline = agora
            soma_volume_baseline = 0.0
            ciclos_baseline = 0

    # Barra visual do terminal (Opcional, deixei comentado como no seu)
    # tamanho_barra = min(int(volume_suavizado), MAX_BAR_LENGTH)
    # barra = "#" * tamanho_barra
    # print(f"\r{status_evento} [{barra:<{MAX_BAR_LENGTH}}] {volume_suavizado:05.2f} (WS: {estado_atual})", end="", flush=True)


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
