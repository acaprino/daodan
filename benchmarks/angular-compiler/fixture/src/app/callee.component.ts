import { Component } from '@angular/core';

// a callee that is no name: `handlers[0]()` reads a keyed property, `factory()()` calls the result of a call
@Component({
  selector: 'app-callee',
  template: `
    <button (click)="handlers[0]()">Keyed</button>
    <button (click)="factory()()">Factory</button>
  `,
})
export class CalleeComponent {
  handlers = [() => {}];
  factory() {
    return () => {};
  }
}
