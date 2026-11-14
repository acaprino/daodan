import styled, { createGlobalStyle } from 'styled-components';
import { css } from '@emotion/css';
export const Title = styled.h1`
  color: var(--ink);
  .dark & { color: white; }
  & .title { margin: 0; }
  ${(p: any) => p.extra}
`;
export const Global = createGlobalStyle`
  :root { --ink: #111; }
  .btn-${'primary'} { color: red; }
  .${(p: any) => p.name} { color: blue; }
`;
export const pad = css`
  padding: 2px;
  &:hover .title { padding: 4px; }
`;
