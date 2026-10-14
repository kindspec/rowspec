Every line ends in a lone CR. §13 makes refusal 15 a warning, and the
warning only means something if the file is then read. Reading: a lone CR
acts as a record break, so the file is a two-column header with two rows
and nothing else is wrong. Read as one line, the header would gain a field
and a column name containing CR, and the warning would be a refusal in
disguise.
