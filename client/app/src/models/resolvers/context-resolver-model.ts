export class contextResolverModel {
  id: string;
  hidden: boolean;
  tip_timetolive: number;
  tip_reminder: number;
  select_all_receivers: boolean;
  maximum_selectable_receivers: number;
  show_recipients_details: boolean;
  allow_recipients_selection: boolean;
  enable_comments: boolean;
  enable_two_way_comments: boolean;
  enable_attachments: boolean;
  score_threshold_medium: number;
  score_threshold_high: number;
  order: number;
  show_receivers_in_alphabetical_order: boolean;
  show_steps_navigation_interface: boolean;
  questionnaire_id: string;
  additional_questionnaire_id: string;
  receivers: string[];
  picture: boolean;
  name: string;
  description: string;
}