import io

P = "compiler/compile.py"
L = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
Q = chr(34)

L[385] = "RX_LOCAL_ABS = re.compile(" + Q.replace(Q, "") + r"r'abstract(?::\w+)?\"([^\"]+)\"'" + ")"
L.insert(386, "")
L.insert(387, "def local_names(lines):")
L.insert(388, "    " + Q.replace(Q, "") + "every identifier this spec claims, lowercased" + Q.replace(Q, ""))
L.insert(389, "    out = set()")
io.open(P, "w", encoding="utf-8", newline="").write("\n".join(L))
for i in range(383, 396):
    print("   %4d| %s" % (i + 1, L[i][:88]))
