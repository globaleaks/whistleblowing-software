## CurTeG

Curl Tester for GLBackend

curteg is a simple python script that implement the GLClient request structure and perform
that to the GLBackend service.

Its useful for test avoiding javascript or the mobile render, whenever a bug happen during the
development.

Its not intended as console client for GlobaLeaks, but the sadic fantasy of the users never
would be understimated.

### curted usage examples 

    $ python curteg.py [API selection] [verbosity options] (HOSTNAME:PORT)

all the option are optionals

The verbosity options are:

    request
    response

The API selection are made with the [U|R|T|A] + number

  * U1 = /node/
  * U2 = /submission/
  * U3 = /submission/(submission_id)/
  * U4 = /submission/(submission_id)/finalize
  * U5 = /submission/(submission_id)/upload_file

  * R1 = /receiver/(string t_id)/overview
  * R2 = /receiver/(string t_id)/(module_type)/

  * A1 = /admin/node/
  * A2 = /admin/contexts/
  * A3 = /admin/receivers/(context_ID)/
  * A4 = /admin/modules/(context_ID)/(module_type)/

  * T1 = /tip/(Tip_ID)
  * T2 = /tip/(Tip_ID)/add_comment
  * T3 = /tip/(Tip_ID)/update_file
  * T4 = /tip/(Tip_ID)/finalize_update
  * T5 = /tip/(Tip_ID)/download_material
  * T6 = /tip/(Tip_ID)/pertinence

