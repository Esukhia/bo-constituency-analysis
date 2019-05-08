from pathlib import Path

from syntactic_analysis import analyze_constituency
from syntactic_analysis.analysis import check_tree


def test_parsed_sentences():
    in_file = 'input/test_processed.tsv'
    content = Path(in_file).read_text()
    tree, version_trees, output = analyze_constituency(content)
    Path('output/test_processed.txt').write_text(output)


def test_check_tree():
    tree = [['[མིང་ཚོགས།', ']', '', '[མིང་ཚོགས།', '', '', ']', '', '[མིང་ཚོགས།', '', '', '', ']',
           '[བྱ་ཚོགས།]', '', '[བྱ་ཚོགས།', ']', '']]
    res = check_tree(tree)
    assert not res

    tree = [['[མིང་ཚོགས།', '', '[མིང་ཚོགས།', '', '', ']']]
    res = check_tree(tree)
    assert ['[མིང་ཚོགས།, , [མིང་ཚོགས།, , , ]'] == res

    tree = [['མིང་ཚོགས།', '', '[མིང་ཚོགས།', '', '', ']']]
    res = check_tree(tree)
    assert ['མིང་ཚོགས།, , [མིང་ཚོགས།, , , ]'] == res

    tree = [['[མིང་ཚོགས]།', '', '[མིང་ཚོགས།', '', '', ']']]
    res = check_tree(tree)
    assert ['[མིང་ཚོགས]།, , [མིང་ཚོགས།, , , ]'] == res
