# Two blocks in one file: .data and .code

A working spec, English, mine. It is here because the spec comes before the
code, and this is the spec for what the compiler does with a file that has two
kinds of content in it.

## The hole

A `.vibe` file is records and nothing else. Anything that is not a record is a
line that fails to parse, and a file that has to carry a note, a table or a
diagram has nowhere to put it. The two things are written in the same file and
the compiler treats them the same, and it cannot tell them apart.

So the compiler is told where the records are. One tag, and everything above it
is not the compiler's business.

## The form

```
.data
anything at all goes here
   with any indentation
   and any markup, <tags>, **markdown**, | pipes |, { braces }
.code
(a):b->c[d]<e>
  (f):g->h[i]<j>
```

```
.data    opens the free block
.code    closes it, and opens the records
```

**Only the `.code` block is compiled.** A line in `.data` is never parsed, never
addressed and never written. It can hold a table, a diagram, a note, a fragment
of another language. The compiler does not look at it and does not complain
about it, and this is the whole of the rule.

**Both blocks are root.** Neither is a child of the other, and the records in
`.code` start at level zero whatever their indentation says. A file has two
roots, and the second one is not inside the first.

**The split is by tag, once.** The first `.code` line ends the free block. A
`.data` or `.code` line after it is a record attempt like any other line, and it
fails like one, because a second split is not a thing this does.

## Three questions the form answers before it is asked

**What if there is no `.code` at all?** Nothing is compiled and nothing is an
error. A file that is only a note is a file that has nothing for the compiler to
do, and that is a whole file, not a broken one.

**What if there is no `.data`?** Every line is a record, and this is what every
file written before this was. The two tags are optional and a file with neither
is exactly the file it was yesterday.

**What is before the first tag?** Records, if they parse, and the compiler does
not care that there was no `.data`. A tag is not a header, it is a boundary.

## The marks in a record

A record is one line, and it has five marks in this order:

```
(a):b->c[d]<e>
 |  | |  |  |
 |  | |  |  e   state
 |  | |  d     hint
 |  | c        function
 |  b          property
 a             object
```

```
()   the object, and the start of the line. nothing may come before it
:    between object and property, and between property and arrow
->   the arrow. -> and the glyph → mean the same thing and both are accepted
[]   the hint, and it is free text
<>   the state, and it is free text
```

A line that is not this shape is not a record, and it is not half a record
either. It is an error, and the error names the line.

## A record that was wrapped

A record is one line, and a long one gets wrapped by hand:

```
(a):b
    ->c[d]<e>
```

The rule is not a mark, it is the arrow. **A line that has no arrow yet and is
followed by a line that opens with one is half of a record**, whatever the first
line ends with, and the indent under it is the person saying so. The two halves
are joined before parsing and the record keeps the indentation of the first.

The test is the arrow because a colon is in the middle of `(a):b` and not at the
end of it, and a rule that looked for a trailing colon would never fire while
reading as if it worked.

```
two whole records in a row    not joined, a whole record is not half of one
two lines, neither has arrow  not joined, nothing to join on
one wrap only                 a third line is a third line
```

An earlier version of this looked for a trailing colon. It never fired, every
wrapped record stayed broken, and the code read as though it worked. The test is
the only thing that had to be right, and the test was wrong.

## What it does not do

```
it does not parse .data         it is not the compiler's business
it does not split twice         one boundary, and the rest is a file
it does not nest the blocks     two roots, not a root and its child
it does not write .data anywhere  it is not output, it is input nobody reads
it does not wrap for you        a person wraps, the compiler joins
it does not guess a boundary    an arrow on the next line, or nothing
```

The last one matters most: the free block is not copied into anything. It is
skipped, and the only trace that it was ever there is that the file still has
it.

## The check, before the write

```
 1  a file with no tags compiles exactly as it did before
 2  a file with a .data block compiles to the same records as without it
 3  anything at all inside .data is skipped, including a broken record
 4  a .code line inside .data ends the block and is not a second split
 5  the free block is not in the output
 6  a record on one line compiles exactly as it did before
 7  a record wrapped over two lines compiles to the same one record
 8  a wrap after the arrow is not a wrap and the record stays broken
 9  two records in a row are not joined
10  a file with a .data block decodes back to the same records
```

## Not yet

```
tag rules and the wrap rule are written here and are checked
the plugin side of both is checked by hand, not by the gate
```
