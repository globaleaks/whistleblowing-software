import {AfterViewInit, ChangeDetectorRef, Component, TemplateRef, ViewChild} from "@angular/core";
import {ActivatedRoute, Router} from "@angular/router";
import {AppConfigService} from "@app/services/app-config.service";
import {TipService} from "@app/shared/services/tip-service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {AppDataService} from "@app/app-data.service";
import {ReceiverTipService} from "@app/services/receiver-tip.service";
import {GrantAccessComponent} from "@app/shared/modals/grant-access/grant-access.component";
import {RevokeAccessComponent} from "@app/shared/modals/revoke-access/revoke-access.component";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {Observable} from "rxjs";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {TipOperationSetReminderComponent} from "@app/shared/modals/tip-operation-set-reminder/tip-operation-set-reminder.component";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {HttpClient} from "@angular/common/http";
import {TipOperationPostponeComponent} from "@app/shared/modals/tip-operation-postpone/tip-operation-postpone.component";
import {CryptoService} from "@app/crypto.service";
import {TransferAccessComponent} from "@app/shared/modals/transfer-access/transfer-access.component";
import {AuthenticationService} from "@app/services/authentication.service";


@Component({
  selector: "src-tip",
  templateUrl: "./tip.component.html",
})
export class TipComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  @ViewChild("tab2") tab2!: TemplateRef<any>;
  @ViewChild("tab3") tab3!: TemplateRef<any>;

  tip_id: string | null;
  answers: any = {};
  uploads: any = {};
  questionnaire: any = {};
  rows: any = {};
  tip: any = {};
  contexts_by_id: any;
  submission_statuses: any;
  score: any;
  ctx: string;
  submission: any;
  showEditLabelInput: boolean;
  tabs: any[];
  active: string;
  loading = true;

  constructor(private tipService: TipService, private appConfigServices: AppConfigService, private router: Router, private cdr: ChangeDetectorRef, private cryptoService: CryptoService, protected utils: UtilsService, protected preferencesService: PreferenceResolver, protected modalService: NgbModal, private activatedRoute: ActivatedRoute, protected httpService: HttpService, protected http: HttpClient, protected appDataService: AppDataService, protected RTipService: ReceiverTipService, protected fieldUtilities: FieldUtilitiesService, protected authenticationService: AuthenticationService) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Everyone";
      this.tabs = [
        {
          title: "Everyone",
          component: this.tab1
        },
        {
          title: "Recipients only",
          component: this.tab2
        },
        {
          title: "Only me",
          component: this.tab3
        },
      ];
      this.loadTipDate();
      this.cdr.detectChanges();
    });
  }

  loadTipDate() {
    this.tip_id = this.activatedRoute.snapshot.paramMap.get("tip_id");
    const requestObservable: Observable<any> = this.httpService.receiverTip(this.tip_id);
    this.loading = true;
    this.RTipService.reset();
    requestObservable.subscribe(
      {
        next: (response: any) => {
          this.loading = false;
          this.RTipService.initialize(response);
          this.tip = this.RTipService.tip;
          this.activatedRoute.queryParams.subscribe((params: { [x: string]: any; }) => {
            this.tip.tip_id = params["tip_id"];
          });

          this.tip.receivers_by_id = this.utils.array_to_map(this.tip.receivers);
          this.score = this.tip.score;
          this.ctx = "rtip";
          this.showEditLabelInput = this.tip.label === "";
          this.preprocessTipAnswers(this.tip);
          this.tip.submissionStatusStr = this.utils.getSubmissionStatusText(this.tip.status, this.appDataService.submissionStatuses);
          this.submission = {};
        }
      }
    );
  }

  openGrantTipAccessModal(): void {
    this.utils.runUserOperation("get_users_names", {}, true).subscribe((response: any) => {
      const selectableRecipients: any = [];
      this.appDataService.public.receivers.forEach(async (receiver: { id: string | number; }) => {
        if (receiver.id !== this.authenticationService.session.user_id && !this.tip.receivers_by_id[receiver.id]) {
          selectableRecipients.push(receiver);
        }
      });
      const modalRef = this.modalService.open(GrantAccessComponent);
      modalRef.componentInstance.usersNames = response;
      modalRef.componentInstance.selectableRecipients = selectableRecipients;
      modalRef.componentInstance.confirmFun = (receiver_id: any) => {
        const req = {
          operation: "grant",
          args: {
            receiver: receiver_id.id
          },
        };
        this.httpService.tipOperation(req.operation, req.args, this.RTipService.tip.id)
          .subscribe(() => {
            this.reload();
          });
      };

      modalRef.componentInstance.cancelFun = null;
    });
  }

  openRevokeTipAccessModal() {
    this.utils.runUserOperation("get_users_names", {}, true).subscribe(
      {
        next: response => {
          const selectableRecipients: any = [];
          this.appDataService.public.receivers.forEach(async (receiver: { id: string | number; }) => {
            if (receiver.id !== this.authenticationService.session.user_id && this.tip.receivers_by_id[receiver.id]) {
              selectableRecipients.push(receiver);
            }
          });
          const modalRef = this.modalService.open(RevokeAccessComponent);
          modalRef.componentInstance.usersNames = response;
          modalRef.componentInstance.selectableRecipients = selectableRecipients;
          modalRef.componentInstance.confirmFun = (receiver_id: any) => {
            const req = {
              operation: "revoke",
              args: {
                receiver: receiver_id.id
              },
            };
            this.httpService.tipOperation(req.operation, req.args, this.RTipService.tip.id)
              .subscribe(() => {
                this.reload();
              });
          };
          modalRef.componentInstance.cancelFun = null;
        }
      }
    );
  }

  openTipTransferModal() {
    this.utils.runUserOperation("get_users_names", {}, true).subscribe(
      {
        next: (response: any) => {
          const selectableRecipients: any = [];
          this.appDataService.public.receivers.forEach(async (receiver: { id: string | number; }) => {
            if (receiver.id !== this.authenticationService.session.user_id && !this.tip.receivers_by_id[receiver.id]) {
              selectableRecipients.push(receiver);
            }
          });
          const modalRef = this.modalService.open(TransferAccessComponent);
          modalRef.componentInstance.usersNames = response;
          modalRef.componentInstance.selectableRecipients = selectableRecipients;
          modalRef.result.then(
            (receiverId) => {
              if (receiverId) {
                const req = {
                  operation: "transfer",
                  args: {
                    receiver: receiverId,
                  },
                };
                this.http
                  .put(`api/recipient/rtips/${this.tip.id}`, req)
                  .subscribe(() => {
                    this.router.navigate(["recipient", "reports"]).then();
                  });
              }
            },
            () => {
            }
          );
        }
      }
    );
  }

  reload(): void {
    const reloadCallback = () => {
      this.utils.reloadComponent();
    };

    this.appConfigServices.localInitialization(true, reloadCallback);
  }

  preprocessTipAnswers(tip: any) {
    this.tipService.preprocessTipAnswers(tip);
  }

  tipToggleStar() {
    this.httpService.tipOperation("set", {
      "key": "important",
      "value": !this.RTipService.tip.important
    }, this.RTipService.tip.id)
      .subscribe(() => {
        this.RTipService.tip.important = !this.RTipService.tip.important;
      });
  }

  tipNotify(enable: boolean) {
    this.httpService.tipOperation("set", {"key": "enable_notifications", "value": enable}, this.RTipService.tip.id)
      .subscribe(() => {
        this.RTipService.tip.enable_notifications = enable;
      });
  }

  tipDelete() {
    const modalRef = this.modalService.open(DeleteConfirmationComponent);
    modalRef.componentInstance.confirmFunction = () => {
    };
    modalRef.componentInstance.args = {
      tip: this.RTipService.tip,
      operation: "delete"
    };
  }

  setReminder() {
    const modalRef = this.modalService.open(TipOperationSetReminderComponent);
    modalRef.componentInstance.args = {
      tip: this.RTipService.tip,
      operation: "set_reminder",
      contexts_by_id: this.contexts_by_id,
      reminder_date: this.utils.getPostponeDate(this.appDataService.contexts_by_id[this.tip.context_id].tip_reminder),
      dateOptions: {
        minDate: new Date(this.tip.creation_date)
      },
      opened: false,

    };
  }

  tipPostpone() {
    const modalRef = this.modalService.open(TipOperationPostponeComponent);
    modalRef.componentInstance.args = {
      tip: this.RTipService.tip,
      operation: "postpone",
      contexts_by_id: this.contexts_by_id,
      expiration_date: this.utils.getPostponeDate(this.appDataService.contexts_by_id[this.tip.context_id].tip_timetolive),
      dateOptions: {
        minDate: new Date(this.tip.expiration_date),
        maxDate: this.utils.getPostponeDate(Math.max(365, this.appDataService.contexts_by_id[this.tip.context_id].tip_timetolive * 2))
      },
      opened: false,
      Utils: this.utils
    };
  }

  exportTip(tipId: any) {
    const param = JSON.stringify({});
    this.httpService.requestToken(param).subscribe
    (
      {
        next: async token => {
          const ans = await this.cryptoService.proofOfWork(token.id);
          window.open("api/recipient/rtips/" + tipId + "/export" + "?token=" + token.id + ":" + ans);
        }
      }
    );
  }
}
