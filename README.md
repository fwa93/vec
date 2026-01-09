## Quick start
./vec.py --reference old_vers/emu-combined-species.tsv --test  TRANA/emu-combined-species.tsv --outdir results --tolerance 0.001
## Requirements
python
# Usage
This script is used to compare the results from emu combine-outputs. The purpose is to check if the resulting tables are the same between versions of expecially EMU.
The script can also be used to compare the results for TRANA down to the step of emu combine outputs.
Works for oth relative abundance and read counts. You should however not compare the percentage abundance difference between reports created with read counts and relative abundance since they will differ sligthly on the percentage difference. 
Optimally only compare reports created from read counts with read counts and relative abundance with relative abundance. 
```
# Help
./vec.py -h
```
