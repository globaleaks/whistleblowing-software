import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {PasswordRecoveryResponseModel} from "@app/models/authentication/password-recovery-response-model";
import {Router} from "@angular/router";


@Injectable({
  providedIn: "root"
})
export class HttpService {

  getPublicResource(): Observable<any> {
    return this.httpClient.get<any>("api/public", {observe: "response"});
  }

  requestAuthTokenLogin(param: string): Observable<any> {
    return this.httpClient.post("api/auth/tokenauth", param);
  }

  requestGeneralLogin(param: string): Observable<any> {
    return this.httpClient.post("api/auth/authentication", param);
  }

  requestWhistleBlowerLogin(param: string, authHeader: any): Observable<any> {
    return this.httpClient.post("api/auth/receiptauth", param, {headers: authHeader});
  }

  requestDeleteUserSession(): Observable<any> {
    return this.httpClient.delete("api/auth/session");
  }

  requestDeleteTenant(url: any): Observable<any> {
    return this.httpClient.delete(url);
  }

  requestUpdateTenant(url: any, data: any): Observable<any> {
    return this.httpClient.put(url, data);
  }

  authorizeIdentity(url: any, data: any): Observable<any> {
    return this.httpClient.put(url, data);
  }

  deleteDBFile(id: string): Observable<any> {
    return this.httpClient.delete("api/recipient/rfiles/" + id);
  }

  requestOperations(data: any, header?: any): Observable<any> {
    return this.httpClient.put("api/user/operations", data, header);
  }

  requestOperationsRecovery(data: any, confirmation: any): Observable<any> {
    const headers = {"X-Confirmation": confirmation};
    return this.httpClient.put("api/user/operations", data, {headers});
  }

  updatePreferenceResource(data: any): Observable<any> {
    return this.httpClient.put("api/user/preferences", data);
  }

  requestChangePassword(param: string): Observable<any> {
    return this.httpClient.put<PasswordRecoveryResponseModel>("api/user/reset/password", param);
  }

  requestToken(param: string): Observable<any> {
    return this.httpClient.post("api/auth/token", param);
  }

  requestResetLogin(param: string): Observable<any> {
    return this.httpClient.post("api/user/reset/password", param);
  }

  requestSignup(param: string): Observable<any> {
    return this.httpClient.post("api/signup", param);
  }

  requestWizard(param: string): Observable<any> {
    return this.httpClient.post("api/wizard", param);
  }

  requestSignupToken(token: any): Observable<any> {
    return this.httpClient.post("api/signup/" + token, {});
  }

  requestTenantSwitch(url: any): Observable<any> {
    return this.httpClient.get(url);
  }

  requestReportSubmission(param: string): Observable<any> {
    return this.httpClient.post("api/whistleblower/submission", param);
  }

  requestSuppor(param: string): Observable<any> {
    return this.httpClient.post("api/support", param);
  }

  requestNewComment(param: string): Observable<any> {
    return this.httpClient.post("api/whistleblower/wbtip/comments", param);
  }

  requestPreferenceResource(): Observable<any> {
    return this.httpClient.get("api/admin/preferences");
  }

  requestUserPreferenceResource(): Observable<any> {
    return this.httpClient.get("api/user/preferences");
  }

  requestNodeResource(): Observable<any> {
    return this.httpClient.get("api/admin/node");
  }

  updateNodeResource(data: any): Observable<any> {
    return this.httpClient.put("api/admin/node", data);
  }

  requestUsersResource(): Observable<any> {
    return this.httpClient.get("api/admin/users");
  }

  requestContextsResource(): Observable<any> {
    return this.httpClient.get("api/admin/contexts");
  }

  requestTenantsResource(): Observable<any> {
    return this.httpClient.get("api/admin/tenants");
  }

  requestQuestionnairesResource(): Observable<any> {
    return this.httpClient.get("api/admin/questionnaires");
  }

  requestTipResource(): Observable<any> {
    return this.httpClient.get("api/admin/auditlog/tips");
  }

  requestNotificationsResource(): Observable<any> {
    return this.httpClient.get("api/admin/notification");
  }

