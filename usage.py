from pathlib import Path

from syntactic_analysis import dir_analyze_constituency


in_dir = Path('input')
out_dir = Path('output')
dir_analyze_constituency(in_dir, out_dir)
