export class WbTipData {
  id: string;
  creation_date: string;
  update_date: string;
  expiration_date: string;
  progressive: number;
  context_id: string;
  questionnaires: Questionnaire[];
  tor: boolean;
  mobile: boolean;
  reminder_date: string;
  enable_two_way_comments: boolean;
  enable_attachments: boolean;
  enable_whistleblower_identity: boolean;
  last_access: string;
  score: number;
  status: string;
  substatus: any;
  receivers: Receiver[];
  comments: any[];
  rfiles: any[];
  wbfiles: any[];
  data: Data;
  context: any = {};
  questionnaire: any;
  additional_questionnaire: any;
  msg_receiver_selected: any;
  msg_receivers_selector: any[];
  tip_id: any;
  receivers_by_id: any;
  submissionStatusStr: any;
  label: any;
  fields: any;
  whistleblower_identity_field: any;
  answers = {};
}

export class Questionnaire {
  steps: Step[];
  answers = {};
}

export class Step {
  id: string;
  questionnaire_id: string;
  order: number;
  enabled = true;
  triggered_by_score: number;
  triggered_by_options: any[];
  children: Children[];
  label: string;
  description: string;
}

export class Children {
  id: string;
  instance: string;
  editable: boolean;
  type: string;
  template_id: string;
  template_override_id: string;
  step_id: string;
  fieldgroup_id: string;
  multi_entry: boolean;
  required: boolean;
  preview: boolean;
  attrs: Attrs;
  x: number;
  y: number;
  width: number;
  triggered_by_score: number;
  triggered_by_options: TriggeredByOption[];
  options: Option[];
  children: any[];
  label: string;
  description: string;
  hint: string;
  placeholder: string;
}

export class Attrs {
  input_validation?: InputValidation;
  max_len?: MaxLen;
  min_len?: MinLen;
  regexp?: Regexp;
  display_alphabetically?: DisplayAlphabetically;
}

export class InputValidation {
  name: string;
  type: string;
  value: string;
}

export class MaxLen {
  name: string;
  type: string;
  value: string;
}

export class MinLen {
  name: string;
  type: string;
  value: string;
}

export interface Regexp {
  name: string;
  type: string;
  value: string;
}

export class DisplayAlphabetically {
  name: string;
  type: string;
  value: boolean;
}

export class TriggeredByOption {
  field: string;
  option: string;
  sufficient: boolean;
}

export class Option {
  id: string;
  order: number;
  block_submission: boolean;
  score_points: number;
  score_type: string;
  trigger_receiver: any[];
  hint1: string;
  hint2: string;
  label: string;
}

export class Receiver {
  id: string;
  name: string;
}

export class Data {
  whistleblower_identity: any;
  whistleblower_identity_provided: boolean = false;
}