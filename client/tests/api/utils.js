exports.validate_mandatory_headers = function(headers) {
  var mandatory_headers = {
    'X-XSS-Protection': '1; mode=block',
    'X-Robots-Tag': 'noindex',
    'X-Content-Type-Options': 'nosniff',
    'Expires': '-1',
    'Server': 'globaleaks',
    'Pragma':  'no-cache',
    'Cache-control': 'no-cache, no-store, must-revalidate'
  };

  for (var key in mandatory_headers) {
    if (headers[key.toLowerCase()] !== mandatory_headers[key]) {
      throw key + ' != ' + mandatory_headers[key];
    }
  }
};

exports.password = 'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#';

exports.invalid_admin_login = {
  'username': 'admin',
  'password': 'antani'
};

exports.valid_admin_login = {
  'username': 'admin',
  'password': exports.password
};

exports.get_user = function() {
  return {
    id: '',
    role: 'receiver',
    username: '',
    name: '',
    public_name: '',
    timezone: 0,
    language: 'en',
    description: '',
    pgp_key_public: '',
    pgp_key_expiration: '',
    pgp_key_fingerprint: '',
    pgp_key_info: '',
    pgp_key_remove: false,
    pgp_key_status: 'ignored',
    mail_address: 'receiver1@antani.gov', // used 'Recipient N' for population
    password: 'ringobongos3cur1ty',
    old_password: '',
    password_change_needed: false,
    state: 'enabled',
    deletable: 'true'
  }
};

exports.get_context = function() {
  return {
    id: '',
    name: 'Context 1',
    description: '',
    presentation_order: 0,
    tip_timetolive: 15,
    can_postpone_expiration: false,
    can_delete_submission: true,
    show_context: true,
    show_recipients_details: true,
    allow_recipients_selection: true,
    show_small_receiver_cards: false,
    enable_comments: true,
    enable_messages: true,
    enable_two_way_comments: true,
    enable_two_way_messages: true,
    enable_attachments: true,
    select_all_receivers: true,
    show_receivers_in_alphabetical_order: false,
    maximum_selectable_receivers: 0,
    recipients_clarification: '',
    status_page_message: '',
    questionnaire_id: '',
    receivers: []
  }
};

