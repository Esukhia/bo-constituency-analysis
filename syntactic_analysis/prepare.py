from pathlib import Path
import csv

from pybo import BoPipeline, BoTokenizer
import xlsxwriter

from .textunits import sentencify


tok = BoTokenizer('GMD')
pos_eqvl = {'NUM': 'གྲངས་ཚིག', 'punct': 'རྟགས་ཤད།', 'DET': 'བརྣན་ཚིག', 'ADP': 'སྦྱོར་ཚིག', 'syl': '???', 'num': 'གྲངས་ཚིག',
            'VERB': 'བྱ་ཚིག', 'PART': 'གྲོགས་ཚིག', 'ADV': 'བསྣན་ཚིག', 'OOV': '???', 'SCONJ': 'ལྟོས་བཅས་སྦྲེལ་ཚིག', 'NOUN': 'མིང་ཚིག',
            'ADJ': 'རྒྱན་ཚིག', 'OTHER': '???', 'PROPN': 'སྦྱར་མིང་།', 'PRON': 'ཚབ་ཚིག'}


def tokenize(string):
    return tok.tokenize(string)


def tokenize_lines(string):
    out = []
    for line in string.split('\n'):
        out.append(tok.tokenize(line))
    return out


def prepare_sentences(sentences):
    print()
    return [(len(sent), sent) for sent in sentences]


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
        pos.append(pos_eqvl[token.pos])

    return words, pos


def prepare_file(in_file, out_dir, xlsx=True):
    in_file, out_dir = Path(in_file), Path(out_dir)
    # pipeline = BoPipeline('dummy',
    #                       tokenize,
    #                       sentencify,
    #                       prepare_analysis)

    pipeline = BoPipeline('dummy',
                          tokenize_lines,
                          prepare_sentences,
                          prepare_analysis)

    content = in_file.read_text(encoding='utf-8-sig')
    sheets = pipeline.pipe_str(content)
    if xlsx:
        workbook = xlsxwriter.Workbook(in_file.stem + '.xlsx')
        for num, sheet in enumerate(sheets):
            worksheet = workbook.add_worksheet(str(num))
            for r, row in enumerate(sheet):
                for c, content in enumerate(row):
                    worksheet.write_string(r, c, content)
        workbook.close()

    else:
        for num, sheet in enumerate(sheets):
            out_file = out_dir / f'{in_file.stem}_{num + 1}.csv'
            with out_file.open('w') as csvfile:
                writer = csv.writer(csvfile)
                for line in sheet:
                    writer.writerow(line)


if __name__ == '__main__':
    prepare_file('../བུ་ཡུག་རྩུབ་ཀྱི་བྱམས་བརྩེ།.txt', '../input')