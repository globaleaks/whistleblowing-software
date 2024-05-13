import {Component, Input, Output, EventEmitter} from '@angular/core';

@Component({
  selector: 'app-switch',
  templateUrl: './switch.component.html'
})
export class SwitchComponent {
  @Input() label: string = 'Switch';
  @Input() isChecked: boolean = false;
  @Input() can_upload_files:boolean
  @Output() switchChange = new EventEmitter<boolean>();

}
