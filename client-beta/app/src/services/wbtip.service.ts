import {Injectable} from "@angular/core";
import {HttpService} from "@app/shared/services/http.service";
import {WbTipData} from "@app/models/whistleblower/wb-tip-data";
import {AppDataService} from "@app/app-data.service";

@Injectable({
  providedIn: "root"
})
export class WbtipService {
  tip: WbTipData = new WbTipData();

  constructor(private httpService: HttpService, private appDataService: AppDataService) {
  }

  initialize(response: WbTipData) {
    this.tip = response;
    this.tip.context = this.appDataService.contexts_by_id[this.tip.context_id];
    this.tip.questionnaire = this.appDataService.questionnaires_by_id[this.tip.context["questionnaire_id"]];
    this.tip.additional_questionnaire = this.appDataService.questionnaires_by_id[this.tip.context["additional_questionnaire_id"]];
    this.tip.msg_receiver_selected = null;
    this.tip.msg_receivers_selector = [];

    this.tip.receivers.forEach((r: any) => {
      const receiver = this.appDataService.receivers_by_id[r.id];
      if (receiver) {
        this.tip.msg_receivers_selector.push({
          key: receiver.id,
          value: receiver.name
        });
      }
    });
  }

  sendContent(content: string, visibility: string) {
    const requestData = JSON.stringify({
      "id": this.tip.msg_receiver_selected,
      "content": content,
      "visibility": visibility
    });

    return this.httpService.requestNewComment(requestData);
  }


  newComment(content: string, visibility: string) {
    return this.sendContent(content, visibility);
  }
}
