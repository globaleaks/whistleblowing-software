interface Option {
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

interface Step {
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
  attrs: any;
  x: number;
  y: number;
  width: number;
  triggered_by_score: number;
  triggered_by_options: any[];
  options: Option[];
  children: Step[];
  label: string;
  description: string;
  hint: string;
  placeholder: string;
}

export class questionnaireResolverModel {
  id: string;
  editable: boolean;
  name: string;
  key: string;
  steps: Step[];
}