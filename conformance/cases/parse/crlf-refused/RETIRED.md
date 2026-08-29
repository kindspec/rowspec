# Retired, and why — do not simply restore this case

This case asserted that CRLF input is refused, citing SPEC.md §3 as it then
read: "UTF-8, LF line endings, no BOM."

It was correct about the prose and the prose was wrong. The pre-existing
`roundtrip/crlf` case requires CRLF input to round-trip byte-exactly, and the
specification's own preamble says that where the spec and the suite disagree,
**the suite wins**. Two cases asserted contradictory rules, so one had to go.

§3 has been amended: line endings are PRESERVED, both LF and CRLF are accepted,
and only the *canonical* form is LF. A lone CR is still refused, because it
makes two rows share one git line — see `parse/lone-cr-refused`, which is the
half of this case that survived and is the half that matters.

Retiring a case authored by the adversarial case author needs a reason on the
record, and this is it: the rule it tested no longer exists. It is not being
retired because it was inconvenient to pass.
