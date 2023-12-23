import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {PasswordRecoveryResponseModel} from "@app/models/authentication/password-recovery-response-model";
import {Router} from "@angular/router";
import {tenantResolverModel} from "@app/models/resolvers/tenant-resolver-model";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {networkResolverModel} from "@app/models/resolvers/network-resolver-model";
import {FileResource} from "@app/models/component-model/file-resources";
import {TlsConfig} from "@app/models/component-model/tls-confiq";
import {Answers} from "@app/models/reciever/reciever-tip-data";
import {NewQuestionare} from "@app/models/admin/new-questionare";
import {Step, questionnaireResolverModel} from "@app/models/resolvers/questionnaire-model";
import {NewUser} from "@app/models/admin/new-user";
import {userResolverModel} from "@app/models/resolvers/user-resolver-model";
import {NewContext} from "@app/models/admin/new-context";
import {NewStep} from "@app/models/admin/new-step";
import {NewField} from "@app/models/admin/new-field";
import {FieldTemplate} from "@app/models/admin/field-Template";
import {Field} from "@app/models/resolvers/field-template-model";
import {contextResolverModel} from "@app/models/resolvers/context-resolver-model";
import {Status, Substatus} from "@app/models/app/public-model";
import {notificationResolverModel} from "@app/models/resolvers/notification-resolver-model";


@Injectable({
  providedIn: "root"
})
export class HttpService {

  constructor(private httpClient: HttpClient, private router: Router) {
  }

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

  requestDeleteTenant(url: string): Observable<any> {
    return this.httpClient.delete(url);
  }

  requestUpdateTenant(url: string, data: tenantResolverModel): Observable<any> {
    return this.httpClient.put(url, data);
  }

  authorizeIdentity(url: string, data: {reply: string, reply_motivation: string}): Observable<any> {
    return this.httpClient.put(url, data);
  }

  deleteDBFile(id: string): Observable<any> {
    return this.httpClient.delete("api/recipient/rfiles/" + id);
  }

  requestOperations(data: {operation: string,args: {[key:string]:string}}, header?:any): Observable<any> {
    return this.httpClient.put("api/user/operations", data, header);
  }

  requestOperationsRecovery(data: {operation: string,args: {[key:string]:string}}, confirmation: string): Observable<any> {
    const headers = {"X-Confirmation": confirmation};
    return this.httpClient.put("api/user/operations", data, {headers});
  }

