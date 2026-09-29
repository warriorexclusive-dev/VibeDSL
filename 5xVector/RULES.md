# RULES

Working folder. English only: the table is English, so a rule in any other
language has no address in it and blurs with the rest of the flood.

## Address

```
address   a byte offset, not a position in a list
field     4 glyphs = 16 bits
file      21 455 bytes, so 3 glyphs = 12 bits = 4 095 does not reach it
```

An address in a list forces a scan of the whole file. An address in bytes
points at one piece: seek, read three bytes, done. That is the rule "do not
load, open by offset" applied to the address itself. The address therefore means
nothing on its own, which is correct: it cannot be confused with a word,
because it is a place and not a name.

## Signs

```
field values   16, 0..F
●  U+25CF      separator in the address layer, one role only
⁕  U+2055      separator in the spec text, one role only
□  U+25A1      space between words
```

One sign, one role. A second role halves a sign's uniqueness, and its
uniqueness is its strength. Before a sign is introduced, ask two questions:
is it free, and is it booked.

## The word

```
3-3-tail      cut, and the tail stays
tail of 1     a letter of the alphabet, 26 of them, already present
tail of 2     a digraph, 390 of them, also present
cut of 3      gets an address
```

The tail is not a remainder. A one-letter tail is a letter, a two-letter tail is
a digraph, and neither is addressed. Type does not depend on length; the address
does. If null therefore never fires on a tail.

## The record

```
( object ):property:->result[hint]<form>
```

Left half addressed, right half as written. The arrow divides what was chosen
from what is wanted, and it is not checked because there is nothing to check it
against.

```
what      object
which     property
for what  result
purpose   hint
why       form
```

All five are always present. A conditional field would require knowing the part
of speech, and that is not available. So an inapplicable field stays empty, and
an empty field says so.

The frame is always present, holds a set, and a vector inside holds the
meaning. A bare value does not exist. An erased address does not break a
record, it changes one, so what is checkable is the number of separators and
not the field.

## If null

```
1  cut the word into 3-3-tail
2  check uniqueness
3  what is missing
4  write only that, last
```

Never substituted, never rounded, never skipped. A fabricated address exists
and therefore passes a lookup. The write is the last step, it writes only the
delta, and it is idempotent by construction, so there is nothing to roll back.

## Threshold

```
3    minimal
5    acceptable
15   habit
20   habit, and acceptance costs nothing after it
```

Twenty is not a number of checks. It is where an action stops being deliberate
and becomes automatic, like shifting a manual gearbox. A habit is verified once,
not twenty times. What is missing is either the address or the meaning, and
which one is not always determinable.

## Writing

```
check before write, never after
verify that a change took effect, then run
```

Writing first and checking after lost the embedding file twice in one evening.
Both times the source was deterministic and the file was rebuilt, and neither
time that was acceptable. All writes go through write_guard.py.

## What is not in here

```
the fifth field is never supplied and is always present
the reference is written by whoever defines acceptance
blur is declared, not derived
search complexity belongs to the task, and uniqueness does not depend on it
```

## Marks

Formatting only. These carry no address and sit outside the sixteen field
values, because a field value is a bit of an address and a formatting glyph
is not. Chosen with zero weight of verifiability.

| mark | code | glyph |
|---|---|---|
| `(` | U+25F0 | ◰ |
| `)` | U+25F1 | ◱ |
| `[` | U+25F2 | ◲ |
| `]` | U+25F3 | ◳ |
| `{` | U+25F4 | ◴ |
| `}` | U+25F5 | ◵ |
| `=` | U+25F6 | ◶ |
| `-` | U+25F7 | ◷ |
| `<` | U+25FA | ◺ |
| `>` | U+25FC | ◼ |
| `~` | U+2600 | ☀ |
| `|` | U+2605 | ★ |
| `/` | U+2606 | ☆ |
| `?` | U+2610 | ☐ |
| `^` | U+2611 | ☑ |
| `&` | U+2612 | ☒ |
| `%` | U+261B | ☛ |
| `$` | U+2620 | ☠ |
| `#` | U+2622 | ☢ |
| `@` | U+2630 | ☰ |
| `!` | U+263C | ☼ |
| `*` | U+2660 | ♠ |
| `_` | U+2665 | ♥ |
| `+` | U+2666 | ♦ |

