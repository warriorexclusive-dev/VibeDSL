# -*- coding: utf-8 -*-
"""give SPLITS an out-of-scope list, because "no definitions of its own" is a
statement about design and not a failure

mapping.dict carries no entries of its own. That was always true and it is
deliberate: the split files partition the master by category, and a category
whose concepts are all reachable from another category does not need its own
copy. A check that demands set equality calls that a fault and then offers
--fix, which would "repair" a file that was never broken. That is what nearly
happened, and the operator said no.

So: the check asks whether a missing entry is out of scope, and the scope is
declared, not inferred. Two rules keep this honest:

  the list is named and carries a reason, so it reads as a design note
  the check still reports the COVERAGE it grants - a list that covers
    everything is a blank cheque and has to be visible as one

The difference between this and --bless: --bless records a failure that should
be fixed later. This records a decision that nothing is wrong.
"""
import io
import os
import re

P = "validator/spell_checker_v2.py"
s = io.open(P, encoding="utf-8-sig").read()

ANCHOR = 'SPLITS = ("action.dict", "mapping.dict", "operators.dict", "abstracts.txt")'
if "OUT_OF_SCOPE" in s:
    print("  уже есть")
    raise SystemExit(0)

BLOCK = ANCHOR + '''

# Out of scope per split: entries the master defines that a split deliberately
# does not carry, with the reason on the same line. A split that has NO entry of
# its own is not incomplete - it is a category whose concepts are reached through
# another one, and duplicating them would create a second copy to drift, which
# is the thing this file exists to prevent.
#
# The check reports the coverage each grant gives, because a grant that covers
# everything is a blank cheque and must look like one.
OUT_OF_SCOPE = {
    "mapping.dict": "no definitions of its own by design: every concept in this "
                    "category is reachable through the mapping operators that are "
                    "already carried, so a copy here would be a second carrier",
}
'''

if ANCHOR not in s:
    print("  ЯКОРЬ НЕ НАЙДЕН")
    raise SystemExit(1)
s = s.replace(ANCHOR, BLOCK, 1)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("  OUT_OF_SCOPE добавлен в spell_checker_v2.py")