  updatePreferenceResource(data: string): Observable<any> {
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

  requestWizard(param: string): Observable<object> {
    return this.httpClient.post("api/wizard", param);
  }

  requestSignupToken(token: string): Observable<any> {
    return this.httpClient.post("api/signup/" + token, {});
  }

  requestTenantSwitch(url: string): Observable<any> {
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
  requestUserPreferenceResource(): Observable<any> {
    return this.httpClient.get("api/user/preferences");
  }

  requestNodeResource(): Observable<any> {
    return this.httpClient.get("api/admin/node");
  }

  updateNodeResource(data: nodeResolverModel): Observable<any> {
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

  requestUpdateNetworkResource(param: networkResolverModel): Observable<any> {
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

  requestPostRedirectsResource(param:{path1:string,path2:string}): Observable<any> {
    return this.httpClient.post("api/admin/redirects", param);
  }

  requestDeleteRedirectsResource(id: string): Observable<any> {
    return this.httpClient.delete("api/admin/redirects/" + id);
  }

  requestUpdateTlsConfigFilesResource(name: string, authHeader: any, data: FileResource): Observable<any> {
    return this.httpClient.put("api/admin/config/tls/files/" + name, data, {headers: authHeader});
  }

  requestDeleteTlsConfigFilesResource(name: string): Observable<any> {
    return this.httpClient.delete("api/admin/config/tls/files/" + name);
  }

  requestAdminAcmeResource(param: {}, authHeader: any): Observable<any> {
    return this.httpClient.post("api/admin/config/acme/run", param, {headers: authHeader});
  }

  requestCSRContentResource(name: string, param: FileResource): Observable<any> {
    return this.httpClient.post("api/admin/config/tls/files/" + name, param);
  }

  requestCSRDirectContentResource(param:{country: string;province: string;city: string;company: string;department: string;email: string}): Observable<any> {
    return this.httpClient.post("api/admin/config/csr/gen", param);
  }

  downloadCSRFile(): Observable<Blob> {
    const url = "api/admin/config/tls/files/csr";
    return this.httpClient.get(url, {responseType: "blob"});
  }

  disableTLSConfig(tls: TlsConfig, authHeader: any): Observable<any> {
    const url = "api/admin/config/tls";
    return this.httpClient.put(url, tls, {headers: authHeader});
  }

  enableTLSConfig(tls: TlsConfig, authHeader: any): Observable<any> {
    const url = "api/admin/config/tls";
    return this.httpClient.post(url, tls, {headers: authHeader});
  }

  whistleBlowerTip(): Observable<any> {
    return this.httpClient.get("api/whistleblower/wbtip");
  }

  whistleBlowerTipUpdate(param: {cmd: string,answers: Answers}): Observable<any> {
    return this.httpClient.post("api/whistleblower/wbtip/fillform", param);
  }

  whistleBlowerIdentityUpdate(param: {identity_field_id:string,identity_field_answers:Answers}): Observable<any> {
    return this.httpClient.post("api/whistleblower/wbtip/identity", param);
  }

  requestAdminFieldTemplateResource(): Observable<any> {
    return this.httpClient.get("api/admin/fieldtemplates");
  }

  requestUpdateAdminNodeResource(data: nodeResolverModel): Observable<any> {
    return this.httpClient.put("api/admin/node", data);
  }

  requestAdminL10NResource(lang: string): Observable<any> {
    return this.httpClient.get("api/admin/l10n/" + lang);
  }

  requestUpdateAdminL10NResource(data: {[key: string]: string}, lang: string): Observable<any> {
    return this.httpClient.put("api/admin/l10n/" + lang, data);
  }

  requestDefaultL10NResource(lang: string): Observable<any> {
    return this.httpClient.get("/data/l10n/" + lang + ".json");
  }

  requestAdminAuditLogResource(): Observable<any> {
    return this.httpClient.get("api/admin/auditlog");
  }

  addQuestionnaire(param:NewQuestionare): Observable<any> {
    return this.httpClient.post("api/admin/questionnaires", param);
  }

  requestDeleteAdminQuestionnaire(id: string): Observable<any> {
    return this.httpClient.delete("api/admin/questionnaires/" + id);
  }

  requestUpdateAdminQuestionnaire(id: string, param: questionnaireResolverModel): Observable<any> {
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

  receiverTip(id: string | null): Observable<any> {
    return this.httpClient.get("api/recipient/rtips/" + id);
  }

  rTipsRequestNewComment(param: string, id: string): Observable<any> {
    return this.httpClient.post(`api/recipient/rtips/${id}/comments`, param);
  }

  requestStatusesResource(): Observable<any> {
    return this.httpClient.get("api/admin/statuses");
  }

  addSubmissionStatus(param: {label: string,order: number}): Observable<any> {
    return this.httpClient.post("api/admin/statuses", param);
  }

  fetchTenant(): Observable<any> {
    return this.httpClient.get("api/admin/tenants");
  }

  addTenant(param: {name:string,active:boolean,mode:string,subdomain:string}): Observable<any> {
    return this.httpClient.post("api/admin/tenants", param);
  }

  accessIdentity(id: string): Observable<any> {
    return this.httpClient.post(`api/recipient/rtips/${id}/iars`, {"request_motivation": ""});
  }

  requestAddAdminUser(param: NewUser): Observable<any> {
    return this.httpClient.post("api/admin/users", param);
  }

  requestUpdateAdminUser(id: string, param: userResolverModel): Observable<any> {
    return this.httpClient.put("api/admin/users/" + id, param);
  }

  requestDeleteAdminUser(id: string): Observable<any> {
    return this.httpClient.delete("api/admin/users/" + id);
  }

  requestAddAdminContext(param: NewContext): Observable<any> {
    return this.httpClient.post("api/admin/contexts", param);
  }

  requestAddAdminQuestionnaireStep(param: NewStep): Observable<any> {
    return this.httpClient.post("api/admin/steps", param);
  }

  requestUpdateAdminQuestionnaireStep(id: string, param: Step): Observable<any> {
    return this.httpClient.put("api/admin/steps/" + id, param);
  }

  requestDeleteAdminQuestionareStep(id: string): Observable<any> {
    return this.httpClient.delete("api/admin/steps/" + id);
  }

  requestAddAdminQuestionnaireField(param: NewField): Observable<any> {
    return this.httpClient.post("api/admin/fields", param);
  }

  requestAddAdminQuestionnaireFieldTemplate(param: FieldTemplate): Observable<any> {
    return this.httpClient.post("api/admin/fieldtemplates", param);
  }

  requestUpdateAdminQuestionnaireField(id: string, param: Step | Field): Observable<any> {
    return this.httpClient.put("api/admin/fields/" + id, param);
  }

  requestDeleteAdminQuestionareField(id: string): Observable<any> {
    return this.httpClient.delete("api/admin/fields/" + id);
  }

  requestUpdateAdminContext(param: contextResolverModel, id: string): Observable<any> {
    return this.httpClient.put("api/admin/contexts/" + id, param);
  }

  requestDeleteAdminContext(id: string): Observable<any> {
    return this.httpClient.delete("api/admin/contexts/" + id);
  }

  requestDeleteStatus(url: string): Observable<any> {
    return this.httpClient.delete(url);
  }

  requestUpdateStatus(url: string, param: Substatus|Status): Observable<any> {
    const headers = {"content-type": "application/json"};
    return this.httpClient.put(url, param, {headers});
  }

  requestUpdateAdminNotification(notification: notificationResolverModel): Observable<any> {
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

  tipOperation = (operation: string, args: any, tipId: string) => {
    const req = {
      "operation": operation,
      "args": args
    };
    return this.httpClient.put("api/recipient/rtips/" + tipId, req);
  };

}
