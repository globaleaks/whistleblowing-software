import {Injectable} from "@angular/core";

@Injectable({
  providedIn: "root"
})
export class SubmissionResourceService {

  context_id: number;
  receivers: [];
  identity_provided: false;
  answers: any;
  answer: 0;
  score: 0;
}
