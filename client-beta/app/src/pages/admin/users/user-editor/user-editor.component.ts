import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {NgForm} from "@angular/forms";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {AppDataService} from "@app/app-data.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {Constants} from "@app/shared/constants/constants";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {Observable} from "rxjs";

@Component({
  selector: "src-user-editor",
  templateUrl: "./user-editor.component.html"
})
export class UserEditorComponent implements OnInit {
  @Input() user: any;
  @Input() users: any;
  @Input() index: any;
  @Input() editUser: NgForm;
  @Output() dataToParent = new EventEmitter<string>();

  editing = false;
  setPasswordArgs: any = {};
  changePasswordArgs: any = {};
  passwordStrengthScore: number = 0;
  nodeData: any = {};
  preferenceData: any = {};
  authenticationData: any = {};
  appServiceData: any = {};
  protected readonly Constants = Constants;

  constructor(private modalService: NgbModal, private appDataService: AppDataService, private preference: PreferenceResolver, private authenticationService: AuthenticationService, private nodeResolver: NodeResolver, private utilsService: UtilsService) {

  }

  ngOnInit(): void {
    if (this.nodeResolver.dataModel) {
      this.nodeData = this.nodeResolver.dataModel;
    }
    if (this.preference.dataModel) {
      this.preferenceData = this.preference.dataModel;
    }
    if (this.authenticationService) {
      this.authenticationData = this.authenticationService;
    }
    if (this.appDataService) {
      this.appServiceData = this.appDataService;
    }
    this.setPasswordArgs = {
      user_id: this.user.id,
      password: ""
    };
    this.changePasswordArgs = {
      password_change_needed: ""
    };
  }

  toggleEditing() {
    this.editing = !this.editing;
  }

  onPasswordStrengthChange(score: number) {
    this.passwordStrengthScore = score;
  }

  disable2FA(user: any) {
    this.utilsService.runAdminOperation("disable_2fa", {"value": user.user.id}, true).subscribe();
  }

  setPassword(setPasswordArgs: any) {
    this.utilsService.runAdminOperation("set_user_password", setPasswordArgs, true).subscribe();
    this.user.newpassword = false;
    this.setPasswordArgs.password = "";
  }

  saveUser(userData: any) {
    const user = userData;
    if (user.pgp_key_remove) {
      user.pgp_key_public = "";
    }
    if (user.pgp_key_public !== "") {
      user.pgp_key_remove = false;
    }
    return this.utilsService.updateAdminUser(userData.id, userData).subscribe(_ => {
      this.sendDataToParent();
    });
  }

  sendDataToParent() {
    this.dataToParent.emit();
  }

  deleteUser(user: any) {
    this.openConfirmableModalDialog(user, "").subscribe();
  }

  openConfirmableModalDialog(arg: any, scope: any): Observable<string> {
    scope = !scope ? this : scope;
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DeleteConfirmationComponent, {});
      modalRef.componentInstance.arg = arg;
      modalRef.componentInstance.scope = scope;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.utilsService.deleteAdminUser(arg.id).subscribe(_ => {
          this.utilsService.deleteResource(this.users,arg);
        });
      };
    });
  }

  resetUserPassword(user: any) {
    this.utilsService.runAdminOperation("send_password_reset_email", {"value": user.id}, true).subscribe();
  }

  loadPublicKeyFile(files: any) {
    if (files && files.length > 0) {
      this.utilsService.readFileAsText(files[0])
        .then((txt: string) => {
          this.user.pgp_key_public = txt;
        });
    }
  };

  toggleUserEscrow(user: any) {
    this.user.escrow = !this.user.escrow;
    this.utilsService.runAdminOperation("toggle_user_escrow", {"value": user.id}, true).subscribe();
  }
}