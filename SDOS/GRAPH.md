# Project Knowledge Graph

_v1 — updated 2026-07-16T04:59:01.917629+00:00_

```yaml
graph:
  events: []
  last_updated: '2026-07-16T04:59:01.917629+00:00'
  nodes:
  - id: PROJECT
    label: srie-runtime
    metadata: {}
    state: SYNCED
    type: raiz
  - id: LANGUAGES
    label: Languages
    metadata: {}
    state: SYNCED
    type: dominio
  - id: TESTS
    label: Tests
    metadata: {}
    state: SYNCED
    type: dominio
  - id: VCS
    label: Version Control
    metadata: {}
    state: SYNCED
    type: dominio
  relationships:
  - source: PROJECT
    target: LANGUAGES
    type: contains
    weight: 1.0
  - source: PROJECT
    target: TESTS
    type: contains
    weight: 1.0
  - source: PROJECT
    target: VCS
    type: contains
    weight: 1.0
  version: 1
```
