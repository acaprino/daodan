import { cn } from './utils';
export const U = ({ on }: { on: boolean }) => <p className={cn('card', on && 'tag')} />;
