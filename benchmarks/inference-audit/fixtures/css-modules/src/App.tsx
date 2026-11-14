import styles from './Button.module.scss';
import colors from './colors.module.css';
import './theme.pcss';
export const A = () => <div className={`${styles.primary} ${styles.gap} ${colors.brand} ${styles.inner} card title`} />;
