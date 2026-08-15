import unicodedata

def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

SINONIMOS = {
    'first_name': ['nombre', 'nombres', 'nombre completo', 'nombes', 'nombrs',
                   'apellido', 'apellidos', 'first_name', 'firstname', 'first name',
                   'nombre y apellido', 'nombres y apellidos', 'nombe', 'nomre'],
    'email': ['email', 'correo', 'correos', 'correo electronico',
              'correo electrónico', 'mail', 'mails', 'emails', 'emial', 'maill'],
    'ci': ['ci', 'c.i', 'cedula', 'cedula', 'documento', 'identificacion',
           'identificacion', 'dni', 'carnet'],
    'telefono': ['telefono', 'telefono', 'telefonos', 'celular', 'telf',
                 'telfono', 'telefano', 'phone', 'cel'],
    'rol_nombre': ['rol', 'roles', 'cargo', 'tipo', 'perfil', 'rol_nombre'],
    'activo': ['activo', 'activos', 'estado', 'habilitado', 'activa'],
    'id': ['id', 'identificador', 'numero', 'numero', 'identificacion'],
}

available_cols = [
    {'key': 'id', 'label': 'ID'},
    {'key': 'first_name', 'label': 'Nombre Completo'},
    {'key': 'email', 'label': 'Email'},
    {'key': 'ci', 'label': 'CI'},
    {'key': 'telefono', 'label': 'Telefono'},
    {'key': 'rol_nombre', 'label': 'Rol'},
    {'key': 'activo', 'label': 'Activo'},
]

tests = [
    "quiero solo los nombres y email en orden alfabetico",
    "solo nombres y correos",
    "muestra email y telefono",
    "dame todo",
    "quiero el ci y el rol",
]

for prompt in tests:
    prompt_norm = normalizar(prompt)
    col_keys = {c.get('key') for c in available_cols}
    keys_detectadas = set()

    for canonical_key, variaciones in SINONIMOS.items():
        if canonical_key not in col_keys:
            continue
        for var in variaciones:
            if var in prompt_norm:
                keys_detectadas.add(canonical_key)
                break

    for col in available_cols:
        label_norm = normalizar(col.get('label', ''))
        key_norm = normalizar(col.get('key', ''))
        if label_norm in prompt_norm or key_norm in prompt_norm:
            keys_detectadas.add(col.get('key'))

    print(f"Prompt: '{prompt}'")
    print(f"  => Columnas: {sorted(keys_detectadas) if keys_detectadas else '[TODAS]'}\n")
