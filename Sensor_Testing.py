import requests

# URL del servidor donde corre tu código con Flask
LAPTOP_URL = "http://192.168.1.126:5000/disparar"   # cambia si es remoto


def main():
    print("Enviando señal al sensor...")
    try:
        r = requests.post(LAPTOP_URL, timeout=10)

        print("Respuesta del servidor:")
        print(r.status_code, r.text)

    except Exception as e:
        print("Error al enviar señal:", e)

    print("Simulación finalizada.")


if __name__ == "__main__":
    main()
