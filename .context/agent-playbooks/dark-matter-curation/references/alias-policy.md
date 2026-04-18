# Alias Policy

## Safe Cases

- `Known Name (descriptor)` -> `Known Name`
- `Known Name (year range)` -> `Known Name`
- well-established alternate labels already implied by Atlas data
- direct acronym normalization when the canonical target is explicit

## Unsafe Cases

- broad historical labels
- concept families collapsed into a single concept
- phrases that could refer to multiple organizations or events
- speculative expansions not already supported by repo data

## Canonical Type Rules

- languages use `type: "language"`
- people use `type: "person"`
- organizations use `type: "organization"`
- historical events use `type: "historical_event"`
- concept combos use `type: "concept_combo"`
- concepts use `type: "concept"`

## Profile Key Rule

Use `profile_key` only when the human-readable canonical term and the file stem
do not match cleanly enough for the existing normalization pipeline.
