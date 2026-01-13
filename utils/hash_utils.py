#utils/hash_utils
import json
import hashlib
import copy


def calcular_hash_datos(datos):
    """
    Calcula el hash MD5 de los datos del sistema.
    Misma lógica que el servidor para garantizar consistencia.
    """

    def normalizar_para_hash(obj):
        """Normaliza cualquier objeto para cálculo de hash consistente"""
        if isinstance(obj, dict):
            return {k: normalizar_para_hash(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            try:
                if obj and isinstance(obj[0], dict):
                    return sorted(
                        [normalizar_para_hash(item) for item in obj],
                        key=lambda x: json.dumps(x, sort_keys=True),
                    )
                else:
                    return sorted([normalizar_para_hash(item) for item in obj])
            except:
                return [normalizar_para_hash(item) for item in obj]
        elif isinstance(obj, str):
            return obj
        else:
            return obj

    datos_normalizados = copy.deepcopy(datos)

    # Eliminar fecha de ejecución (no afecta el hash)
    datos_normalizados.pop("Fecha Ejecución", None)

    # Eliminar campos de fecha/hora de antivirus (no afectan el hash)
    for av_key in ["Información de Segurmática", "Información de Kaspersky"]:
        if av_key in datos_normalizados and isinstance(
            datos_normalizados[av_key], dict
        ):
            av_data = datos_normalizados[av_key]
            for key in list(av_data.keys()):
                key_lower = key.lower()
                if any(
                    palabra in key_lower
                    for palabra in [
                        "fecha",
                        "hora",
                        "actualiz",
                        "expir",
                        "time",
                        "last",
                        "última",
                    ]
                ):
                    av_data.pop(key, None)

    datos_para_hash = normalizar_para_hash(datos_normalizados)

    datos_str = json.dumps(datos_para_hash, sort_keys=True, ensure_ascii=False)

    return hashlib.md5(datos_str.encode("utf-8")).hexdigest()
