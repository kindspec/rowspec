§9.1 refuses a line whose first seven characters are seven `|`. In a CSV
`|` is not structural, so the line is otherwise an ordinary one-field
record matching the one-column header; the marker is the only refusal.
