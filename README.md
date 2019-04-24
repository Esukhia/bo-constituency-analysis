# bo-constituency-analysis
Constituency analysis of Tibetan sentences done by natives

## `prepare_file()`
Makes use of pybo's BoPipeline to segment generate ready to be parsed .csv files

Can easily be adapted to take as input any format of POS tagged sentences.

## `analyze_constituency()` 
Takes as input a csv file as formatted by `prepare_file()` and assumes it has been manually processed.

Outputs 
 - a file containing a mshang link to the syntax tree found in the .csv
 - extra trees derived from the simplified sentences
 - a list of rewrite rules from the main syntax tree
 - a list of the extra rules
 - a list of the vocabulary used in the sentence together with their POS
 
The output contains all the information required by Context Free Grammars.
