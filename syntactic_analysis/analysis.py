import csv
from html import escape
from collections import defaultdict
import re

from nltk.tree import ParentedTree, Tree
from nltk.treeprettyprinter import TreePrettyPrinter


def analyze_constituency(raw_content):
    rows = list(csv.reader(raw_content.split('\n'), delimiter='\t'))
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
    mshang_extra = '\n\n'.join([generate_mshang_link(t) for t in version_trees])

    vocab = '\n'.join(vocab)

    return f'{mshang_tree}\n\nextra trees:\n{mshang_extra}\n\nrules:\n{rules}\n\nextra rules:\n{extra_rules}\n\nvocab:\n{vocab}'


def generate_trees(raw_content):
    rows = list(csv.reader(raw_content.split('\n'), delimiter='\t'))
    rows = strip_empty_rows(rows)
    raw_tree, raw_versions = parse_rows(rows)
    tree = parse_tree(raw_tree, raw_versions[0])
    version_trees = generate_subtrees(raw_versions, tree)
    return tree, version_trees


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
    parented_tree = ParentedTree(0, []).convert(full_tree)
    subtrees = []
    for n, sent in enumerate(simplified_sentences):
        new_tree = parented_tree.copy(deep=True)
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

        subtrees.append(BoTree(0, []).convert(new_tree))

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


class BoTreePrettyPrinter(TreePrettyPrinter):
    def svg(self, nodecolor='blue', leafcolor='red', funccolor='green', font='Noto Sans Tibetan'):
        """
        :return: SVG representation of a tree.
        """
        fontsize = 12
        hscale = 40
        vscale = 25
        hstart = vstart = 20
        width = max(col for _, col in self.coords.values())
        height = max(row for row, _ in self.coords.values())
        result = [
            '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
            'width="%dem" height="%dem" viewBox="%d %d %d %d">'
            % (
                width * 3,
                height * 2.5,
                -hstart,
                -vstart,
                width * hscale + 3 * hstart,
                height * vscale + 3 * vstart,
            )
        ]

        children = defaultdict(set)
        for n in self.nodes:
            if n:
                children[self.edges[n]].add(n)

        # horizontal branches from nodes to children
        for node in self.nodes:
            if not children[node]:
                continue
            y, x = self.coords[node]
            x *= hscale
            y *= vscale
            x += hstart
            y += vstart + fontsize // 2
            childx = [self.coords[c][1] for c in children[node]]
            xmin = hstart + hscale * min(childx)
            xmax = hstart + hscale * max(childx)
            result.append(
                '\t<polyline style="stroke:black; stroke-width:1; fill:none;" '
                'points="%g,%g %g,%g" />' % (xmin, y, xmax, y)
            )
            result.append(
                '\t<polyline style="stroke:black; stroke-width:1; fill:none;" '
                'points="%g,%g %g,%g" />' % (x, y, x, y - fontsize // 3)
            )

        # vertical branches from children to parents
        for child, parent in self.edges.items():
            y, _ = self.coords[parent]
            y *= vscale
            y += vstart + fontsize // 2
            childy, childx = self.coords[child]
            childx *= hscale
            childy *= vscale
            childx += hstart
            childy += vstart - fontsize
            result += [
                '\t<polyline style="stroke:white; stroke-width:10; fill:none;"'
                ' points="%g,%g %g,%g" />' % (childx, childy, childx, y + 5),
                '\t<polyline style="stroke:black; stroke-width:1; fill:none;"'
                ' points="%g,%g %g,%g" />' % (childx, childy, childx, y),
            ]

        # write nodes with coordinates
        for n, (row, column) in self.coords.items():
            node = self.nodes[n]
            x = column * hscale + hstart
            y = row * vscale + vstart
            if n in self.highlight:
                color = nodecolor if isinstance(node, Tree) else leafcolor
                if isinstance(node, Tree) and node.label().startswith('-'):
                    color = funccolor
            else:
                color = 'black'
            result += [
                '\t<text style="text-anchor: middle; fill: %s; '
                'font-size: %dpx; font-family: %s" x="%g" y="%g">%s</text>'
                % (
                    color,
                    fontsize,
                    font,
                    x,
                    y,
                    escape(node.label() if isinstance(node, Tree) else node),
                )
            ]

        result += ['</svg>']
        return '\n'.join(result)


class BoTree(Tree):
    def print_svg(self, sentence=None, highlight=()):
        """
        Pretty-print this tree as .svg
        For explanation of the arguments, see the documentation for
        `nltk.treeprettyprinter.TreePrettyPrinter`.
        """
        return BoTreePrettyPrinter(self, sentence, highlight).svg()

    def print_latex(self):
        qtree = self.pformat_latex_qtree()
        qtree = re.sub(r'([^a-zA-Z\[\].\s\\_]+)', r'\\bo{\1}', qtree)
        header = """\\documentclass{article}
\\usepackage{polyglossia}
\\usepackage{fontspec} 
\\usepackage{tikz-qtree}

\\newfontfamily\\tibetanfont{[Monlam_Uni_OuChan2.ttf]}
\\newcommand{\\bo}[1]{\\tibetanfont{#1}}

\\begin{document}

\\hoffset=-1in
\\voffset=-1in
\\setbox0\hbox{
"""
        footer = """
        }
\\pdfpageheight=\\dimexpr\\ht0+\\dp0\\relax
\\pdfpagewidth=\\wd0
\\shipout\\box0


\\stop"""
        document = header + qtree + footer
        document = document.replace('\\', '\\')
        return document
