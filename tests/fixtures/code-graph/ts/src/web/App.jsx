import React from 'react';
import * as UI from './ui';
import { Banner } from './ui';
import { useCheckout } from './useCheckout';
import { runWith, priceFor } from './billing';
export function App() {
  const { pay, price } = useCheckout('pro');
  const handleClose = () => pay();
  const total = runWith(priceFor, 'pro');
  return (
    <div>
      <Banner />
      <UI.Paywall onPay={pay} />
      <button onClick={handleClose}>{price + total}</button>
    </div>
  );
}
