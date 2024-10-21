import { ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from "@angular/core";
import {ActivatedRoute, Router} from "@angular/router";
import {AppConfigService} from "@app/services/root/app-config.service";
import {TipService} from "@app/shared/services/tip-service";
import { NgbModal, NgbNav, NgbNavItem, NgbNavItemRole, NgbNavLinkButton, NgbNavLinkBase, NgbNavContent, NgbNavOutlet } from "@ng-bootstrap/ng-bootstrap";
import {AppDataService} from "@app/app-data.service";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";
import {GrantAccessComponent} from "@app/shared/modals/grant-access/grant-access.component";
import {RevokeAccessComponent} from "@app/shared/modals/revoke-access/revoke-access.component";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {Observable} from "rxjs";
import {
  TipOperationSetReminderComponent
} from "@app/shared/modals/tip-operation-set-reminder/tip-operation-set-reminder.component";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {HttpClient} from "@angular/common/http";
import {
  TipOperationPostponeComponent
} from "@app/shared/modals/tip-operation-postpone/tip-operation-postpone.component";
import {CryptoService} from "@app/shared/services/crypto.service";
import {TransferAccessComponent} from "@app/shared/modals/transfer-access/transfer-access.component";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {Tab} from "@app/models/component-model/tab";
import {RecieverTipData} from "@app/models/reciever/reciever-tip-data";
import {Receiver} from "@app/models/app/public-model";
import {TipUploadWbFileComponent} from "@app/shared/partials/tip-upload-wbfile/tip-upload-wb-file.component";
import {TipCommentsComponent} from "@app/shared/partials/tip-comments/tip-comments.component";
import {ReopenSubmissionComponent} from "@app/shared/modals/reopen-submission/reopen-submission.component";
import {ChangeSubmissionStatusComponent} from "@app/shared/modals/change-submission-status/change-submission-status.component";
import { TranslateService, TranslateModule } from "@ngx-translate/core";
import { NgClass, NgTemplateOutlet } from "@angular/common";
import { TipInfoComponent } from "../../../shared/partials/tip-info/tip-info.component";
import { TipReceiverListComponent } from "../../../shared/partials/tip-receiver-list/tip-receiver-list.component";
import { TipQuestionnaireAnswersComponent } from "../../../shared/partials/tip-questionnaire-answers/tip-questionnaire-answers.component";
import { WhistleBlowerIdentityReceiverComponent } from "../whistleblower-identity-reciever/whistle-blower-identity-receiver.component";
import { TipFilesReceiverComponent } from "../../../shared/partials/tip-files-receiver/tip-files-receiver.component";
import { TipUploadWbFileComponent as TipUploadWbFileComponent_1 } from "../../../shared/partials/tip-upload-wbfile/tip-upload-wb-file.component";
import { TipCommentsComponent as TipCommentsComponent_1 } from "../../../shared/partials/tip-comments/tip-comments.component";
import { TranslatorPipe } from "@app/shared/pipes/translate";


@Component({
    selector: "src-tip",
    templateUrl: "./tip.component.html",
    standalone: true,
    imports: [
    NgClass,
    TipInfoComponent,
    TipReceiverListComponent,
    TipQuestionnaireAnswersComponent,
    WhistleBlowerIdentityReceiverComponent,
    TipFilesReceiverComponent,
    NgbNav,
    NgbNavItem,
    NgbNavItemRole,
    NgbNavLinkButton,
    NgbNavLinkBase,
    NgbNavContent,
    NgTemplateOutlet,
    NgbNavOutlet,
    TipUploadWbFileComponent_1,
    TipCommentsComponent_1,
    TranslateModule,
    TranslatorPipe
],
})
export class TipComponent implements OnInit {
  private translateService = inject(TranslateService);
  private tipService = inject(TipService);
  private appConfigServices = inject(AppConfigService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private cryptoService = inject(CryptoService);
  protected utils = inject(UtilsService);
  protected preferencesService = inject(PreferenceResolver);
  protected modalService = inject(NgbModal);
  private activatedRoute = inject(ActivatedRoute);
  protected httpService = inject(HttpService);
  protected http = inject(HttpClient);
  protected appDataService = inject(AppDataService);
  protected RTipService = inject(ReceiverTipService);
  protected authenticationService = inject(AuthenticationService);

  @ViewChild("tab1") tab1!: TemplateRef<TipUploadWbFileComponent | TipCommentsComponent>;
  @ViewChild("tab2") tab2!: TemplateRef<TipUploadWbFileComponent | TipCommentsComponent>;
  @ViewChild("tab3") tab3!: TemplateRef<TipUploadWbFileComponent | TipCommentsComponent>;

  tip_id: string | null;
  tip: RecieverTipData;
  score: number;
  ctx: string;
  showEditLabelInput: boolean;
  active: string;
  loading = true;
  redactMode:boolean = false;
  redactOperationTitle: string;
  tabs: Tab[];

  ngOnInit() {
    this.loadTipDate();
    this.cdr.detectChanges();
  }

  loadTipDate() {
    this.tip_id = this.activatedRoute.snapshot.paramMap.get("tip_id");
    this.redactOperationTitle = this.translateService.instant('Mask') + ' / ' + this.translateService.instant('Redact');
    const requestObservable: Observable<any> = this.httpService.receiverTip(this.tip_id);
    this.loading = true;
    this.RTipService.reset();
    requestObservable.subscribe(
      {
        next: (response: RecieverTipData) => {
          this.loading = false;
          this.RTipService.initialize(response);
          this.tip = this.RTipService.tip;
          this.activatedRoute.queryParams.subscribe((params: { [x: string]: string; }) => {
            this.tip.tip_id = params["tip_id"];
          });

          this.tip.receivers_by_id = this.utils.array_to_map(this.tip.receivers);
          this.score = this.tip.score;
          this.ctx = "rtip";
          this.showEditLabelInput = this.tip.label === "";
          this.preprocessTipAnswers(this.tip);
          this.tip.submissionStatusStr = this.utils.getSubmissionStatusText(this.tip.status, this.tip.substatus, this.appDataService.submissionStatuses);
          setTimeout(() => {
              this.initNavBar();
          });
        }
      }
    );
  }

  initNavBar() {
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
          title: "Me only",
          component: this.tab3
        },
      ];
    });
  }

  openGrantTipAccessModal(): void {
    this.utils.runUserOperation("get_users_names", {}, false).subscribe({
      next: response => {
        const selectableRecipients: Receiver[] = [];
        this.appDataService.public.receivers.forEach(async (receiver: Receiver) => {
          if (receiver.id !== this.authenticationService.session.user_id && !this.tip.receivers_by_id[receiver.id]) {
            selectableRecipients.push(receiver);
          }
        });
        const modalRef = this.modalService.open(GrantAccessComponent, {backdrop: 'static', keyboard: false});
        modalRef.componentInstance.usersNames = response;
        modalRef.componentInstance.selectableRecipients = selectableRecipients;
        modalRef.componentInstance.confirmFun = (receiver_id: Receiver) => {
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
      }
    });
  }

  openRevokeTipAccessModal() {
    this.utils.runUserOperation("get_users_names", {}, false).subscribe(
      {
        next: response => {
          const selectableRecipients: Receiver[] = [];
          this.appDataService.public.receivers.forEach(async (receiver: Receiver) => {
            if (receiver.id !== this.authenticationService.session.user_id && this.tip.receivers_by_id[receiver.id]) {
              selectableRecipients.push(receiver);
            }
          });
          const modalRef = this.modalService.open(RevokeAccessComponent, {backdrop: 'static', keyboard: false});
          modalRef.componentInstance.usersNames = response;
          modalRef.componentInstance.selectableRecipients = selectableRecipients;
          modalRef.componentInstance.confirmFun = (receiver_id: Receiver) => {
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
    this.utils.runUserOperation("get_users_names", {}, false).subscribe(
      {
        next: response => {
          const selectableRecipients: Receiver[] = [];
          this.appDataService.public.receivers.forEach(async (receiver: Receiver) => {
            if (receiver.id !== this.authenticationService.session.user_id && !this.tip.receivers_by_id[receiver.id]) {
              selectableRecipients.push(receiver);
            }
          });
          const modalRef = this.modalService.open(TransferAccessComponent, {backdrop: 'static', keyboard: false});
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

  openModalChangeState(){
    const modalRef = this.modalService.open(ChangeSubmissionStatusComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.arg={
      tip:this.tip,
      motivation:this.tip.motivation,
      submission_statuses:this.prepareSubmissionStatuses(),
    };

    modalRef.componentInstance.confirmFunction = (status:any,motivation: string) => {
      this.tip.status = status.status;
      this.tip.substatus = status.substatus;
      this.tip.motivation = motivation;
      this.updateSubmissionStatus();
    };
    modalRef.componentInstance.cancelFun = null;
  }

  openModalReopen(){
    const modalRef = this.modalService.open(ReopenSubmissionComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.confirmFunction = (motivation: string) => {
      this.tip.status = "opened";
      this.tip.substatus = "";
      this.tip.motivation = motivation;
      this.updateSubmissionStatus();
    };
    modalRef.componentInstance.cancelFun = null;
  }

  updateSubmissionStatus() {
    const args = {"status":  this.tip.status, "substatus": this.tip.substatus ? this.tip.substatus : "", "motivation":  this.tip.motivation || ""};
    this.httpService.tipOperation("update_status", args, this.tip.id)
      .subscribe(
        () => {
          this.utils.reloadComponent();
        }
      );
  };

  prepareSubmissionStatuses() {
    const subCopy:any[]= [...this.appDataService.submissionStatuses];
    const output = [];
    for (const x of subCopy) {
      if (x.substatuses.length) {
        for (const y of x.substatuses) {
          output.push({
            id: `${x.id}:${y.id}`,
            label: this.translateService.instant(x.label) + ' \u2013 ' + y.label,
            status: x.id,
            substatus: y.id,
            order: output.length,
          });
        }
      } else {
        x.status = x.id;
        x.substatus = "";
        x.order = output.length;
        output.push(x);
      }
    }
    return output;
  }

  reload(): void {
    const reloadCallback = () => {
      this.utils.reloadComponent();
    };

    this.appConfigServices.localInitialization(true, reloadCallback);
  }

  preprocessTipAnswers(tip: RecieverTipData) {
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
    const modalRef = this.modalService.open(DeleteConfirmationComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.confirmFunction = () => {
    };
    modalRef.componentInstance.args = {
      tip: this.RTipService.tip,
      operation: "delete"
    };
  }

  setReminder() {
    const modalRef = this.modalService.open(TipOperationSetReminderComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.args = {
      tip: this.RTipService.tip,
      operation: "set_reminder",
      contexts_by_id: this.appDataService.contexts_by_id,
      reminder_date: this.utils.getPostponeDate(this.appDataService.contexts_by_id[this.tip.context_id].tip_reminder),
      dateOptions: {
        minDate: new Date(this.tip.creation_date)
      },
      opened: false,
    };
  }

  tipPostpone() {
    const modalRef = this.modalService.open(TipOperationPostponeComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.args = {
      tip: this.RTipService.tip,
      operation: "postpone",
      contexts_by_id: this.appDataService.contexts_by_id,
      expiration_date: this.utils.getPostponeDate(this.appDataService.contexts_by_id[this.tip.context_id].tip_timetolive),
      dateOptions: {
        minDate: new Date(this.tip.expiration_date),
        maxDate: this.utils.getPostponeDate(Math.max(365, this.appDataService.contexts_by_id[this.tip.context_id].tip_timetolive * 2))
      },
      opened: false,
      Utils: this.utils
    };
  }

  exportTip(tipId: string) {
    const param = JSON.stringify({});
    this.httpService.requestToken(param).subscribe
    (
      {
        next: async token => {
          this.cryptoService.proofOfWork(token.id).subscribe(
            (result: number) => {
              window.open("api/recipient/rtips/" + tipId + "/export" + "?token=" + token.id + ":" + result);
              this.appDataService.updateShowLoadingPanel(false);
            }
          );
        }
      }
    );
  }

  toggleRedactMode() {
    this.redactMode = !this.redactMode;
  }

  listenToFields() {
    this.loadTipDate();
  }

  protected readonly JSON = JSON;
}
