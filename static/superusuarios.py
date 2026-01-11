# superusuarios.py

SUPERUSUARIOS = {
    "gustavofoschi@gmail.com",
    "agustina@tucorreo.com",
    "belen@tucorreo.com",
    "antonella@tucorreo.com",
}

def es_superusuario(email):
    if not email:
        return False
    return email.lower() in SUPERUSUARIOS
