GL.constant("CONSTANTS", {
   /* The email regexp restricts email addresses to less than 400 chars. See #1215 */
   "email_regexp": /^([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}[\w]{1,100}$/,
   "email_regexp_or_empty": /^([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}[\w]{1,100}$|^$/,
   "country_code_regexp_or_empty": /^([a-zA-Z]){2}$|^$/,
   "number_regexp": /^\d+$/,
   "phonenumber_regexp": /^[+]?[ \d]+$/,
   "hostname_regexp": /^[a-z0-9-.]+$|^$/,
   "https_regexp": /^https:\/\/([a-z0-9-]+)\.(.*)$|^$/,
   "secure_or_local_url_regexp": /^https:\/\/([a-z0-9-]+)\.(.*)$|^\/(.*)$|^$/,
   "uuid_regexp": /^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/
});
