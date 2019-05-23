from pathlib import Path

in_path = '../output/བུ་ཡུག་རྩུབ་ཀྱི་བྱམས་བརྩེ།'
for f in Path(in_path).glob('*.txt'):
    content = f.read_text(encoding='utf-8-sig')
    print()