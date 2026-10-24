# Fixed-height card update

Requirement: a supported React catalog shows 5,000 immutable cards in document order, each exactly 40px high. Only 20 are near the viewport. A search-result update may use at most 8ms of layout/paint work. All cards remain semantically present and reachable by scrolling/search; JavaScript node creation is a different budget and is within that budget.

```jsx
function Catalog({cards}) {
  return <div>{cards.map(card => <article className="card" key={card.id}>{card.label}</article>)}</div>;
}
```
```css
.card { height: 40px; }
```

Complete effective style/build inventory: no virtualization, containment or automatic content deferral. Supported RenderEngine 5 implements content-visibility:auto and honors the supplied 40px intrinsic geometry. Candidate-bound synthetic profile attributes 36ms to layout/paint of offscreen card content on every result update. Deferring offscreen content with stable reserved geometry yields 4ms on the same candidate/workload; it does not remove the React elements. These are supplied profile/engine facts, not browser execution by the reviewer.
