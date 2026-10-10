from pathlib import Path

base = Path(__file__).resolve().parent
source = (base / 'warehouse_stage5_completo.py').read_text(encoding='utf-8')
source = source.replace('LIGHT_EMISSION_STRENGTH = 4.0', '''LIGHT_EMISSION_STRENGTH = 9.0
LED_EMISSION_COLOR = (1.0, 0.035, 0.32, 1.0)
LED_LIGHT_COLOR = (1.0, 0.065, 0.36)''')
source = source.replace('emission.inputs["Color"].default_value = (1.0, 0.94, 0.84, 1.0)',
                        'emission.inputs["Color"].default_value = LED_EMISSION_COLOR')
source = source.replace('mat.diffuse_color = (1.0, 0.94, 0.84, 1.0)',
                        'mat.diffuse_color = LED_EMISSION_COLOR')
source = source.replace('data.color = (1.0, 0.94, 0.86)', 'data.color = LED_LIGHT_COLOR')
source = source.replace('AREA_LIGHT_ENERGY = 260.0', 'AREA_LIGHT_ENERGY = 120.0')
adjustment = (base / 'aplicar_luz_rosa.py').read_text(encoding='utf-8')
start = adjustment.index('def configure_led_glow(')
end = adjustment.index("\n\nif __name__ == '__main__':", start)
source += '\n\n# Pink LED bloom and visible diffuser edges.\nLED_AREA_ENERGY = AREA_LIGHT_ENERGY\nLED_EMISSION_STRENGTH = LIGHT_EMISSION_STRENGTH\n' + adjustment[start:end] + '\n\napply_pink_leds()\n'
compile(source, 'warehouse_stage5_luz_rosa.py', 'exec')
for folder in (base, Path(r'C:\Users\erons\Downloads')):
    (folder / 'warehouse_stage5_luz_rosa.py').write_text(source, encoding='utf-8')
    if folder != base:
        (folder / 'aplicar_luz_rosa.py').write_text(adjustment, encoding='utf-8')
print('Standalone pink Stage 5 and in-place adjustment ready.')
