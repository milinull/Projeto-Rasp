# Tests\dispositivos.py
import sounddevice as sd

print("RECONHECIMENTO DE DISPOSITIVOS DE ENTRADA (COMPLETO)")
print("------------------##------------------\n")

lista_final = []

# Varre a lista iterando sobre as informações de cada hardware
for i, dev in enumerate(sd.query_devices()):

    # Filtra apenas os equipamentos que têm canais de entrada (microfones)
    if dev["max_input_channels"] > 0:
        nome = dev["name"]
        delay = dev.get("default_low_input_latency", 999.0)
        lista_final.append({"id": i, "nome": nome, "delay": delay})

# Exibe o resultado mostrando o índice exato para usar no main.py
for info in lista_final:
    print(f"Índice: {info['id']:02d} | Delay: {info['delay']:.4f}s | {info['nome']}")

print("\n------------------##------------------")
print(f"Total de canais de entrada encontrados: {len(lista_final)}")
