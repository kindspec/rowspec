# Why this case exists, and the alternative if I have read it wrong

§4.2 rule 1's grammar allows **at most one** unary minus per factor:

    factor  = [ "-" *WSP ] primary
    primary = literal / ident / "(" *WSP expr *WSP ")"

`[ "-" ]` is zero-or-one, and `-a` is not a `primary`, so `--a` is not generated
by `formula` and §9.20 refuses it. `- -a` with a space is the same string of
tokens and is refused for the same reason.

**Both implementations currently accept it** and return 6.0, reading it as
double negation. Neither is following the ABNF.

If stacking was intended, the fix is in the grammar, not here: `[ "-" *WSP ]`
becomes `*( "-" *WSP )`, and this case should be retired with a note. I have
written it in the direction the ABNF actually generates, because that is the
normative artifact and because the [CHOICE] paragraphs elsewhere in §4.2 argue
consistently for one spelling per value — `- -a`, `--a`, `----a` and `a` are
four spellings of two values.

The control that stops an over-correction is
`eval/unary-minus-after-binary-minus`: `a - -b` **is** generated (`expr` is
`term *( ("+" / "-") term )` and the second `term`'s `factor` takes the unary
minus) and must keep working.
