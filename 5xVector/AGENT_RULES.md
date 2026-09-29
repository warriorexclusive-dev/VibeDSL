# AGENT RULES

This is a dictionary, not a task. It is consulted in English and the question
is answered from it. It is not read as instructions to follow and not worked
through from the top to the bottom.

```
this file    a dictionary of what the signs and the file are for
consulted    in English
answer       comes from here and not from the model
never        read it as a list of things to do
```

The writing side is the compiler's, it lives in RULES.md, and nothing from it
belongs here. A reader that also carries the rules for building the table
starts building the table.

```
this file    reading a spec, and what the signs and the file are for
RULES.md     writing a spec, and how the table is built
compiler     the only thing that writes
```

## The order

```
1  decode   every sign is read as a sign
2  resolve  an address is a byte offset, seek there, read the word
3  glue     the pieces are joined into a word
```

Decode first, then read. Reading before decoding gives a text, and the text is
not what was written.

## What the signs are for

```
▦▣▭▬▯▮▢⇲⇱⇵⇶▤▰▱▲◉

the sixteen    a bit of an address, 5 of them make one address
●          the separator, the only sign in the file that is not an address
□         the visible space, never turned back into a space
▶ ... ◀         the parent tags, and the parent goes between them
```

The marks are looked up one at a time by their sign, and a list of them is not
a list to work through. The mark for a sign is a single lookup, and the table
for it is in the compiler.

A sign is read as a sign. `◰` is a bracket, what it brackets is read, and
the bracket itself is never written out as `(`. Reversing it throws the role
away, and the role is the whole of the sign.

The marks are formatting. They are there so the shape of a record is visible
and they carry no meaning of their own.

## What the file is for

```
one file     the words and where each one sits
used for     taking a byte offset and getting the word at it
not for      what a word means, that is not in it at all
not for      deciding an address, that is the compiler's
```

The file holds offsets and nothing else. It does not translate, it does not
define, and it is not a vocabulary. What the words mean is outside it, and a
reader that expects the file to supply meaning will read meaning into it.

## Spaces stay signs

`□` is a sign and it is never turned into a space. A space in the
source is what the sign stands for; the sign is what is in the file. Gluing
words and dropping the sign between them produces a word that was never
written, and it looks correct, which is what makes it dangerous.

## What the model never does

```
never types a sign        a human cannot, and neither can the model
never writes the file     the compiler owns it
never decides an address   if it is not there, that is for the compiler
never turns a sign into ASCII   the role is in the sign, not in the letter
```

The last one is the whole difference from a text model, and it is not a style.
A text model reads a bracket and sees a bracket. This one sees a sign with a
role, and reads what is inside it.

### The arrow

```
→   U+2192   the arrow, one sign, and the writer types it
```

It carries the load on both sides: it is what the writer types and what the
reader resolves. It was two signs, and the two signs pulled apart, because the
dash is the marker of a child and the bracket closes the area, so neither of
them belonged to it. One sign has no neighbours to be confused with.

The old two signs are still accepted, so what is already written keeps working.

## The two blocks, and they are not one thing

```
the dictionary   below, consulted in English, a sign is looked up
the spec         a block of its own, loaded and executed
```

A model that has both as one run of text works through them, and a model that
works through a dictionary answers nothing. So the spec is its own block, under
its own heading, and the two are never handed over together.

## The cycle

```
1  convert       into a spec, the words a person can type
2  load          the spec into the model, and only the spec
3  execute       the spec, and not the dictionary
4  a lost spec   is converted again, and the two blocks stay apart
```

A spec that is lost is not remembered, it is made again from the source. The
source is the words on the disk, and it is the only thing that is not derived.
Everything else is compiled from it, and anything compiled can be made again.

## What is looked up and what is converted

```
a sign   read from the dictionary, and never written back as ASCII
a word   taken from the address, and that one is English again
```

Only the second is a conversion, and the first must not be made into one. A
sign turned back into a letter loses the role, and the role is the whole of the
sign: a bracket becomes a bracket, and then it is only a bracket, and what it
brackets is not read at all.

So the model does two different things, and they are not one thing. A sign is
looked up. A word is resolved. The model converts back only the word.

## Where the words are decoded

```
the dictionary   here, consulted in English, a sign is looked up
the words        in the decoder, in code, and not in the model
```

The model does not decode a word. A rule that says a word is resolved does not
say who resolves it, and this says: the decoder does, it is code, it costs
nothing, and the model receives the word already English. A model that
decodes in the head spends its cache on it, and that is the whole cost this
design removes.

So the order is fixed and there is no other: the glyphs are decoded by the
decoder, the words go to the model, and the model executes. The dictionary is
consulted only when a sign is not understood, and a sign that is not
understood is never converted into a letter, it is looked up again.
