import {Injectable} from "@angular/core";
import {HttpService} from "@app/shared/services/http.service";
import {AppDataService} from "@app/app-data.service";
import {RecieverTipData} from "@app/models/reciever/reciever-tip-data";

@Injectable({
  providedIn: "root"
})
export class ReceiverTipService {
  tip: RecieverTipData = new RecieverTipData();

  constructor(private httpService: HttpService, private appDataService: AppDataService) {
  }

  reset(){
    this.tip = new RecieverTipData();
  }

  initialize(response: RecieverTipData) {
    this.tip = response;
    this.tip.context = this.appDataService.contexts_by_id[this.tip.context_id];
    this.tip.questionnaire = this.appDataService.questionnaires_by_id[this.tip.context["questionnaire_id"]];
    this.tip.msg_receiver_selected = null;
    this.tip.msg_receivers_selector = this.getMsgReceiversSelector();
  }


  operation(url: string, operation: string, args: {key:string,value:boolean}) {
    return this.httpService.runOperation(url, operation, args, false).subscribe({});
  }

  newComment(content: string, visibility: string) {
    const param = JSON.stringify({"id": this.tip.msg_receiver_selected, "content": content, "visibility": visibility});
    return this.httpService.rTipsRequestNewComment(param, this.tip.id);
  }

  private getMsgReceiversSelector() {
    const msgReceiversSelector = [];

    for (const receiver of this.tip.receivers) {
      if (this.appDataService.receivers_by_id[receiver.id]) {
        const r = this.appDataService.receivers_by_id[receiver.id];
        msgReceiversSelector.push({
          key: r.id,
          value: r.name
        });
      }
    }

    return msgReceiversSelector;
  }
}
