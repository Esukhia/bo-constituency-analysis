from pathlib import Path
import csv

from pybo import BoPipeline, BoTokenizer

from .textunits import sentencify


def prepare_analysis(sentences):
    LINES = 10  # amount of copies of the sentence for the simplification
    TREE = 10  # amount of lines left for constructing the tree

    return [generate_sheet(sent, TREE, LINES) for sent in sentences]


def generate_sheet(sent, lines_above, amount_sentence):
    sheet = []
    words, pos = extract_words_n_pos(sent)
    sheet.extend([[''] * len(words)] * lines_above)
    sheet.append(pos)
    sheet.append(words)
    sheet.extend([[''] + words[1:]] * amount_sentence)
    return sheet


def extract_words_n_pos(sent):
    words, pos = ['W'], ['P']
    for token in sent[1]:
        words.append(token.content)
        pos.append(token.pos)

    return words, pos


def prepare_file(in_file, out_dir):
    tok = BoTokenizer('GMD')

    in_file, out_dir = Path(in_file), Path(out_dir)
    pipeline = BoPipeline('dummy',
                          tok.tokenize,
                          sentencify,
                          prepare_analysis)

    content = in_file.read_text(encoding='utf-8-sig')
    sheets = pipeline.pipe_str(content)
    for num, sheet in enumerate(sheets):
        out_file = out_dir / f'{in_file.stem}_{num + 1}.csv'
        with out_file.open('w') as csvfile:
            writer = csv.writer(csvfile)
            for line in sheet:
                writer.writerow(line)
