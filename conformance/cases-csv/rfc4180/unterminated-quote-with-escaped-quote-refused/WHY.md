The quoted field opened on line 2 holds an escaped "" and is never
closed: the remaining quote count after the opener is even, all of it
the one escape. The file ends inside the field, refused under §13's
record-boundary bullet. Issue #94 item 3.