## Dependency

`
▶◀(root)▶root◀(parent)

The parent is named explicitly, not by level and not by order, so the dependency
is visible in full: parent, then arrow, then root. Nothing has to be inferred
from indentation, and therefore nothing is lost when the indentation is not
seen.

`
not seeing spaces        not seeing indents       not seeing one coordinate
`

The third axis is the one that is invisible in the plane, and a space and an
indent are its trace. It does not need a third number. It needs a visible
indent, and there already is one.

Names inside the frames are addresses, exactly like object names. Every named
thing is addressed; nothing is named in words.

### Parts

```
▶◀        root element
(object)  an example of an object, a literal word, not the name
▶         arrow right, open tag
name      the real name, addressed, written in glyphs
◀         arrow left, close tag
(object)  an example of an object
```

The parenthesized words are illustrations, and the two of them are not required
to differ, because they are not roles but examples. Only the name between the
arrows is addressed. The examples are copied through untouched.

### One role, one writer

```
(object)          object syntax, a human writes it, ASCII
▶◀     root element and frame, a machine writes it
```

The brackets have one role and there is no second bracket glyph. FRAME_R and
FRAME_L are the root element and the frame, not a parent marker, and giving
them a second meaning is exactly the double booking that weakens a sign.

The bracket glyphs already exist: U+25F0 and U+25F1, in the Marks table,
assigned to ( and ). A human types ASCII and the compiler emits the glyphs,
so nothing new is introduced.

### Indent is a named parent

```
(root□element):element->example[to model]<view>
▶root□element◀
         - (child□element):element□or□other->example(toModel)<view>
```

```
line 1   the arrow is a carriage return, so the root is (root□element)
line 2   FRAME_R opens the parent, FRAME_L closes it, then - and the record
```

Depth is named, not counted. The root carries no name because it has no parent,
and the absence of the name is what marks it. A dash with no parent is half a
construct, and so is a parent with no dash. A record is a root and a parent and
is complete only with both.

The parser catches the leading indent of a new line, with or without the dash,
and joins the parent to the record.

### The indent is a visible space

```
▶root□element◀
□□□□- (child□element):element□or□other->example(toModel)<view>
```

An ASCII space inside a field is invisible, and an invisible indent is a lost
coordinate. The indent is therefore written with U+25A1, which is visible,
countable, and survives compilation.

So a human does type one glyph, and it is the visible space: words are ASCII,
the indent is U+25A1, and the machine writes the rest. Depth is both named by
the parent and counted by the □, and the count is the one that is visible.

### The space has two roles

```
a human       prints an ASCII space
the compiler  turns the space into U+25A1

leading, at the start of a line    the parent
any other                          the separator between words
```

The sign is the same in both roles, so the sign cannot tell them apart and does
not try. Position does, and this is how YAML already works: leading whitespace
is indent, inner whitespace separates. The compiler looks at where the space
is, never at what it is.

A human types ASCII. U+25A1 is the output, not the input.

### CRLF is the separator

```
\r\n     separates records, physically, not by a sign
a space immediately after \r\n    leading, the parent
any other space                     the separator between words
```

A space has no double role, and it never did. CRLF marks where a record begins,
so a space right after it is leading by position and not by convention, and the
other spaces in the record are between words.

```
record    ends at \r\n
parent    the leading space right after \r\n
words     the spaces further in
```

Three levels, separated physically, and none of them ambiguous. "At the start of
a line" is not a convention here, it is what is left after CRLF.

### The closing tag is the newline

```
(object):property->result[hint]<view>\r\n
                         ^ the closing tag is the carriage return
