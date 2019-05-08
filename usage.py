from pathlib import Path

from syntactic_analysis import analyze_constituency


def main(in_dir, out_dir, write_pdfs=True):
    # ensure the in and out folders exist
    if not in_dir.is_dir():
        in_dir.mkdir(exist_ok=True)
    if not out_dir.is_dir():
        out_dir.mkdir(exist_ok=True)

    for csv in in_dir.glob('*.tsv'):
        # read the tsv file in a single block
        content = csv.read_text(encoding='utf-8-sig')

        # analyse
        tree, version_trees, output = analyze_constituency(content)

        if write_pdfs:
            tree.build_pdf(Path(out_dir / f'{csv.stem}.pdf'))
            for num, v in enumerate(version_trees):
                v.build_pdf(Path(out_dir / f'{csv.stem}_version{num+1}.pdf'))

        # write the output
        out_file = out_dir / (csv.stem + '.txt')
        out_file.write_text(output, encoding='utf-8-sig')


in_dir = Path('input')
out_dir = Path('output')
main(in_dir, out_dir)
