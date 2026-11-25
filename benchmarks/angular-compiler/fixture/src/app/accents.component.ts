import { Component } from '@angular/core';

// perché i byte di una riga non sono le unità di JavaScript: è, 😀
@Component({
  selector: 'app-caffè', template: `
    <p>caffè 😀</p><button (click)="brew()">Brew</button> perché`,
})
class AccentsComponent {
  brew() {}
}
