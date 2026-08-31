# Why this case exists

Sibling of `canon/crlf-declaration-terminator-normalised`; read that WHY.md
for the full mechanism (the `removes-padding` non-vacuity guard is the
runner's one assertion that `canon(x) != x`).

Here the terminator under test is the **annotation's**. Amended §4.1.1 makes
the point explicitly: the inertness promise §9 gives the annotation channel is
unaffected because "a line terminator is not something an annotation *says*".
Everything in this file is canonical except the `CRLF` ending the annotation
line — table lines, blank line and declarations are already `LF` — and the
double space the guard requires sits inside the annotation, where it is
content canon must preserve. A canon that normalises every terminator changes
the file and passes; one that carries "byte-verbatim" over to the annotation's
terminator is the identity here and fails.
