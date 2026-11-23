import { Component } from '@angular/core';

@Component({
  selector: 'app-crlf',
  template: `
    <button (click)="go()">Go</button>
    <button (click)="stop()">Stop</button>
  `,
})
export class CrlfComponent {
  go() {}
  stop() {}
}