```

CRLF is not written freely by the author. The compiler emits it right after the
closing tag, so the end of a record is given by the tag and not by the hand
that wrote the record. A record cannot end in any other place, and the leading
space of the next record is unambiguous for the same reason: its predecessor
ended at a tag.

```
record    ends where the tag closes
parent    the leading space right after that \r\n
words     the spaces further in
```

This is what made the double role of a space disappear. The newline is not a
position in a text, it is the output of a closing tag.

### Parent tags

```
▶   opens the parent
◀   closes the parent
```

```
▶name◀
```

The two signs are a pair of tags around the parent's name, and that is their
whole use. They were written down inside Parts, and a later section then called
the same two signs the root element and the frame, which left the parent tags
unnamed as tags. One sign, one role, and the role that counts is the one in use.

A root has no parent, so it has no tags. The tags are what marks a record as
nested, and a record with no leading tags and no leading space is a root.

### Writing a dataset entry

The rules above say how to read a record. This is the write side, and it was
missing, and the first entry in dataset.jsonl shows what that costs:

```
the dataset said   three per field, 12 bits, 3655 used, 185 free
the compiler said  four per field, 16 bits, 3654 used, 186 free
```

Every one of those figures was typed by hand and every one of them was stale.

So a dataset entry carries no number a person wrote. A figure in a dataset is
taken from the compiler, and an entry that disagrees with the compiler is wrong
by construction and not by opinion. The compiler is the canon, and a dataset is
a record of what the compiler did, not a description of it.


### Signs of the record that had none

The form is decoded completely, so every sign in it has to exist. The
24 marks covered brackets and formatting and the colon was not among
them, which a fully decoded record could not survive.

| sign | code | glyph |
|---|---|---|
| `:` | U+2663 | ♣ |
| `.` | U+2668 | ♨ |
| `,` | U+2669 | ♩ |

### The address table file

```
name       englang.embedding
what       a table of addresses, nothing else
layout     entries joined by one separator, nothing else
one entry  a word, ASCII letters, no marks, no spaces
a size     1, 2 or 3 letters, because a word is not always longer
grows      at the end only, and only through if null
addresses  byte offsets, counted from the first byte of the file
```

The name is correct by purpose. The spelling was wrong and is fixed; the name was
always right and the code now agrees with it.

Why a byte offset and not an index: an index means reading the file to count
to the entry, and an offset means opening the file there. The file is 21 515
bytes and the last offset is 21 513, so 4 glyphs at 16 bits hold it with room
to spare, and the table can grow to about 65 000 bytes before a fifth glyph is
needed.

What the file is not: it is not a vocabulary, it is not a translation, and it
does not say what anything means. The English words in it are the keys and the
offsets are the only information it carries.

### The name

The name is correct by purpose and was right all along. It was used once for the
wrong object, in a message where two things had been mixed up, and that was one
message and not a concept. The word is not withdrawn.

The spelling was wrong. englang.embending is not a word, and it is now
englang.embedding. That was the whole of it.

### The assembly formula

```
3*x + tail
```

x pieces of three and a tail. That is the layout of a word in bytes, and it is
all it is. The address is one per word, and the layout and the address are two
different things, which is why this formula is a rule of writing and not of
reading. A reader that has this formula starts cutting words, and cutting is
not reading.

A tail of one is a letter of the alphabet and a tail of two is a digraph, and
both are vectors of their own with their own addresses, and neither is part of
the word's address.

### Every sign the compiler uses

The compiler refuses to start if it uses a sign the rules do not name.
This table is generated from the compiler, so a sign cannot be added to
one and forgotten in the other.

| role | code | glyph |
|---|---|---|
| the sixteen | U+25A6 | ▦ |
| the sixteen | U+25A3 | ▣ |
| the sixteen | U+25AD | ▭ |
| the sixteen | U+25AC | ▬ |
| the sixteen | U+25AF | ▯ |
| the sixteen | U+25AE | ▮ |
| the sixteen | U+25A2 | ▢ |
| the sixteen | U+21F2 | ⇲ |
| the sixteen | U+21F1 | ⇱ |
| the sixteen | U+21F5 | ⇵ |
| the sixteen | U+21F6 | ⇶ |
| the sixteen | U+25A4 | ▤ |
| the sixteen | U+25B0 | ▰ |
| the sixteen | U+25B1 | ▱ |
| the sixteen | U+25B2 | ▲ |
| the sixteen | U+25C9 | ◉ |
| separator | U+25CF | ● |
| visible space | U+25A1 | □ |
| opens the parent | U+25B6 | ▶ |
| closes the parent | U+25C0 | ◀ |
| mark '(' | U+25F0 | ◰ |
| mark ')' | U+25F1 | ◱ |
| mark '[' | U+25F2 | ◲ |
| mark ']' | U+25F3 | ◳ |
| mark '{' | U+25F4 | ◴ |
| mark '}' | U+25F5 | ◵ |
| mark '=' | U+25F6 | ◶ |
| mark '-' | U+25F7 | ◷ |
| mark '<' | U+25FA | ◺ |
| mark '>' | U+25FC | ◼ |
| mark '~' | U+2600 | ☀ |
| mark '|' | U+2605 | ★ |
| mark '/' | U+2606 | ☆ |
| mark '?' | U+2610 | ☐ |
| mark '^' | U+2611 | ☑ |
| mark '&' | U+2612 | ☒ |
| mark '%' | U+261B | ☛ |
| mark '$' | U+2620 | ☠ |
| mark '#' | U+2622 | ☢ |
| mark '@' | U+2630 | ☰ |
| mark '!' | U+263C | ☼ |
| mark '*' | U+2660 | ♠ |
| mark ';' | U+2662 | ♢ |
| mark ':' | U+2663 | ♣ |
| mark '_' | U+2665 | ♥ |
| mark '+' | U+2666 | ♦ |
| mark '.' | U+2668 | ♨ |
| mark ',' | U+2669 | ♩ |

### The formula is per word

```
3*x + tail
```

The formula counts one word. A field may hold more than one, and each word is
divided on its own, so a tail lands on the end of the last word and not on the
end of the field.

```
one Russian word      29 letters   3*9 + 2
two English words     22 letters   3*7 + 1
```

The two give different tails, and that is not a translation detail: it is what
a field of more than one word means. The formula is applied per word and never
to the field as a whole.

### The arrow

```
→   U+2192   the arrow, one sign
```

The writer types two signs and the shell puts the one in. Two become one, and
the one is inserted rather than typed: write `-` and `>` next to each other and
the arrow appears. It was two signs in the output, and became one, because the
dash is the marker of a child and the bracket closes the area, so neither of
them belonged to the arrow.

    on the disk    two signs, because a person types them
    on the way out one sign, because a reader reads it

The old two signs are still accepted, so what is already written keeps working.

### The digits

```
⓪  U+24EA
①  U+2460
②  U+2461
③  U+2462
④  U+2463
⑤  U+2464
⑥  U+2465
⑦  U+2466
⑧  U+2467
⑨  U+2468
```

They are digits and they are the only signs that carry a value by
themselves rather than by position, so they are not passed through.
A digit at a distance is a number, and a glyph keeps it visible.

### No duplicate keys

```
a sign      one key, one glyph, and the key is the sign
a duplicate  not an error, the later one wins, the first becomes dead
```

A duplicate key in a dictionary literal is not an error, and that is the whole
of the trouble: the later line wins and the earlier one becomes a line that
reads as though it works. A sign is given a second glyph while it has one
already, and the second is dead, and nothing anywhere says so.

So a sign is checked before it is given a glyph, not after. The check is the
list of keys: as many lines as unique keys, and a line more is a duplicate.
