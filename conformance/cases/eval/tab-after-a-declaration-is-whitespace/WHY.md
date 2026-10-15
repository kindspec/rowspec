# Why this case exists

The control for `parse/vertical-tab-after-a-declaration-refused`: the last
declaration ends with a horizontal tab.

§4.1: `declaration = *WSP ident *WSP ":=" *WSP rhs [ 1*WSP "#" *char ] *WSP eol`,
and `WSP = SP / HTAB`. The tab is the trailing `*WSP`, so the line is a
declaration and `s` is `1`.
