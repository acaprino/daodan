import clsx from 'clsx';
import styles from './styles/Button.module.css';
import './styles/theme.css';

const BASE = 'card btn';
const TONES = { warm: 'text-red-500', cold: 'text-blue-500' };

export function App({ size, on, color }: { size: string; on: boolean; color: string }) {
  document.documentElement.classList.toggle('dark', on);
  document.documentElement.style.setProperty('--gap', '2px');
  return (
    <div id="app" className={`${BASE} flex px-2 hover:bg-red-500 ghost-x`} style={{ '--accent': color, animation: 'spin 2s', rotate: 'var(--angle)' }}>
      <button className={clsx(styles.primary, on && 'btn', { sidebar: on })} />
      <span className={`panel__title ${size}-x ${TONES.warm}`} />
      <i className={styles[size]} />
      <b className="[--accent:blue] shell" />
    </div>
  );
}

export const Wide = () => (
  <p
    className={`flex
      shell`}
  />
);
