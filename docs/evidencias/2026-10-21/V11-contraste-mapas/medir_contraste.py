"""
V11 (SES-154) -- calculo de contraste WCAG real sobre fondos reales muestreados
del mapa claro de la app (OpenFreeMap "liberty"), no colores inventados.

Los tres fondos de abajo son pixeles reales muestreados de una captura de
pantalla real de la app (navegador real, tema claro, capa de datos apagada)
con PIL, en zonas representativas sin marcadores encima:
  - tan/parque:  (226,211,156)
  - crema:       (245,233,221)
  - lavanda:     (235,230,234)

Los colores de los elementos son los reales de frontend/src/constants.js
(NIVELES, NIVELES_INSEGURIDAD_COLOR) y de MapaMotoSafe.jsx (ruta/corredor).
"""

def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(rgb):
    r, g, b = rgb
    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)


def contraste(c1, c2):
    l1, l2 = luminancia(c1), luminancia(c2)
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend(fg, alpha, bg):
    return tuple(round(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))


FONDOS = {
    'tan/parque (muestreado real)': (226, 211, 156),
    'crema (muestreado real)': (245, 233, 221),
    'lavanda (muestreado real)': (235, 230, 234),
}

ELEMENTOS = {
    'ruta seleccionada #4FA8E8': '#4FA8E8',
    'ruta borde #0B1620 (ya existia)': '#0B1620',
    'siniestros bajo #3DDC84': '#3DDC84',
    'siniestros medio #FFD23F': '#FFD23F',
    'siniestros alto #FF8C42': '#FF8C42',
    'siniestros critico #FF3B3B': '#FF3B3B',
    'inseguridad bajo #D9A6FF': '#D9A6FF',
    'inseguridad medio #B266FF': '#B266FF',
    'inseguridad alto #9B30FF': '#9B30FF',
    'inseguridad critico #FF2E92': '#FF2E92',
}

print('=== ANTES (sin ningun contorno nuevo) ===')
for nombre_f, rgb_f in FONDOS.items():
    print(f'--- fondo: {nombre_f} ---')
    for nombre_e, hex_e in ELEMENTOS.items():
        c = contraste(hex_to_rgb(hex_e), rgb_f)
        print(f'  {nombre_e:34} ratio={c:.2f}  {"FALLA" if c < 3 else "ok"}')

print('\n=== DESPUES (V11): borde oscuro #0B1620 en hexagonos y corredores, tema claro ===')
borde = (11, 22, 32)
print('Hexagonos (borde fijo 0.55 de opacidad):')
for nombre_f, rgb_f in FONDOS.items():
    mezcla = blend(borde, 0.55, rgb_f)
    print(f'  {nombre_f:30} contraste_borde_vs_fondo={contraste(mezcla, rgb_f):.2f}')

print('Corredores (borde fijo 0.7 de opacidad, no escalado por nivel):')
for nombre_f, rgb_f in FONDOS.items():
    mezcla = blend(borde, 0.7, rgb_f)
    print(f'  {nombre_f:30} contraste_borde_vs_fondo={contraste(mezcla, rgb_f):.2f}')
