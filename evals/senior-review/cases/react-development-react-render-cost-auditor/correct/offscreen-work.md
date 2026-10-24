# Fixed-height card update

Requirement: a supported React catalog shows 5,000 immutable cards in document order, each exactly 40px high. Only 20 are near the viewport. A search-result update may use at most 8ms of layout/paint work. All cards remain semantically present and reachable by scrolling/search; JavaScript node creation is a different budget and is within that budget.

```jsx
function Catalog({cards}) {
  return <div>{cards.map(card => <article className="card" key={card.id}>{card.label}</article>)}</div>;
}
```
```css
.card { height: 40px; content-visibility: auto; contain-intrinsic-size: auto 40px; }
```

Complete effective style/build inventory: these declarations apply. Supported RenderEngine 5 implements content-visibility:auto, keeps these cards searchable/semantically present, and honors the supplied exact 40px intrinsic geometry during deferral. Candidate-bound synthetic profile attributes 4ms to layout/paint on the result update; JavaScript node creation remains and is separately within budget. No added virtualizer or node-removal requirement exists. These are supplied profile/engine facts, not browser execution by the reviewer.
