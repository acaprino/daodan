import { Component, Input } from "@angular/core";

@Component({
  selector: "uk-button",
  standalone: true,
  template: `<button>{{ label }}</button>`,
})
export class ButtonComponent {
  @Input() label = "";
}
