---
title: useEffectEvent for Latest Effect Values
impact: LOW
impactDescription: prevents effect re-runs
tags: advanced, hooks, useEffectEvent, refs, optimization
---

## useEffectEvent for Latest Effect Values

Use Effect Events for non-reactive logic fired from an Effect in supported React versions. Keep values that should resynchronize the Effect in its dependencies. This is not a stable callback API or a general dependency escape. The example assumes changes to onSearch alone must not restart the debounce. See [React useEffectEvent](https://react.dev/reference/react/useEffectEvent).

**Incorrect (effect re-runs on every callback change):**

```tsx
function SearchInput({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState('')

  useEffect(() => {
    const timeout = setTimeout(() => onSearch(query), 300)
    return () => clearTimeout(timeout)
  }, [query, onSearch])
}
```

**Correct (using React's useEffectEvent):**

```tsx
import { useEffectEvent } from 'react';

function SearchInput({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState('')
  const onSearchEvent = useEffectEvent(onSearch)

  useEffect(() => {
    const timeout = setTimeout(() => onSearchEvent(query), 300)
    return () => clearTimeout(timeout)
  }, [query])
}
```
