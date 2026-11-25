import { Component } from '@angular/core';

const title = 'Run';

@Component({
  selector: 'app-computed',
  template: `<button (click)="run()">${title}</button>`,
})
export class ComputedComponent {
  run() {}
}
