# superusuarios.py
# -----------------

# Lista fija de superusuarios (emails)
SUPERUSUARIOS = {
    "gustavofoschi@gmail.com": {
        "rol": "superadmin",
        "nombre": "Gustavo",
        "nivel": 100
    },
    "libre@gmail.com": {
        "rol": "admin",
        "nombre": "libre",
        "nivel": 80
    },
    "mariabelenfoschi10@gmail.com": {
        "rol": "admin",
        "nombre": "Belén",
        "nivel": 80
    },
     "marianoesp1234@gmail.com": {
        "rol": "admin",
        "nombre": "Mariano",
        "nivel": 80
    },
    "lukasfoschi123@gmail.com": {
        "rol": "admin",
        "nombre": "Antonella",
        "nivel": 80
    },
     "libre@gmail.com": {
        "rol": "admin",
        "nombre": "libre",
        "nivel": 80
    },
    "jeremiasgimenez253@gmail.com": {
        "rol": "admin",
        "nombre": "Jeremias",
        "nivel": 80
    },
    "valentinaborras5@gmail.com": {
        "rol": "admin",
        "nombre": "Valentina",
        "nivel": 80
    },
    "javodambrosi@hotmail.com": {
        "rol": "admin",
        "nombre": "Javo",
        "nivel": 80
    },
    "libre3@gmail.com": {
        "rol": "admin",
        "nombre": "Mariano",
        "nivel": 80
    },
    "mlauraaraujo40@gmail.com": {
        "rol": "admin",
        "nombre": "Lura Araujo",
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




