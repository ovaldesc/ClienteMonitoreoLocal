# utils/config_interactiva.py

def pedir_configuracion_inicial():
    print("\n=== CONFIGURACIÓN INICIAL ===")
    print("Esta es la primera vez que se ejecuta el cliente.")
    while True:
        servidor = input("Introduzca la IP del servidor al cual quiere enviar la informacion: ").strip()
        if servidor:
            servidor = 'http://' + servidor + ':5000'
            break
        print("La dirección del servidor no puede estar vacía.")

    print("\nFrecuencia de ejecución:")
    print("1. Cada X horas")
    print("2. Diariamente")
    print("3. Semanalmente")
    print("4. Mensualmente")
    while True:
        try:
            opcion = input("Seleccione una opción (1-4): ").strip()
            if opcion == "1":
                horas = int(input("¿Cada cuántas horas? (mínimo 1): "))
                if horas >= 1:
                    break
                else:
                    print("El valor debe ser >= 1.")
            elif opcion == "2":
                horas = 24
                break
            elif opcion == "3":
                horas = 168
                break
            elif opcion == "4":
                horas = 720
                break
            else:
                print("Opción inválida. Intente de nuevo.")
        except ValueError:
            print("Por favor, introduzca un número válido.")
    return servidor, horas