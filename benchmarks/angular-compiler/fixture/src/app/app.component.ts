import { Component, inject } from '@angular/core';
import { NgFor } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterOutlet } from '@angular/router';
import { EditorComponent } from './editor.component';
import { OrderService } from './order.service';

@Component({
  selector: 'app-root',
  imports: [NgFor, FormsModule, RouterOutlet, EditorComponent],
  templateUrl: './app.component.html',
})
export class AppComponent {
  svc = inject(OrderService);
  router = inject(Router);
  busy = false;
  ready = true;
  open = false;
  q = '';
  label = 'Pay now';
  orders = [{ id: 1 }, { id: 2 }];

  save() {}
  close() {}
  reopen() {}
  submit() {}
  search() {}
  inIf() {}
  remove(o: { id: number }) {}
  removeFor(o: { id: number }) {}
  liClick(o: { id: number }) {}
  inTpl() {}
  onSaved(e: string) {}
  onResize() {}
  withIcon() {}
  pay() {}
}
