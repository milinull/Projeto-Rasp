import sys
import numpy as np
import sounddevice as sd

# Códigos de cor ANSI para o terminal
VERDE = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"
RESET = "\033[0m"  # Volta para a cor padrão do terminal


def callback(indata, frames, time, status):
    # Calcula o volume
    volume = np.linalg.norm(indata) * 10

    # Limita o tamanho máximo da barra em 50 para não quebrar a linha
    tamanho_barra = min(int(volume), 50)

    # Define a cor baseada na intensidade
    if tamanho_barra < 25:
        cor = VERDE
    elif tamanho_barra < 40:
        cor = AMARELO
    else:
        cor = VERMELHO

    # Cria a barra com o caractere de bloco sólido
    caractere = "█"
    barra = caractere * tamanho_barra

    # Monta a string final
    # \033[?25l oculta o cursor
    # Utilizamos sys.stdout.write e flush para uma atualização mais limpa que o print
    sys.stdout.write(f"\r\033[?25l[{cor}{barra:<50}{RESET}] {volume:05.2f} ")
    sys.stdout.flush()


try:
    with sd.InputStream(device=21, channels=1, samplerate=48000, callback=callback):
        print("Ouvindo... (Pressione Enter para parar)")
        input()
finally:
    # Garante que o cursor volte a aparecer quando o programa terminar ou der erro
    # \033[?25h mostra o cursor novamente
    sys.stdout.write("\033[?25h\n")
