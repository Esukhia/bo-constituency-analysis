import csv
from pathlib import Path
import re

from nltk.tree import ParentedTree


def analyze_constituency(raw_rows):
    rows = list(csv.reader(raw_rows))
    rows = strip_empty_rows(rows)
    raw_tree, raw_versions = parse_rows(rows)
    tree = parse_tree(raw_tree, raw_versions[0])
    version_trees = generate_subtrees(raw_versions, tree)
    rules = [str(r) for r in tree.productions() if "'" not in str(r)]
    vocab = [str(r) for r in tree.productions() if "'" in str(r)]
    extra_rules = []
    for n, t in enumerate(version_trees):
        for rule in t.productions():
            str_rule = str(rule)
            str_rule = str_rule.replace('--extra' + str(n + 1), '')
            if "'" not in str_rule and str_rule not in rules and str_rule not in extra_rules:
                extra_rules.append(str_rule)

    rules = '\n'.join(rules)
    extra_rules = '\n'.join(extra_rules)

    mshang_tree = generate_mshang_link(tree)
    mshang_extra = '\n'.join([generate_mshang_link(t) for t in version_trees])

    vocab = '\n'.join(vocab)

    return f'{mshang_tree}\n\nextra trees:\n{mshang_extra}\n\nrules:\n{rules}\n\nextra rules:\n{extra_rules}\n\nvocab:\n{vocab}'


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

    to_parse = ' '.join([' '.join(col) for col in tree]).replace('-', '')
    tree = BoTree.fromstring(to_parse.replace('[', '(').replace(']', ')'))

    return tree


def generate_mshang_link(tree):
    str_tree = re.sub(r'\s+', ' ', str(tree).replace('\n', ''))
    str_tree = str_tree.replace('(', '[').replace(')', ']')
    return 'http://mshang.ca/syntree/?i=' + str_tree.replace('_', ' ').replace(' ', '%20')


def generate_subtrees(simplified_sentences, full_tree):
    subtrees = []
    for n, sent in enumerate(simplified_sentences):
        new_tree = full_tree.copy(deep=True)
        new_tree.set_label(f'{new_tree.label()}--extra{n}')
        # delete leafs
        to_del = list(reversed([num for num, word in enumerate(sent) if not word]))
        if not to_del:
            continue
        for num in to_del:
            postn = new_tree.leaf_treeposition(num)
            # go up deleting nodes until there are left siblings (we are starting
            while not (new_tree[postn[:-1]].left_sibling() or new_tree[postn[:-1]].right_sibling()):
                postn = postn[:-1]

            del new_tree[postn[:-1]]

        subtrees.append(new_tree)

    return subtrees


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


class BoTree(ParentedTree):
    def print_svg(self, sentence=None, highlight=(), out_file='out.svg'):
        """
        Pretty-print this tree as .svg
        For explanation of the arguments, see the documentation for
        `nltk.treeprettyprinter.TreePrettyPrinter`.
        """
        from nltk.treeprettyprinter import TreePrettyPrinter

        svg = TreePrettyPrinter(self, sentence, highlight).svg()
        Path(out_file).write_text(svg)
