import { Component } from '@angular/core';

// not imported by main.ts nor by what it imports: the tsconfig.json of the fixture does not reach it
@Component({
  selector: 'app-unreached',
  template: '<button (click)="helper.run()">Run</button>',
})
export class UnreachedComponent {
  helper = { run() {} };
}
