# Why this case exists

Two adjacent rows keyed U+00E9 and U+0065 U+0301, one key under NFC.

§3: "Identifiers are compared after Unicode NFC normalisation." §6: "two rows holding one key are §9.5, not this."

On raw code points the second key sorts below the first, so a reader that compares unnormalised values reports the wrong refusal. Under NFC they are equal, and equal adjacent keys are §9.5 alone.
