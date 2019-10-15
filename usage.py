from pathlib import Path

from syntactic_analysis import analyze_constituency


in_dir = Path("input")
out_dir = Path("output")
analyze_constituency(
    in_dir, out_dir, header_sheets=1, write_all=False, translate_tree='bo_en'
)
