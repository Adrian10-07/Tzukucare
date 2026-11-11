# views/dog_sprites.py
"""Pixel art del cachorro (24x24). Cada pose es una cabeza distinta sobre el mismo cuerpo."""

# Colores por letra ('.' es transparente)
COLORES = {
    'K': (26, 26, 26),      # contorno
    'B': (140, 80, 40),     # cuerpo
    'L': (200, 130, 70),    # cabeza
    'M': (95, 52, 25),      # oreja
    'T': (240, 200, 150),   # hocico y pecho
    'W': (245, 245, 245),   # brillo del ojo y patas
    'R': (220, 50, 50),     # collar y boca
    'Y': (255, 200, 0),     # placa del collar
    'P': (255, 150, 180),   # lengua
    'C': (150, 215, 245),   # lágrima / sudor
}

# Cuerpo sentado (filas 13-23): collar rojo con placa, pecho crema, cola y patas blancas
CUERPO = [
 ".....KRRYRRRBBBBBK....KK",
 ".....KBBYBBBBBBBBBK..KBK",
 ".....KTTBBBBBBBBBBBK.KBK",
 ".....KTTTBBBBBBBBBBBKBK.",
 ".....KTTTBBKBBBBBBBBBK..",
 ".....KTTTBBKBBBBBBBBBK..",
 ".....KTTBBBKBBBKKKKBBK..",
 ".....KBBBKBKBBKBBBBKBK..",
 ".....KBBBKBKBKBBBBBBBK..",
 "....KWWWKWWWKKKWWWWWK...",
 "....KKKKKKKKK..KKKKKK...",
]

# Cabezas (filas 0-12), mirando a la izquierda
CABEZAS = {}
CABEZAS["sentado"] = [
 "........................",
 "........................",
 "......KKKKKK............",
 ".....KLLLLLLKK..........",
 "....KLLLLLLKMMK.........",
 "...KLLLLLLKMMMMK........",
 "...KLKWLLLKMMMMK........",
 "...KLKKLLLKMMMMK........",
 ".KKLLLLLLLKMMMK.........",
 "KKKTTLLLLLLKMMK.........",
 "KKTTTTLLLLLLKK..........",
 ".KKKKTLLLLLLLK..........",
 "....KKLLLLLLLLKKK.......",
]
CABEZAS["parpadeo"] = CABEZAS["sentado"][:6] + [
 "...KLLLLLLKMMMMK........",
 "...KLKKLLLKMMMMK........",
] + CABEZAS["sentado"][8:]
CABEZAS["ladrando"] = [
 "........................",
 "..........KK............",
 "......KKKKMMK...........",
 ".....KLLLLKMMK..........",
 "....KLLLLLKMMK..........",
 "...KLLLLLLLKMK..........",
 "...KLKWLLLLLKK..........",
 "...KLKKLLLLLLK..........",
 ".KKLLLLLLLLLLK..........",
 "KKKTTLLLLLLLLK..........",
 "KKTTTKKLLLLLLK..........",
 ".KRRPPKLLLLLLLK.........",
 "..KKKKKLLLLLLLLKKK......",
]
CABEZAS["atento"] = [
 "........................",
 "..........KK............",
 "......KKKKMMK...........",
 ".....KLLLLKMMK..........",
 "....KLLLLLKMMK..........",
 "...KLLLLLLLKMK..........",
 "...KLKWLLLLLKK..........",
 "...KLKKLLLLLLK..........",
 ".KKLLLLLLLLLLK..........",
 "KKKTTLLLLLLLLK..........",
 "KKTTTTLLLLLLLK..........",
 ".KKKKTLLLLLLLK..........",
 "....KKLLLLLLLLKKK.......",
]
CABEZAS["asustado"] = [
 "........................",
 "........................",
 "......KKKKKK............",
 ".....KLLLLLLKKKKKK......",
 "....KLLLLLLKMMMMMMK.....",
 "...KLLLLLLLLKKKKKK......",
 "...KWWWLLLLLLK..........",
 "...KWKWLLLLLLK..........",
 ".KKKWWWLLLLLLK..........",
 "KKKTTLLLLLLLLK..........",
 "KKTTTTLLLLLLLK..........",
 ".KKTKKTLLLLLLK..........",
 "....KKLLLLLLLLKKK.......",
]
CABEZAS["asustado_2"] = [r[:20] + "...." for r in CABEZAS["asustado"]]
CABEZAS["asustado_2"][1] = "...............C........"
CABEZAS["asustado_2"][2] = "......KKKKKK..CCC......."
CABEZAS["asustado_2"][3] = ".....KLLLLLLKKKCKK......"
CABEZAS["aullando"] = [
 "....KK..................",
 "...KTKK....KK...........",
 "..KRRTLK..KMMK..........",
 "..KRTTLLKKKMMK..........",
 "...KTLLLLLKMMK..........",
 "...KLLKKLLLKMK..........",
 "...KLLLLLLLLKK..........",
 "...KLLLLLLLLLK..........",
 "....KLLLLLLLLK..........",
 ".....KLLLLLLLK..........",
 ".....KLLLLLLLK..........",
 ".....KLLLLLLLK..........",
 ".....KLLLLLLLLKKK.......",
]
CABEZAS["preocupado"] = [
 "........................",
 "........................",
 "......KKKKKK............",
 ".....KLLLLLLKK..........",
 "....KLKKLLLLLKK.........",
 "...KLLLLLLLLKMMK........",
 "...KLKWLLLLKMMMK........",
 "...KLKKLLLLKMMMK........",
 ".KKLLCLLLLLKMMMK........",
 "KKKTTCLLLLLKMMMK........",
 "KKTTTTLLLLLLKMMK........",
 ".KKKKTLLLLLLLKK.........",
 "....KKLLLLLLLLKKK.......",
]
# Ladrando con líneas de movimiento amarillas
CABEZAS["alarma"] = list(CABEZAS["ladrando"])
for fila, col in ((1, 2), (2, 1), (4, 0), (4, 1), (6, 1)):
    r = CABEZAS["alarma"][fila]; CABEZAS["alarma"][fila] = r[:col] + "Y" + r[col + 1:]


def sprite(pose: str) -> list:
    """Cuadrícula 24x24 del cachorro con la cabeza indicada."""
    return CABEZAS[pose] + CUERPO
