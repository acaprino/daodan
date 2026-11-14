import { useState } from 'react';
import { api } from './api';
import { persist, MemoryStore } from './store';
export function useClient() {
  const [value, setValue] = useState('');
  setValue(api.load('1'));
  api.save('2');
  persist(new MemoryStore());
  return value;
}
