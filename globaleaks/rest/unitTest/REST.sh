#!/bin/sh

dumpdir="/tmp/RESTtest"

# perform_test $testname $url $method $response $request 
perform_test() {

    testname=$1
    url=$2
    method=$3
    expected_response=$4
    payload=$5

    of=$dumpdir$url
    mkdir -p $of

    echo "\n\nstarting test with method: $method in $url..."
    echo "press enter to continue..."
    read Y

    case $method in
        "PUT")
            echo 'curl -i -o '$of$method'.out -D '$of$method' -H "Accept: application/json" -X PUT -d '$payload' http://127.0.0.1:8082'$url
            curl -i -o $of$method.out -D $of$method -H "Accept: application/json" -X PUT -d "$payload" http://127.0.0.1:8082$url
            ;;
        "POST")
            echo 'curl -i -o '$of$method'.out -D '$of$method' -H "Accept: application/json" -X POST -d '$payload' http://127.0.0.1:8082'$url
            curl -i -o $of$method".out" -D $of$method -H "Accept: application/json" -X POST -d "$payload" http://127.0.0.1:8082$url
            ;;
        "DELETE")
            echo 'curl -i -o '$of$method'.out -D '$of$method' -H "Accept: application/json" -X DELETE -d '$payload' http://127.0.0.1:8082'$url
            curl -i -o $of$method".out" -D $of$method -H "Accept: application/json" -X DELETE -d "$payload" http://127.0.0.1:8082$url
            ;;
        "GET")
            echo 'curl -i -o '$of$method'.out -D '$of$method' -H "Accept: application/json" -X GET http://127.0.0.1:8082'$url
            curl -i -o $of$method".out" -D $of$method -H "Accept: application/json" -X GET http://127.0.0.1:8082$url
            ;;
        ?)
            echo "invalid method $method"
            exit
            ;;
    esac

    echo "test $testname ($method $url) completed"
    ls -l $of$method*
    head -2 $of$method.out

}

# START HERE
if [ ! -d $dumpdir ]; then
    mkdir $dumpdir
    echo "created $dumpdir"
else
    echo "$dumpdir already exists"
fi

ID='"random-ID"'
fileDict=' {   "filename": "string", "comment": "string", "size": "Int", "content_type": "string", "date": "Time", "CleanedMetaData": "int" }'

localizationDict=' {   "IT" : "Io mi chiamo Mario.", "EN" : "Is a me, Mario!!1!", "FR" : "je m_appelle Marìò, pppffff" }'
formFieldsDict=' {   "element-name": "string", "element-type": "Enum", "default-value": "string", "required": "Bool" }'

receiverDescriptionDict=' {   "ReceiverID": '${ID}', "CanDeleteSubmission": "Bool", 
            "CanPostponeExpiration": "Bool", "CanConfigureNotification": "Bool", "CanConfigureDelivery": "Bool", 
            "receiver_name": "string", "receiver_description": "string",
            "receiver_tags": "string", "contact_data": "string", "creation_date": "Time",
            "update_date": "Time" "module_id": $ID,
            "module_dependent_data": '${formFieldsDict}', "module_dependent_stats": "Array" }'
        
nodePropertiesDict='{   "AnonymousSubmissionOnly": "Bool", "AdminAreReceivers": "Bool", "NodeProvideDocsPublication": "Bool",
            "FixedCorpusOfReceiver": "Bool", "ReceiverAreAnonymous": "Bool" }'

moduleDataDict=' {   "name": '${ID}', "active": "Bool", "module_type": "string",
            "module_name": "string" "description": "string", "admin_options": '${formFieldsDict}', 
            "user_options": '${formFieldsDict}',  "service_message": "string" }'


groupDescriptionDict=' {   "group_id" : '${ID}', "group_name": "string", "description" : '${localizationDict}', 
            "spoken_language": "Array, list of spoken languages", "group_tags": "string", 
            "receiver_list": "Array", "group_id": "string", "associated_module": '${moduleDataDict}'"creation_date": "Time", 
            "update_date": "Time" }'

