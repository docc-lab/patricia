#!/usr/bin/python
import sys
sys.path.insert(0, "/home/maniaa/patricia/library/restful_api")

import patricia


outfile = sys.argv[1]
print(outfile)
patricia.getAllObjectsJson(outfile)
