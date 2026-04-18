# Alias Policy

## Safe Cases

- `Known Name (descriptor)` -> `Known Name`
- `Known Name (year range)` -> `Known Name`
- well-established alternate labels already implied by Atlas data
- direct acronym normalization when the canonical target is explicit
- reviewed project or platform labels when repo context makes the target
  identity unambiguous
- reviewed descriptor-heavy phrases when they clearly name one existing Atlas
  person, language, organization, or historical event

## Unsafe Cases

- broad historical labels
- concept families collapsed into a single concept
- phrases that could refer to multiple organizations or events
- speculative expansions not already supported by repo data
- related but non-identical things merged only because they often co-occur
- institution, product, and language terms collapsed without clear evidence
  about which level the phrase is naming

## Judgment-Heavy Review Rule

If a candidate is not a simple mechanical variant, require explicit repo
evidence before merging it:

1. the target exists clearly in source data or profile docs
2. the candidate phrase is acting as a label for that target
3. the merge does not destroy a separately meaningful concept
4. the behavior can be protected with a focused test

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
