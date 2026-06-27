import sounddevice as sd

# RECONHECIMENTO DE DISPOSITIVOS DE SOM DO SISTEMA

for i, dev in enumerate(sd.query_devices()):
    if "USB PnP Sound Device" in dev["name"]:
        print(f"\nÍndice: {i}")
        print(dev)

print("")
print("------------------##------------------")
print("")

for i, device in enumerate(sd.query_devices()):
    print(f"{i}: {device['name']}")
