import {Answers} from "@app/models/reciever/reciever-tip-data";

export class submissionResourceModel {
    context_id: number;
    receivers: string[];
    identity_provided: boolean = false;
    answers: Answers;
    answer: 0;
    score: 0;
}