import { Component } from '@angular/core';

// a call with no object before it names a method of the class, unless the template declares the name: `let-c` of an
// ng-template, an `@let`, the variable of an `@for` (the compiler's own scope rules, not the parser's)
@Component({
  selector: 'app-scoped',
  template: `
    <ng-template #tpl let-c="close"><button (click)="c('x')">Close</button></ng-template>
    @let save = pick();
    <button (click)="save()">Let save</button>
    @for (go of items; track $index) {
      <button (click)="go()">Loop go</button>
    }
    <button (click)="real()">Real</button>
    <button (click)="this.save()">This save</button>
  `,
})
export class ScopedComponent {
  items = [() => {}];
  pick() {
    return () => {};
  }
  real() {}
  save() {}
  go() {}
}
