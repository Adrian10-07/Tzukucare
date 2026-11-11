# views/alert_styles.py
"""Aspecto de cada alerta extra en pantalla: textos, colores y pixel art del cachorro.

Solo afecta a la interfaz. Qué sonidos se detectan y qué se envía a Firebase sigue
definido en config.ALERTAS_EXTRA.
"""

# Segundos que la tarjeta de estado muestra la alerta antes de volver al estado normal
DURACION_ALERTA_SEG = 12

# Colores extra de los iconos (se suman a los del cachorro, ver dog_sprites.COLORES)
COLORES_EXTRA = {
    'O': (255, 140, 40),    # naranja
    'G': (150, 160, 170),   # gris humo
    'D': (90, 100, 110),    # gris oscuro
    'C': (150, 215, 245),   # celeste cristal
    'N': (40, 90, 170),     # azul
    'V': (124, 108, 240),   # violeta
    'S': (210, 220, 228),   # plata
}

# ---------- Iconos (8x8) que aparecen en una burbuja junto al cachorro ----------
ICONOS = {
    "disparo": [  # estallido
        ["...Y....", ".Y.Y.Y..", "..YOOY..", "YYORROYY", "..YOOY..", ".Y.Y.Y..", "...Y....", "........"],
        ["Y..Y..Y.", ".YYOYY..", ".YORROY.", "YORRRROY", ".YORROY.", ".YYOYY..", "Y..Y..Y.", "........"],
    ],
    "cristal": [  # vidrio roto
        ["KKKKKKKK", "KCCKCCCK", "KCCCKCCK", "KCKCCKCK", "KKCCCCKK", "KCCKCCCK", "KKKKKKKK", "........"],
        ["KKKKKKKK", "KCCKCCCK", "KCCCKCCK", "KCKCCKCK", "KKCC.CKK", "KCC..C.K", "KKK.K.KK", "..C...C."],
    ],
    "humo": [  # llama con humo
        [".GG.GG..", "GGGGGGG.", "..GGG...", "...R....", "..RYR...", ".ROYOR..", ".RYYYR..", "..RRR..."],
        ["..GG.GG.", ".GGGGGGG", "...GGG..", "....R...", "...RYR..", "..ROYR..", ".RYYYOR.", "..RRRR.."],
    ],
    "sirena": [  # baliza
        ["Y......Y", ".Y.RR.Y.", "...RRR..", "..RRWRR.", "..RRRRR.", ".DDDDDDD", ".DDDDDDD", "........"],
        ["........", "....RR..", "...RRR..", "..RRWRR.", "..RRRRR.", ".DDDDDDD", ".DDDDDDD", "........"],
    ],
    "explosion": [  # nube de explosión
        ["..GGGG..", ".GOOOOG.", "GOYYYYOG", ".GOOOOG.", "...RR...", "...RR...", "..ROOR..", ".RRRRRR."],
        [".GGGGGG.", "GOOOOOOG", "OYYWWYYO", "GOOOOOOG", "..RRRR..", "...RR...", ".ROOOOR.", "RRRRRRRR"],
    ],
    "gritos": [  # bocadillo con !!
        ["KKKKKKK.", "KWWWWWWK", "KWRWRWWK", "KWRWRWWK", "KWWWWWWK", "KWRWRWWK", "KKWKKKK.", "..K....."],
        [".KKKKKKK", "KWWWWWWK", "KWWRWRWK", "KWWRWRWK", "KWWWWWWK", "KWWRWRWK", ".KKKKWKK", "......K."],
    ],
    "bebe": [  # biberón
        ["...PP...", "...PP...", "..SSSS..", "..WCCW..", "..WCCW..", "..WWWW..", "..WWWW..", "...WW..."],
        ["...PP...", "..PPPP..", "..SSSS..", "..WWWW..", "..WCCW..", "..WCCW..", "..WWWW..", "...WW..."],
    ],
    "coche": [  # coche con luces
        ["...YY...", "..VVVV..", ".VCVVCV.", "VVVVVVVV", "VVVVVVVV", ".KK..KK.", "........", "........"],
        ["Y..YY..Y", "..VVVV..", ".VCVVCV.", "YVVVVVVY", "VVVVVVVV", ".KK..KK.", "........", "........"],
    ],
}

# ---------- Estilo de cada alerta ----------
# sonido: nombre corto para "Sonido detectado" | titulo: texto de la píldora | descripcion: texto bajo la píldora
# colores: (fondo píldora, texto píldora, fondo perrito, borde tarjeta)
# poses: dos cabezas de dog_sprites que se alternan | temblor: el cachorro tiembla
ESTILOS_ALERTA = {
    "disparo": {
        "sonido": "Disparos",
        "titulo": "¡DISPAROS!",
        "descripcion": "Posibles disparos cerca. Alerta enviada.",
        "colores": ("#E5484D", "#FFFFFF", "#FFE4E4", "#E5484D"),
        "poses": ("asustado", "asustado_2"), "temblor": True,
    },
    "cristal": {
        "sonido": "Cristal roto",
        "titulo": "¡CRISTAL ROTO!",
        "descripcion": "Un cristal se rompió. Alerta enviada.",
        "colores": ("#2F8FCF", "#FFFFFF", "#E1F1FB", "#2F8FCF"),
        "poses": ("asustado", "ladrando"), "temblor": False,
    },
    "humo": {
        "sonido": "Alarma de humo",
        "titulo": "¡ALARMA DE HUMO!",
        "descripcion": "Suena una alarma de incendio. Alerta enviada.",
        "colores": ("#E8702A", "#FFFFFF", "#FFE9DA", "#E8702A"),
        "poses": ("ladrando", "atento"), "temblor": False,
    },
    "sirena": {
        "sonido": "Sirena",
        "titulo": "¡SIRENA!",
        "descripcion": "Sirena o alerta sísmica. Alerta enviada.",
        "colores": ("#D9435E", "#FFFFFF", "#FDE3E8", "#D9435E"),
        "poses": ("aullando", "atento"), "temblor": False,
    },
    "explosion": {
        "sonido": "Explosión",
        "titulo": "¡EXPLOSIÓN!",
        "descripcion": "Posible explosión cerca. Alerta enviada.",
        "colores": ("#B8430E", "#FFFFFF", "#FFE7D6", "#B8430E"),
        "poses": ("asustado", "asustado_2"), "temblor": True,
    },
    "gritos": {
        "sonido": "Gritos",
        "titulo": "GRITOS",
        "descripcion": "Se escuchan gritos. Aviso enviado.",
        "colores": ("#F2A93B", "#1F3A4D", "#FFF1D6", "#F2A93B"),
        "poses": ("atento", "ladrando"), "temblor": False,
    },
    "bebe": {
        "sonido": "Llanto de bebé",
        "titulo": "LLANTO DE BEBÉ",
        "descripcion": "Un bebé está llorando. Aviso enviado.",
        "colores": ("#D9649A", "#FFFFFF", "#FDE7F0", "#D9649A"),
        "poses": ("preocupado", "atento"), "temblor": False,
    },
    "coche": {
        "sonido": "Alarma de coche",
        "titulo": "ALARMA DE COCHE",
        "descripcion": "Suena una alarma de coche. Aviso enviado.",
        "colores": ("#6C5CE0", "#FFFFFF", "#ECE9FE", "#6C5CE0"),
        "poses": ("ladrando", "atento"), "temblor": False,
    },
}

