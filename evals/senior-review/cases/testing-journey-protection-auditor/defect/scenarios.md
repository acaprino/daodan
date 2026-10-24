# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## entry-and-denial

Required journey: keyboard users enter checkout, decline optional location, then submit an order. Complete supplied browser test:
```ts
test("checkout",async ({page,context})=>{
 await context.grantPermissions(["geolocation"]);
 await page.goto("/checkout");
 await page.getByRole("button",{name:"Submit"}).click();
});
```

## Admitted production route

checkout-production.html is the complete standalone /checkout production route for the independent browser scenario. Its native button supports keyboard activation; the optional geolocation permission resolves to either its success or denial callback, and both callbacks record one order and display confirmation. The browser harness supplies a fresh page per test. The correct scenario's declared project configuration denies geolocation, so its error callback is the admitted path. These are source and hypothetical harness contracts, never an observed browser run. The pure reducer scenario remains separate.
