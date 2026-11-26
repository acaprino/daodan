import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LegacyComponent } from './legacy.component';

@NgModule({
  declarations: [LegacyComponent],
  imports: [CommonModule, RouterModule.forChild([{ path: '', component: LegacyComponent }])],
})
export class LegacyModule {}
