# Why this case exists

§4.2 rule 3 names this file as the sanctioned way to compose: "The composition
is available by writing the intermediate column down:
`| run = cumulative(a) | twice = run * 2 |` is two well-formed formulas, and by
rule 9 their order in the header does not matter."

It is also the second instance of the pass-ordering defect: `twice` returned
`#REF!(run)` because the pass that evaluates ordinary formulas ran before the
pass that evaluates row-relative ones and never ran again. A plain column may
depend on a row-relative column, so the plain pass must be able to see the
row-relative results.
