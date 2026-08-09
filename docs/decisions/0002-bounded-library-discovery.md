# 0002: Bound all library discovery

- Status: accepted
- Date: 2026-08-08

## Context

Game-library folders are external input. They can be unavailable, unusually
large, deeply nested, or contain links that leave the expected directory.
Recursive traversal inside a television Activity also makes the behavior hard
to test and can exhaust the UI process.

## Decision

Library discovery lives in a pure Java `GameCatalog`. The scanner is iterative,
read-only, rejects symbolic links, and verifies that canonical child paths stay
inside the selected system root. It enforces explicit limits for depth,
directories, game entries, core-marker bytes, and core-marker lines.

The catalog returns an immutable snapshot with a truncation flag. The Activity
renders the result and reports truncation without owning filesystem traversal.

## Consequences

- Catalog behavior can be tested without Android or device storage.
- Unexpected directory structures fail closed or return a bounded partial list.
- Limit changes must include a contract-test update and a review of television
  memory and navigation behavior.