tipStatistics='{ "tip_access_ID": '${ID}' "tip_title": "string", "last_access": "Time", "last_comment": "Time", "notification_msg": "string",
            "delivery_msg": "string", "expiration_date": "Time", "pertinence_overall": "Int", "requested_fields": '${formFieldsDict}',
            "context_name": "string", "group": '${groupDescriptionDict}'}'

tipIndexDict=' {   "tip_access_ID": '${ID}', "tip_title": "string", "context_ID": '${ID}', "group_ID": '${ID}', 
            "notification_adopted": "string", "notification_msg": "string", "delivery_adopted": "string",
            "delivery_msg": "string", "expiration_date": "Time", "creation_date": "Time",
            "update_date": "Time" }'

contextDescriptionDict='{ "context_id": '${ID}', "name": '${localizationDict}', 
            "groups": [ '${groupDescriptionDict}', '${groupDescriptionDict}', ],
            "fields": '${formFieldsDict}', "description": "string", "style": "string",
            "creation_date": "Time", "update_date": "Time" }'

# ## -- Recurring JSON variables
#echo $ID
#echo $fileDict
#echo $localizationDict
#echo $formFieldsDict
#echo $receiverDescriptionDict
#echo $nodePropertiesDict
#echo $moduleDataDict
# ## ---------------------------


testname='P1'
url='/node/'
method='GET'
request="unused"
response='{ "name": "string",
              "statistics": '${nodeStatisticsDict}', "node_properties": '${nodePropertiesDict}', "contexts": 
              [ '${contextDescriptionDict}', '${localizationDict}', ],
              "public_site": "string", "hidden_service": "string", "url_schema": "string" }'
perform_test $testname $url $method $response $request 

testname='P1Put'
url='/node/'
method='PUT'
request="unused"
response='{ "name": "string",
              "statistics": '${nodeStatisticsDict}', "node_properties": '${nodePropertiesDict}', "contexts": 
              [ '${contextDescriptionDict}', '${localizationDict}', ],
              "public_site": "string", "hidden_service": "string", "url_schema": "string" }'
perform_test $testname $url $method $response $request 


# REMIND: needed tests are:
# P1-P7, T1-T6, R1-R2, A1-A5
# 
# P1 `/node/`
# P2 `/submission`
# P3 `/submission/<submission_id>`
# P4 `/submission/<submission_id>/submit_fields`
# P5 `/submission/<submission_id>/submit_group`
# P6 `/submission/<submission_id>/finalize`
# P7 `/submission/<submission_id>/upload_file`
# T1 `/tip/<string auth t_id>`
# T2 `/tip/<uniq_Tip_$ID>/add_comment`
# T3 `/tip/<uniq_Tip_$ID>/update_file`
# T4 `/tip/<string t_id>/finalize_update`
# T5 `/tip/<string t_id>/download_material`
# T6 `/tip/<string t_id>/pertinence`
# R1 `/receiver/<string t_id>/overview`
# R2 `/receiver/<string t_id>/<string module_name>`
# A1 `/admin/node/`
# A2 `/admin/contexts/`
# A3 `/admin/groups/<context_$ID>/`                     (test implemented)
# A4 `/admin/receivers/<group_$ID>/`
# A5 `/admin/modules/<string module_type>/`
# 

# CURD A3
testname='A3C'
method='PUT'
request=' { "group": '${groupDescriptionDict}' }'
perform_test $testname $url $method $response $request 

testname='A3U'
method='POST'
request='{ "group": '${groupDescriptionDict}', "create": "Bool", "delete": "Bool", }'
perform_test $testname $url $method $response $request 

testname='A3R'
url='/admin/group/context_ID_baah/'
method='GET'
request="unused"
response='{"groups":'${groupDescriptionDict}', "modules_available": 
              [ '${moduleDataDict}', '${moduleDataDict}', ]}'