  requestNetworkResource(): Observable<any> {
    return this.httpClient.get("api/admin/network");
  }

  requestUpdateNetworkResource(param: any): Observable<any> {
    return this.httpClient.put("api/admin/network", param);
  }

  requestTlsConfigResource(): Observable<any> {
    return this.httpClient.get("api/admin/config/tls");
  }

  requestDeleteTlsConfigResource(): Observable<any> {
    return this.httpClient.delete("api/admin/config/tls");
  }

  requestRedirectsResource(): Observable<any> {
    return this.httpClient.get("api/admin/redirects");
  }

  requestPostRedirectsResource(param: any): Observable<any> {
    return this.httpClient.post("api/admin/redirects", param);
  }

  requestDeleteRedirectsResource(id: any): Observable<any> {
    return this.httpClient.delete("api/admin/redirects/" + id);
  }

  requestUpdateTlsConfigFilesResource(name: any, authHeader: any, data: any): Observable<any> {
    return this.httpClient.put("api/admin/config/tls/files/" + name, data, {headers: authHeader});
  }

  requestDeleteTlsConfigFilesResource(name: string): Observable<any> {
    return this.httpClient.delete("api/admin/config/tls/files/" + name);
  }

  requestAdminAcmeResource(param: any, authHeader: any): Observable<any> {
    return this.httpClient.post("api/admin/config/acme/run", param, {headers: authHeader});
  }

  requestCSRContentResource(name: any, param: any): Observable<any> {
    return this.httpClient.post("api/admin/config/tls/files/" + name, param);
  }

  requestCSRDirectContentResource(param: any): Observable<any> {
    return this.httpClient.post("api/admin/config/csr/gen", param);
  }

  downloadCSRFile(): Observable<Blob> {
    const url = "api/admin/config/tls/files/csr";
    return this.httpClient.get(url, {responseType: "blob"});
  }

  disableTLSConfig(tls: any, authHeader: any): Observable<any> {
    const url = "api/admin/config/tls";
    return this.httpClient.put(url, tls, {headers: authHeader});
  }

  enableTLSConfig(tls: any, authHeader: any): Observable<any> {
    const url = "api/admin/config/tls";
    return this.httpClient.post(url, tls, {headers: authHeader});
  }

  whistleBlowerTip(): Observable<any> {
    return this.httpClient.get("api/whistleblower/wbtip");
  }

  whistleBlowerTipUpdate(param: any): Observable<any> {
    return this.httpClient.post("api/whistleblower/wbtip/fillform", param);
  }

  whistleBlowerIdentityUpdate(param: any): Observable<any> {
    return this.httpClient.post("api/whistleblower/wbtip/identity", param);
  }

  requestAdminFieldTemplateResource(): Observable<any> {
    return this.httpClient.get("api/admin/fieldtemplates");
  }

  requestUpdateAdminNodeResource(data: any): Observable<any> {
    return this.httpClient.put("api/admin/node", data);
  }

  requestAdminL10NResource(lang: any): Observable<any> {
    return this.httpClient.get("api/admin/l10n/" + lang);
  }

  requestUpdateAdminL10NResource(data: any, lang: any): Observable<any> {
    return this.httpClient.put("api/admin/l10n/" + lang, data);
  }

  requestDefaultL10NResource(lang: any): Observable<any> {
    return this.httpClient.get("/data/l10n/" + lang + ".json");
  }

  requestAdminAuditLogResource(): Observable<any> {
    return this.httpClient.get("api/admin/auditlog");
  }

  addQuestionnaire(param: any): Observable<any> {
    return this.httpClient.post("api/admin/questionnaires", param);
  }

  requestDeleteAdminQuestionnaire(id: any): Observable<any> {
    return this.httpClient.delete("api/admin/questionnaires/" + id);
  }

  requestUpdateAdminQuestionnaire(id: any, param: any): Observable<any> {
    return this.httpClient.put("api/admin/questionnaires/" + id, param);
  }

  requestJobResource(): Observable<any> {
    return this.httpClient.get("api/admin/auditlog/jobs");
  }

