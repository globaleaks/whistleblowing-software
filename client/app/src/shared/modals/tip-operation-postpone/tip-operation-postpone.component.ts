import {HttpClient} from "@angular/common/http";
import { Component, Input, OnInit, inject } from "@angular/core";
import { NgbDateStruct, NgbModal, NgbInputDatepicker } from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import { FormsModule } from "@angular/forms";
import { TranslateModule } from "@ngx-translate/core";
import { TranslatorPipe } from "@app/shared/pipes/translate";

@Component({
    selector: "src-tip-operation-postpone",
    templateUrl: "./tip-operation-postpone.component.html",
    standalone: true,
    imports: [NgbInputDatepicker, FormsModule, TranslateModule, TranslatorPipe]
})
export class TipOperationPostponeComponent implements OnInit {
  private modalService = inject(NgbModal);
  private http = inject(HttpClient);
  private utils = inject(UtilsService);

  @Input() args: any;

  request_motivation: string;
  model: NgbDateStruct;
  minDate: NgbDateStruct;
  maxDate: NgbDateStruct;

  confirm() {
    this.cancel();

    if (this.args.operation === "postpone" || this.args.operation === "set_reminder") {
      let date: number;

      const {year, month, day} = this.args.expiration_date;
      const dateData = new Date(year, month - 1, day, 23, 59, 59);
      const timestamp = dateData.getTime();

      if (this.args.operation === "postpone")
        date = timestamp;
      else {
        date = this.args.reminder_date.getTime();
      }

      const req = {
        "operation": this.args.operation,
        "args": {
          "value": date
        }
      };

      return this.http.put("api/recipient/rtips/" + this.args.tip.id, req)
        .subscribe(() => {
          this.reload();
        });
    }
    return;
  }

  reload() {
    this.utils.reloadCurrentRoute();
  }

  cancel() {
    this.modalService.dismissAll();
  }

  ngOnInit() {
    if (this.args && this.args.expiration_date) {
      const expirationDate = this.args.expiration_date;
      this.args.expiration_date = {
        year: expirationDate.getUTCFullYear(),
        month: expirationDate.getUTCMonth() + 1,
        day: expirationDate.getUTCDate()
      };
    }

    if (this.args && this.args.dateOptions) {
      this.minDate = this.parseNgbDate(this.args.dateOptions.minDate);
      this.maxDate = this.parseNgbDate(this.args.dateOptions.maxDate);
    }
  }

  private parseNgbDate(date: Date): NgbDateStruct {
    const dateObj = new Date(date);
    const year = dateObj.getUTCFullYear();
    const month = dateObj.getUTCMonth() + 1;
    const day = dateObj.getUTCDate();

    if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
      return {year, month, day};
    }
    return {year: 0, month: 0, day: 0};
  }
}