perform_test $testname $url $method $response $request 

testname='A3D'
method='DELETE'
request=' { "group": '${groupDescriptionDict}' }'
perform_test $testname $url $method $response $request 

# end of A3
# --- switched to unitTestRest.py
# --- switched to unitTestRest.py
# --- switched to unitTestRest.py
echo "development and unitTest, switched to unitTestRest.py"

testname='A4R'
url='/admin/receiver/group_ID_XYZ/'
method='GET'
response=' { "receivers" : [ '${receiverDescriptionDict}', '${receiverDescriptionDict}', ] }'

method='POST'
request='{ "delete": "Bool", "create: "Bool", "receiver": '${receiverDescriptionDict}', }'

method='DELETE'
request=' { "receiver": '${receiverDescriptionDict}' }'

method='PUT'
request=' { "receiver": '${receiverDescriptionDict}' }'


# `/submission`
# 
#     :GET
#         This creates an empty submission and returns the ID
#         to be used when referencing it as a whistleblower.
#         ID is a random 64bit integer
#         * Response:
#           { 
#               "submission_id": '${ID",
#               "creation_time": "Time"
#           }
#           Status code: 201 (Created)
# 
#         * Error handling:
#         If configuration REQUIRE anonymous upload, and the WB is not anonymous
#           Status Code: 415 (Unsupported Media Type)
#           { "error_code": "Int", "error_message": "Anonymity required to perform a submission" }
# 
# **common behaviour in /submission/<submission_$ID>**
# 
# Error handling
# 
#     If submission_$ID is invalid
#         Status Code: 204 (No Content)
#         { "error_code": "Int", "error_message": "submission ID is invalid" }
# 
# `/submission/<submission_$ID>/status`
# 
# This interface represent the state of the submission. Will show the
# current uploaded data, choosen group, and file uploaded.
# 
# permit to update fields content and group selection.
# 
#     :GET
#         Returns the currently submitted fields, selected group, and uploaded files.
#         * Response:
#           { 
#             "fields": '${formFieldsDict",
#             "group_matrix": [ '${ID", "$ID" ],
#             "uploaded_file": [ '${fileDict", {} ]
#             "creation_time": "Time"
#           }
# 
#           Would be accepted "fields" with missing "Required" fields,
#           because the last check is performed in "finalize" interface below.
# 
#     :POST
#         * Request:
#           { 
#             "fields": '${formFieldsDict",
#             "group_matrix": [ '${ID", "$ID" ]
#           }
# 
#         * Response:
#           Status Code: 202 (accepted)
# 
#         * Error handling:
#           As per "common behaviour in /submission/<submission_$ID/*"
#           If group ID is invalid:
#             { "error_code": "Int", "error_message": "group selected ID is invalid" }
# 
# 
# `/submission/<submission_$ID>/finalize`, 
# 
#     :POST
#         checks if all the "Required" fields are present, then 
#         completes the submission in progress and returns a receipt.
#         The WB may propose a receipt (because is a personal secret 
#         like a password, afterall)
# 
#         * Request (optional, see "Rensponse Variant" below):
#           { 
#             "proposed-receipt": "string"
#           }
# 
#         * Response (HTTP code 200):
#           If the receipt is acceptable with the node requisite (minimum length
#           respected, lowecase/uppercase, and other detail that need to be setup
#           during the context configuration), rs saved as authenticative secret for 
#           the WB Tip, is echoed back to the client Status Code: 201 (Created)
# 
#           Status Code: 200 (OK)
#           { "receipt": "string" }
# 
#         * Variant Response (HTTP code 201):
#           If the receipt do not fit node prerequisite, or is expected but not provide
#           the submission is finalized, and the server create a receipt. 
#           The client print back to the WB, who record that 
# 
#           Status Code: 201 (Created)
#           { "receipt": "string" }
# 
# 
#         * Error handling:
#           As per "common behaviour in /submission/<submission_$ID/*"
# 
#           If the field check fail
#           Status Code: 406 (Not Acceptable)
#           { "error_code": "Int", "error_message": "fields requirement not respected" }
# 
# 
# `/submission/<submission_$ID>/upload_file`, 
# 
#     XXX
#     XXX
# 
#     This interface supports resume. 
#     This interface expose the JQuery FileUploader and the REST/protocol
#     implemented on it.
#     FileUploader has a dedicated REST interface to handle start|stop|delete.
#     Need to be studied in a separate way.
# 
#     The uploaded files are shown in /status/ with the appropriate
#     '${fileDict" description structure.
# 
# **At the moment is under research:**
# https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1
# 
#     XXX
#     XXX
# 
# 
# `/tip/<uniq_Tip_$ID>` (shared between Receiver and WhistleBlower)
# 
#     :GET
#         Permit either to WB authorized by Receipt, or to Receivers.
#         Both actors have a single, authorized and univoke "t_id".
# 
#         Returns the content of the submission with the specified ID.
#         Inside of the request headers, if supported, the password for accessing
#         the tip can be passed. This returns a session cookie that is then
#         used for all future requests to be authenticated.
# 
#         * Response:
#           Status Code: 200 (OK)
#           { 
#             "fields": '${formFieldsDict",
#             "comments": [ { "author_name": "string",
#                             "date": "Time",
#                             "comment": "string" },
#                           { }
#                         ],
# 
#             "delivery_method": "string",
#             "delivery_data": "string",
#             "notification_method": "string",
#             "notification_data": "string",
# 
#             "folders": [ { "id": "Int" ,
#                            "data": "Time",
#                            "description": "string",
#                            "delivery_way" : "string" },
#                          { }
#                        ],
#             "statistics": '${tipStatistics",
#           }
# 
#         * Error handling:
#           If Tip $ID invalid
#           Status Code: 204 (No Content)
#           { "error_code": "Int", "error_message": "requested Tip ID is expired or invalid" }
# 
#     :POST
#         Used to delete a submission if the users has sufficient priviledges.
#         Administrative settings can configure if all or some, receivers or
#         WB, can delete the submission. (by default they cannot).
# 
#         * Request:
#         {
#             "delete": "Bool"
#         }
# 
#         * Response:
#           If the user has right permissions:
#           Status Code: 200 (OK)
# 
#           If the user has not permission:
#           Status Code: 204 (No Content)
# 
# 
# `/tip/<uniq_Tip_$ID>/add_comment` (shared between Receiver and WhistleBlowe)
# 
#     Permit either to WB authorized by Receipt, or to Receivers.
#     adds a new comment to the submission.
# 
#     :POST
#         * Request:
#             {
#                 "comment": "string" 
#             }
# 
#         * Response:
#           Status Code: 200 (OK)
#         * Error handling 
#           as per `GET /tip/<uniq_Tip_$ID>/`
# 
# 
# `/tip/<uniq_Tip_$ID>/update_file` (WhistleBlower only)
# 
#     perform update operations. If a Material Set has been started, the file is appended
#     in the same pack. A Material Set is closed when the `finalize_update` is called.
# 
#     :GET
#         return the unfinalized elements accumulated by the whistleblower. The unfinalized
#         material are promoted as "Set" if the WB do not finalize them before a configurable
#         timeout.
# 
#         * Request: /
#         * Response:
#         every object is repeated for every "NOT YET finalized Material Set":
#         { 
#           "finalized-material-date": "Time",
#           "description": "string",
#           "uploaded": [ $fileDict, {} ],
#         }
# 
#      :POST
# 
#         This interface need to be reviewed when jQuery FileUploader,
#         and expose the same interface of upload_file
# 
#        * Error handling:
#          As per jQueryFileUploader
#          and as per `/tip/<uniq:_Tip_$ID>/`
# 
# 
# `/tip/<uniq_Tip_$ID>/finalize_update` (WhistleBlowing)
# 
#     Used to add description in the Material set not yet completed (optional)
#     Used to complete the files upload, completing the Material Set.
# 
#     :POST
#         * Request:
#         { "description": "string" }
# 
#         Field description is optional
# 
#         * Response:
#             if files are available to be finalized:
#             Status Code: 202 (Accepted)
# 
#         * Error handling as per `/tip/<uniq_Tip_$ID>/`
# 
# 
# `/tip/<uniq_Tip_$ID>/download_material` (Receiver - **Delivery module dependent**)
# 
#     This REST interface would be likely present, and in future would be moved
#     in a separate documentation of optional REST interfaces. Is implemented by
#     the module "delivery_local" (default module for delivery), has the property
#     to permit a limited amount of download, an then invalidate itself.
# 
#     Used to download the material from the
#     submission. Can only be requested if the user is a Receiver and the
#     relative download count is < max_downloads.
# 
#     :GET
#         * Request:
#              { "folder_ID": '${ID" }
# 
#         * Response:
#              Status Code: 200 (OK)
# 
# 
# `/tip/<uniq_Tip_$ID>/pertinence` (Receiver only)
# 
#     Optional (shall not be supported by configuration settings)
#     express a vote on pertinence of a certain submission.
#     This can only be done by a receiver that has not yet voted.
# 
#     :POST
#         * Request: 
#           { "pertinence-vote": "Bool" }
# 
#         * Response:
#           Status Code: 202 (Accepted)
#         _ Error handling as per `/tip/<string t_id>/`
# 
# 
# Receiver API
# 
# `/receiver/<uniq_Tip_$ID>/overview`
# 
# This interface expose all the receiver related info, require one valid Tip authentication.
# This interface returns all the options available for the receiver (notification and delivery)
# and contain the require field (empty or compiled)
# 
# depends from the node administator choose and delivery/notification extension, the capability
# to be configured by the user.
# 
# (tmp note: overview is the replacement of the previous release "Bouquet")
# note, this access model imply that a receiver can configured their preferences only having a
# Tip opened for him. This default behaviour would be overrided by modules.
# 
#     :GET
#        * Response:
#          Stauts Code: 200 (OK)
#          {
#              "tips": [ '${tipIndexDict", { } ]
#              "notification-method": [ '${moduleDataDict", { } ],
#              "delivery-method": [ '${moduleDataDict", { }  ],
#              "receiver-properties": '${receiverDescriptionDict"
#          }
# 
#     :(GET and POST)
#         * Error code:
#         _ If t_id is invalid
#           Status Code: 204 (No Content)
#           { "error_code": "Int", "error_message": "requested Tip ID is expired or invalid" }
# 
# `/receiver/<string t_id>/<string module_name>`
# 
# Every module need a way to specify a personal interface where receive preferences, this would be
# used in Notification and Delivery modules.
# 
#     :GET 
#         * Response:
#           Status Code: 200 (OK)
#           {
#               "module_description": '${localizationDict"
#               "pref": '${moduleDataDict"
#           }
# 
#     :POST
#           {
#               "pref": '${moduleDataDict"
#           }
# 
# Admin API
# 
# **common behaviour in Admin resorces**
# 
#     The following API has a shared element: they have a GET, that return
#     the list of the resource data, and a POST, that await for a single
#     instance of a data, and two optional boolean "create" and "delete".
#     Every instance of data has an $ID inside, the identify in an unique
#     way the object.
# 
#     :POST
#       * Request
#       {
#           "create": "Bool",
#           "delete": "Bool",
#           "example": '${SpecificObject"
#       }
# 
#       * Response
# 
#     if "create" is True, 
#         SpecificObjet["id"] is ignored, SpecificObject is copied and a new resource created.
#         return as GET
# 
#     if "delete" is True
#         if SpecificObject["id"] exists
#             the context is deleted
#             return as GET
#         else
#             Error Code 400 (Bad Request)
#             { "error_code": "Int", "error_message" : "Invalid $ID in request" }
# 
#     if SpecifiedObject["id"] exists
#         if "create" AND "delete" are False
#             the context is updated
#             return as GET
#         else
#             Error Code 400 (Bad Request)
#             { "error_code": "Int", "error_message" : "Invalid $ID in request" }
# 
# 
# `/admin/contexts/`
# 
#     List, create, delete and update all the contexts in the Node.
# 
#     :GET
#         Returns a json object containing all the contexts information.
#         * Response:
#           Status Code: 200 (OK)
#         {
#           "contexts": [ '${contextDescriptionDict", { } ]
#         }
# 
#     :POST
#         * Request:
#           Implements the fallback if PUT and DELETE method do not work
#         { 
#           "create": "Bool",
#           "delete": "Bool",
#           "context": '${ContexDescription",
#         }
# 
#     :DELETE
#         Remove an existing context, same effect of POST with delete = True
#         {
#           "context": '${ContexDescription"
#         }
# 
#     :PUT
#         Create a new context, same effect of POST with create = True
#         {
#           "context": '${ContexDescription"
#         }
# 
#         * Response:
#           As per **common behaviour in Admin resorces**
# 

