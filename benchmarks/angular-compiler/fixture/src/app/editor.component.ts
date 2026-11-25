import { Component, output } from '@angular/core';

@Component({
  selector: 'app-editor',
  template: `<button (click)="saved.emit('done')">Done editing</button>`,
})
export class EditorComponent {
  saved = output<string>();
}
