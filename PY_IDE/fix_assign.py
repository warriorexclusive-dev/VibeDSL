import io

P = "compiler/compile.py"
Q = chr(39)
L = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")

L[378] = "# The ASSIGN mark is what `=` compiles to, so an already-compiled line carries"
L[379] = "# no `=` at all. Matching only the source spelling made local_names() see a"
L[380] = "# DIFFERENT set on a second pass - every name it was protecting had vanished -"
L[381] = "# so the words it had shielded compiled anyway and the legend grew 62 -> 123."
L[382] = "# Accepting both spellings is what makes a compile idempotent."
L[383] = "ASSIGN = " + Q + "[=\\u2a72]" + Q
L[384] = ("RX_LOCAL_ID = re.compile(" + Q + r"\bid[=⩲]" + chr(34)
         + r"([^" + chr(34) + r"]+)" + chr(34) + Q + ")")
L[385] = ("RX_LOCAL_NAME = re.compile(" + Q + r"\bname[=⩲]" + chr(34)
          + r"([^" + chr(34) + r"]+)" + chr(34) + Q + ")")

io.open(P, "w", encoding="utf-8", newline="").write("\n".join(L))
print("  строки 379-386 переписаны")
for i in range(378, 387):
    print("   %4d| %s" % (i + 1, L[i][:88]))
