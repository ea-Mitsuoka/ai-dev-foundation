---
id: tests-layout
title: Test Layout
---

# tests/ — Test Layout

Binding rules: [.ai/testing.md](../.ai/testing.md). This tree mirrors `src/` exactly so
the tests for any file are findable mechanically:

```
tests/
  modules/<context>/
    unit/            # no I/O, <100ms each — mirrors the module's internal structure
    integration/     # module + real adapters (containers)
  e2e/               # critical user flows through the real stack
```

Run via canonical commands only: `task test`, `task test-unit`, `task coverage`.
