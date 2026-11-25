import { Component } from '@angular/core';

@Component({
  selector: 'app-inline',
  host: { '(click)': 'onHost()', '(window:keydown.escape)': 'onEsc()', '[class.active]': 'active' },
  template: `
    <section>
      <h2>Inline</h2>
      <button (click)="go()">Go inline</button>
      <button (click)="this.goThis()">Go with this</button>
    </section>
  `,
})
export class InlineComponent {
  active = false;
  onHost() {}
  onEsc() {}
  go() {}
  goThis() {}
}

@Component({
  selector: 'app-inline-escaped',
  template: 'It\'s <button (click)="esc()">Esc</button>\n<button (click)="esc2()">Esc two</button>',
})
export class InlineEscapedComponent {
  esc() {}
  esc2() {}
}

@Component({
  selector: 'app-inline-dq',
  template: "<button (click)=\"dq()\">Dq \"quoted\"</button>",
})
export class InlineDoubleQuotedComponent {
  dq() {}
}
