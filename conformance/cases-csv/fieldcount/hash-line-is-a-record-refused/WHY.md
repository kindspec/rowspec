`# note` would be an annotation in .mdtbl. A CSV has no annotation channel
(RFC 4180 defines none, and §9's ignorable channel is "outside the
table" in the .mdtbl sense), so the line is a one-field record against a
two-field header (§9.6). Reading: treating it as a comment would let a CSV
row silently vanish.
