The sidecar is not valid JSON and the CSV has no other fault (ids unique).
SPEC.md does not define the sidecar's failure modes. Reading: §4 says a
reader that cannot recognise a construct MUST refuse it and MUST NOT
degrade a failed recognition into a different successful one. Ignoring
the sidecar would degrade "key declared" into "no key", which silently
switches off refusal 5, so the file is refused.
