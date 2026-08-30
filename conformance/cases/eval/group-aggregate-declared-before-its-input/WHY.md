# Why this case exists

The same shape as `eval/group-aggregate-over-a-computed-column`, with the group
aggregate written to the **left** of the column it reads.

§4.2 rule 9: "A formula may name any column, stored or computed, wherever that
column stands in the header. **The order of columns in the header is not an
input to any value**, exactly as §6 says a row's position in the file is not."

A reader that evaluates the header left to right, or in a fixed number of
passes, gets a different answer for this file than for the other one. The two
files hold the same data and must hold the same values.
