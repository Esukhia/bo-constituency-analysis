from pathlib import Path

from syntactic_analysis import analyze_constituency


in_dir = Path('input')
out_dir = Path('output')
if not in_dir.is_dir():
    in_dir.mkdir(exist_ok=True)
if not out_dir.is_dir():
    out_dir.mkdir(exist_ok=True)

for csv in in_dir.glob('*.csv'):
    content = csv.read_text(encoding='utf-8-sig')

    output = analyze_constituency(content)

    out_file = out_dir / (csv.stem + '.txt')
    out_file.write_text(output, encoding='utf-8-sig')