####### CUT HERE 
# `/admin/group/<context_$ID>/`
# `/admin/receiver/<group_$ID>/`
# 
#### END CUT HERE
# 
# `/admin/modules/<string module_type>/`
# 
# These interface permit to list, configure, enable and disasble all the 
# available modules.
# The modules are flexible implementation extending a specific part of GLBackend,
# The modules would be part of a restricted group of elements:
# 
#     TODO METTI QUI LA LISTA DELLE ABSTRACT CLASS
# 
# and one of those keyword need to be requested in the REST interface.
# 
# 
#     :GET
#         * Response:
#         {
#           "modules_available": [ '${moduleDataDict", { } ]
#           "context_applied": { 
#                       "module_$ID": [ "context_$ID", "context_$ID" ], 
#                       { } }
#         }
# 
#     :POST
#         * Request:
#         {
#           "status": "Bool",
#           "targetContext": [ "context_$ID", "context_$ID" ],
#           "module_settings": '${moduleDataDict"
#         }
# 
#         * Response:
# 
#           "status" if is True mean that the module would be activated,
#           else, is False, mean that the module would be deactivated.
#           The previous status of the module is not checked, but during
#           the activation some module dependend check may fail, in those
#           cases:
# 
#             Error Code 501 (Not Implemented)
#               { "error_code": "Int", "error_message" : "module error details" }
# 
#           Otherwise, if request is accepted:
#             Status Code 200 (OK)
# 
# `/admin/node`
# 
#     :GET
#         Returns a json object containing all the information of the node.
#         * Response:
#             Status Code: 200 (OK)
#             {
#               "name": "string",
#               "statistics": '${nodeStatisticsDict",
#               "private_stats": { },
#               "node_properties": '${nodePropertiesDict",
#               "contexts": [ '${contextDescriptionDict", { }, ],
#               "description": '${localizationDict",
#               "public_site": "string",
#               "hidden_service": "string",
#               "url_schema": "string"
#              }
# 
#         "private_stats" need do be defined, along with $nodeStatisticsDict.
# 
#     :POST
#         Changes the node public node configuration settings
#         * Request:
#             {
#               "name": "string",
#               "node_properties": '${nodePropertiesDict",
#               "description": '${localizationDict",
#               "public_site": "string",
#               "hidden_service": "string",
#               "url_schema": "string"
# 
#               "enable_stats": [ ],
#               "do_leakdirectory_update": "Bool",
#               "new_admin_password": "string",
# 
#              }
# 
#         "enable_stats" need to be defined along with $nodeStatisticsDict.
