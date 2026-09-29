# SPEC

Reference is the source form. The glyph form is what it compiles to.

## 1. The tool

GPS gives an area, 50 km spread. An exact query gives a point, 20 m spread.
2 500 times finer.

A 1:1 answer is always false, for GPS and for the model. Triangulation differs
from invention in nothing but being named. So the truth is the guess, and the
falsehood is presenting it as exact.

## 2. Why five coordinates and not three

Three is a small area, and a small area gets mistaken for a point. Five is large
enough that it cannot be mistaken by accident.

Latitude and longitude are an area. Height is added to some and not to all, and
that is normal rather than exceptional. The area always exists. The point
appears only once the area is chosen, and it is chosen by whoever stands in it,
not by the file.

## 3. Acceptance, and the threshold

Three is minimal. Five is acceptable. Fifteen is habit. Twenty is habit, and
past twenty acceptance costs nothing.

Twenty is not a number of checks and not an overhead on reasoning. It is the
point at which an action stops being deliberate and becomes automatic, like
shifting a manual gearbox while driving: the driver does not recall which gear
the fourth is, they know, because it was learned.

Twenty acceptances per address is cheap, because it runs on automatic. Twenty
checks every time, no. A unique action, yes, and errors happen, and it is
correctable.

So twenty is the boundary between thinking and habit. Below it every use costs
deliberation. Above it nothing is costed, because it repeats. And a habit is
verified once, not twenty times.

## 4. All words, as addresses

Every word becomes an address. The address is the same for all words, and this
is not because content is washed out but because only repetition washes out.

A hash duplicates by merging, a vector duplicates by averaging. Repetition of a
hash is useful, repetition of a vector is harmful. So ninety five percent of
meaning is in hashes and five percent in vectors. A hash is not a marker, it is
a reference.

Uniqueness does not give irreplaceability. It gives more precise addressing, and
it guarantees storage in the cache regardless of the search complexity of the
task.

What remains in the vectors is what the operator can correct, by choosing the
weights.

## 5. The frame

The frame is always present, it always holds a set, and inside the set are
vectors, and a vector holds the meaning. A bare value does not exist.

Erasing one address does not break the record, it changes it, so what is
checkable is the number of separators and not the field. Separators are
cheaper than holding weight.

## 6. The answer is an area, not a point

```
( fix ) area          correct the area
( fix ) ( narrow )    correct and narrow
( fix ) ( reject )    correct, do not narrow, reject
```

One address in all three, and only the second field differs. So blur is
declared rather than derived, and someone else decides what is acceptable,
because that is not a level I can reach.

## 7. What it is for

An embedding is built in order to write a comparative specification. That is its
purpose. Everything else is construction. A comparative specification is written
in order to be compared, not in order to be read by a person, and that is why
glyphs are legitimate where words do not work: a person looks at the line with
their eyes anyway, and the triangulation happens in the device, not in the text.

## 8. The rules that do not get lost

Only English. Translation into English is mandatory before the task is written
in glyphs.

The table is English, so a rule written in any other language has no address in
it and blurs together with everything else in the flood. Rules that are meant
to survive must be in the language that survives.
