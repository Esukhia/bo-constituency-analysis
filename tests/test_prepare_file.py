from syntactic_analysis import prepare_file


def test_create_files():
    in_file = 'input/test.txt'
    out_dir = 'output/'
    prepare_file(in_file, out_dir)