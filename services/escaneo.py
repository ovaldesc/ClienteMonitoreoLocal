#services/escaneo.py
import socket
from concurrent.futures import ThreadPoolExecutor


def escanear_puertos(ip, start_port=1, end_port=1024):
    """Escanea puertos de forma eficiente usando ThreadPoolExecutor"""
    open_ports = []

    # Lista de puertos comunes para priorizar
    common_ports = [
        21,
        22,
        23,
        25,
        53,
        80,
        110,
        135,
        139,
        143,
        443,
        993,
        995,
        3389,
        5432,
        3306,
    ]

    def scan(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)  # Timeout más corto para mayor velocidad
                result = sock.connect_ex((ip, port))
                if result == 0:
                    try:
                        service_name = socket.getservbyport(port)
                    except:
                        service_name = "Unknown"
                    return (port, service_name)
        except:
            pass
        return None

    # Escanear puertos comunes primero
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(scan, port) for port in common_ports]
        for future in futures:
            result = future.result()
            if result:
                open_ports.append(result)

    # Si no se encontraron puertos comunes, escanear rango completo
    if not open_ports:
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(scan, port) for port in range(start_port, end_port + 1)
            ]
            for future in futures:
                result = future.result()
                if result:
                    open_ports.append(result)

    return sorted(open_ports, key=lambda x: x[0])