  receiverTipResource(): Observable<any> {
    return this.httpClient.get("api/recipient/rtips");
  }

  iarResource(): Observable<any> {
    return this.httpClient.get("api/custodian/iars");
  }

  receiverTip(id: any): Observable<any> {
    return this.httpClient.get("api/recipient/rtips/" + id);
  }

  rTipsRequestNewComment(param: any, id: any): Observable<any> {
    return this.httpClient.post(`api/recipient/rtips/${id}/comments`, param);
  }

  requestStatusesResource(): Observable<any> {
    return this.httpClient.get("api/admin/statuses");
  }

  addSubmissionStatus(param: any): Observable<any> {
    return this.httpClient.post("api/admin/statuses", param);
  }

  fetchTenant(): Observable<any> {
    return this.httpClient.get("api/admin/tenants");
  }

  addTenant(param: any): Observable<any> {
    return this.httpClient.post("api/admin/tenants", param);
  }

  accessIdentity(id: any): Observable<any> {
    return this.httpClient.post(`api/recipient/rtips/${id}/iars`, {"request_motivation": ""});
  }

  requestAddAdminUser(param: any): Observable<any> {
    return this.httpClient.post("api/admin/users", param);
  }

  requestUpdateAdminUser(id: any, param: any): Observable<any> {
    return this.httpClient.put("api/admin/users/" + id, param);
  }

  requestDeleteAdminUser(id: any): Observable<any> {
    return this.httpClient.delete("api/admin/users/" + id);
  }

  requestAddAdminContext(param: any): Observable<any> {
    return this.httpClient.post("api/admin/contexts", param);
  }

  requestAddAdminQuestionnaireStep(param: any): Observable<any> {
    return this.httpClient.post("api/admin/steps", param);
  }

  requestUpdateAdminQuestionnaireStep(id: any, param: any): Observable<any> {
    return this.httpClient.put("api/admin/steps/" + id, param);
  }

  requestDeleteAdminQuestionareStep(id: any): Observable<any> {
    return this.httpClient.delete("api/admin/steps/" + id);
  }

  requestAddAdminQuestionnaireField(param: any): Observable<any> {
    return this.httpClient.post("api/admin/fields", param);
  }

  requestAddAdminQuestionnaireFieldTemplate(param: any): Observable<any> {
    return this.httpClient.post("api/admin/fieldtemplates", param);
  }

  requestUpdateAdminQuestionnaireField(id: any, param: any): Observable<any> {
    return this.httpClient.put("api/admin/fields/" + id, param);
  }

  requestDeleteAdminQuestionareField(id: any): Observable<any> {
    return this.httpClient.delete("api/admin/fields/" + id);
  }

  requestUpdateAdminContext(param: any, id: any): Observable<any> {
    return this.httpClient.put("api/admin/contexts/" + id, param);
  }

  requestDeleteAdminContext(id: any): Observable<any> {
    return this.httpClient.delete("api/admin/contexts/" + id);
  }

  requestDeleteStatus(url: string): Observable<any> {
    return this.httpClient.delete(url);
  }

  requestUpdateStatus(url: string, param: any): Observable<any> {
    const headers = {"content-type": "application/json"};
    return this.httpClient.put(url, param, {headers});
  }

  requestUpdateAdminNotification(notification: any): Observable<any> {
    return this.httpClient.put("api/admin/notification", notification);
  }

  runOperation(url: string, operation: string, args: any, refresh: boolean) {

    const data = {
      operation: operation,
      args: args
    };

    if (refresh) {
      setTimeout(() => {
        const currentUrl = this.router.url;
        this.router.navigateByUrl("routing", {skipLocationChange: true, replaceUrl: true}).then(() => {
          this.router.navigate([currentUrl]).then();
        });
      }, 150);
    }

    return this.httpClient.put(url, data);
  }

  tipOperation = (operation: string, args: any, tipId: any) => {
    const req = {
      "operation": operation,
      "args": args
    };
    return this.httpClient.put("api/recipient/rtips/" + tipId, req);
  };

  constructor(private httpClient: HttpClient, private router: Router) {
  }
}
