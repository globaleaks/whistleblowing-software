import {Component} from "@angular/core";
import {ngxCsv} from "ngx-csv";
import {UsersResolver} from "@app/shared/resolvers/users.resolver";
import {userResolverModel} from "@app/models/resolvers/user-resolver-model";

@Component({
  selector: "src-auditlog-tab2",
  templateUrl: "./audit-log-tab2.component.html"
})
export class AuditLogTab2Component {
  currentPage = 1;
  pageSize = 20;
  users: any = new userResolverModel();

  constructor(protected usersResolver: UsersResolver) {
  }

  ngOnInit() {
    this.loadAuditLogData();
  }

  loadAuditLogData() {
    this.users = this.usersResolver.dataModel;
  }

  getPaginatedData(): any[] {
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    return this.users.slice(startIndex, endIndex);
  }

  exportAuditLog() {
    new ngxCsv(JSON.stringify(this.users), "users", {

      headers: ["id", "creation_date", "username", "salt", "role", "enabled", "last_login", "name", "description", "public_name", "mail_address", "change_email_address", "language", "password_change_needed", "password_change_date", "pgp_key_fingerprint", "pgp_key_public", "pgp_key_expiration", "pgp_key_remove", "picture", "tid", "notification", "encryption", "escrow", "two_factor", "forcefully_selected", "can_postpone_expiration", "can_delete_submission", "can_grant_access_to_reports", "can_transfer_access_to_reports", "can_edit_general_settings", "clicked_recovery_key", "accepted_privacy_policy", "contexts"],
    });
  }
}