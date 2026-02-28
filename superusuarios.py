# superusuarios.py
# -----------------

# Lista fija de superusuarios (emails)
SUPERUSUARIOS = {
    "gustavofoschi@gmail.com": {
        "rol": "superadmin",
        "nombre": "Gustavo",
        "nivel": 100
    },
    "agustina@foschi.com": {
        "rol": "admin",
        "nombre": "Agustina",
        "nivel": 80
    },
    "belen@foschi.com": {
        "rol": "admin",
        "nombre": "Belén",
        "nivel": 80
    },
    "lukasfoschi123@gmail.com": {
        "rol": "admin",
        "nombre": "Antonella",
        "nivel": 80
    },
    "guadarenata@icloud.com": {
        "rol": "admin",
        "nombre": "Guada",
        "nivel": 80
    }
}

def es_superusuario(email):
    if not email:
        return False
    return email.lower() in SUPERUSUARIOS

def obtener_superusuario(email):
    return SUPERUSUARIOS.get(email.lower())

def rol_superusuario(email):
    data = obtener_superusuario(email)
    return data["rol"] if data else None

def nivel_superusuario(email):
    data = obtener_superusuario(email)
    return data["nivel"] if data else 0

