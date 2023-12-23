import {HttpClient} from "@angular/common/http";
import {Component, Input} from "@angular/core";
import {NgbDateStruct, NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";


@Component({
  selector: "src-tip-operation-set-reminder",
  templateUrl: "./tip-operation-set-reminder.component.html"
})
export class TipOperationSetReminderComponent {
  @Input() args: any;

  request_motivation: string;
  model: NgbDateStruct;

  constructor(private modalService: NgbModal, private http: HttpClient, private utils: UtilsService) {
  }

  confirm() {
    this.cancel();

    if (this.args.operation === "postpone" || this.args.operation === "set_reminder") {
      let date: number;
      const {year, month, day} = this.args.reminder_date;
      const dateData = new Date(year, month - 1, day);
      const timestamp = dateData.getTime();
      if (this.args.operation === "postpone")
        date = this.args.expiration_date.getTime();
      else {
        date = timestamp;
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

  disableReminder() {
    this.cancel();
    const req = {
      "operation": "set_reminder",
      "args": {
        "value": 32503680000000
      }
    };
    this.http.put("api/recipient/rtips/" + this.args.tip.id, req)
      .subscribe(() => {
        this.reload();
      });
  }

  reload() {
    this.utils.reloadCurrentRoute();
  }

  cancel() {
    this.modalService.dismissAll();
  }

  ngOnInit() {
    const reminderDate = this.args.reminder_date;
    this.args.reminder_date = {
      year: reminderDate.getUTCFullYear(),
      month: reminderDate.getUTCMonth() + 1,
      day: reminderDate.getUTCDate()
    };
  }
}
