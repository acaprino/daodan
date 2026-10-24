# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## entry-and-denial

Required journey: keyboard entry, optional location denial, then order confirmation. Browser project config denies geolocation by default.
```ts
test("checkout",async ({page})=>{
 await page.goto("/checkout");
 await page.keyboard.press("Tab");
 await expect(page.getByRole("button",{name:"Submit"})).toBeFocused();
 await page.keyboard.press("Enter");
 await expect(page.getByText("Order confirmed")).toBeVisible();
});
```

## Admitted production route

checkout-production.html is the complete standalone /checkout production route for the independent browser scenario. Its native button supports keyboard activation; the optional geolocation permission resolves to either its success or denial callback, and both callbacks record one order and display confirmation. The browser harness supplies a fresh page per test. The correct scenario's declared project configuration denies geolocation, so its error callback is the admitted path. These are source and hypothetical harness contracts, never an observed browser run. The pure reducer scenario remains separate.
