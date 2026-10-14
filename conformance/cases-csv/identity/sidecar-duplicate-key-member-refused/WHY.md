The sidecar declares `key` twice. Both named columns exist and both hold
unique values, so the only fault is the repeated declaration. Reading:
§9.4 refuses a duplicate `key` declaration, and the sidecar is the CSV's
only place to declare one. JSON parsers disagree on duplicate members
(RFC 8259 calls the behaviour unpredictable), so two readers would key on
different columns, which is the divergence §2 forbids.
