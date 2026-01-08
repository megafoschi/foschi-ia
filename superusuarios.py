# superusuarios.py

# superusuarios.py

SUPERUSUARIOS = {
    "gustavofoschi@gmail.com",
    "hija1@gmail.com",
    "hija2@gmail.com",
    "hija3@gmail.com"
}

def es_superusuario(email: str) -> bool:
    return email.lower() in SUPERUSUARIOS
