"""Epic 2 — extraction. Parsers run OFFLINE over stored bytes and are
re-runnable: a parser that was wrong for three months is repaired by replaying
history, which is only possible because nothing was parsed at fetch time."""
