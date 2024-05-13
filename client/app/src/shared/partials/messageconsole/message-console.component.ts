import {AfterViewChecked, Component} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {ErrorCodes} from "@app/models/app/error-code";

@Component({
  selector: "messageconsole",
  templateUrl: "./message-console.component.html"
})
export class MessageConsoleComponent implements AfterViewChecked {
  private timeoutId: number | NodeJS.Timeout;
  private timeoutRunning: boolean = false;

  constructor(public appDataService: AppDataService) {
  }

  dismissError() {
    clearTimeout(this.timeoutId);
    this.timeoutRunning = false;
    this.appDataService.errorCodes = new ErrorCodes();
  }

  ngAfterViewChecked(): void {
    if (!this.timeoutRunning && this.appDataService.errorCodes.code !== -1) {
      this.timeoutRunning = true;
      this.timeoutId = setTimeout(() => {
        this.dismissError();
      }, 3000);
    }
  }
}
