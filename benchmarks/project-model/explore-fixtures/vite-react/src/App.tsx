import { useEffect, useState } from 'react';
import { save, reset } from './lib/actions';
export default function App() {
  const [total, setTotal] = useState(5);
  useEffect(() => { const t = setInterval(() => setTotal(n => n), 150); return () => clearInterval(t); }, []);
  return <main><p>{total}</p><button onClick={() => setTotal(save(total))}>Save</button>
    <button onClick={() => setTotal(reset())}>Reset</button></main>;
}
