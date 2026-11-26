import { Routes } from '@angular/router';
import { AppComponent } from './app.component';
import { InlineComponent } from './inline.component';

export const routes: Routes = [
  { path: '', component: AppComponent },
  {
    path: 'orders',
    loadComponent: () => import('./orders.component').then((m) => m.OrdersComponent),
  },
  {
    path: 'admin',
    children: [{ path: 'users', component: InlineComponent }],
  },
  {
    path: 'legacy',
    loadChildren: () => import('./legacy.module').then((m) => m.LegacyModule),
  },
  { path: '**', redirectTo: '' },
];
