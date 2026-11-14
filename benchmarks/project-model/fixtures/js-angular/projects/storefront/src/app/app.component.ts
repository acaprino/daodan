import { Component } from "@angular/core";
import { ButtonComponent } from "ui-kit";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [ButtonComponent],
  templateUrl: "./app.component.html",
})
export class AppComponent {}
