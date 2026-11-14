import { cva } from 'class-variance-authority';
import { tv } from 'tailwind-variants';
export const button = cva('btn', {
  variants: { intent: { primary: 'btn-primary', ghost: ['btn-ghost', 'faded'] } },
  compoundVariants: [{ intent: 'primary', class: 'raised' }],
});
export const card = tv({ base: 'card', slots: { title: 'card-title' }, variants: { size: { lg: 'card-lg' } } });
export const B = () => <button className={button({ intent: 'primary' })} />;
