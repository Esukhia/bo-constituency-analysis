import csv
from pathlib import Path
import json
import re


def analyze_constituency(raw_rows):
    rows = list(csv.reader(raw_rows))
    rows = strip_empty_rows(rows)
    raw_tree, raw_versions = parse_rows(rows)
    tree = parse_tree(raw_tree, raw_versions[0])
    print()


def parse_tree(raw_tree, words):
    sanity = check_tree(raw_tree[:-1])
    if sanity:
        errors = '\n\t'.join(sanity)
        raise SyntaxError(f'Errors in following rows:\n\t{errors}\n')

    tree = [[raw_tree[line][col] for line in range(len(raw_tree))] for col in range(len(raw_tree[0]))]
    for num, col in enumerate(tree):
        new_line = [el for el in col if el]
        for mun, el in enumerate(new_line):
            if ']' in el and mun < len(new_line) - 1:
                count = el.count(']')
                new_line[mun] = new_line[mun].replace(']', '')
                new_line[mun + 1] += ']' * count
        new_line = [el for el in new_line if el]
        tree[num] = new_line

    # add words to tree
    for n, word in enumerate(words):
        word = word.replace(' ', '_')
        pos = tree[n][-1]
        if pos.endswith(']'):
            count = pos.count(']')
            pos = pos[:-count] + ' -' + word + ']' * count
        else:
            pos = pos + ' -' + word

        tree[n][-1] = pos

    # add boxes to final nodes for mshang
    for n, col in enumerate(tree):
        for m, cell in enumerate(col):
            if not cell.startswith('['):
                tree[n][m] = '[' + tree[n][m] + ']'

    print()
    to_parse = ' '.join([' '.join(col) for col in tree])
    mshang = 'http://mshang.ca/syntree/?i=' + to_parse.replace('-', '').replace('_', ' ').replace(' ', '%20')

    # list structure
    to_parse = re.sub(r'([^\[\] ]+)', r'"\1"', to_parse)
    to_parse = to_parse.replace('" "', '", "')
    to_parse = to_parse.replace(' [', ', [')
    struct = json.loads(to_parse)

    # to trie structure
    # get max level:
    depth = 0
    for col in tree:
        depth = len(col) + 1 if depth < len(col) + 1 else depth


    tree_struct = {}

    print()





def strip_empty_rows(rows):
    i = 0
    while i < len(rows):
        if not ''.join(rows[i]):
            del rows[i]
        else:
            i += 1

    return rows


def check_tree(tree):
    errors = []
    for num, row in enumerate(tree):
        state = None
        for cell in row:
            if cell and cell != ']':
                if not cell.startswith('['):
                    errors.append(num)
                if state and state != 'end':
                    errors.append(num)
                if ']' in cell:
                    if cell.endswith(']'):
                        state = 'end'
                    else:
                        errors.append(num)
                        state = 'begin'
                else:
                    state = 'begin'
            elif cell == ']':
                if not state == 'begin':
                    errors.append(num)
                state = 'end'
        if state != 'end':
            errors.append(num)

    errors = sorted(list(set(errors)))

    return [', '.join(tree[e]) for e in errors]


def parse_rows(rows):
    # indentify POS and Words rows
    p, w = -1, -1
    for num, row in enumerate(rows):
        if 'P' == row[0]:
            p = num
        if 'W' == row[0]:
            w = num

    assert p != -1 and w != -1  # ensure we have the POS and Words lines

    # delete 1st column
    rows = [row[1:] for row in rows]

    # rows belonging to: the tree, the versions of the sentence
    return rows[:p + 1], rows[w:]


if __name__ == '__main__':
    in_file = '../tests/input/test_processed.csv'
    content = Path(in_file).read_text().split('\n')
    analyze_constituency(content)