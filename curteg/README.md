## CurTeG

Curl Tester for GLBackend

curteg is a simple python script that implement the GLClient request structure and perform
that to the GLBackend service.

Its useful for test avoiding javascript or the mobile render, whenever a bug happen during the
development.

Its not intended as console client for GlobaLeaks, but the sadic fantasy of the users never
would be understimated.

### curted usage examples 

    $ python curteg.py [API selection] [HTTP METHOD LIST] [verbosity options] (HOSTNAME:PORT)

all the option are optionals

The verbosity options are:

    request
    response
    verbose

The API selection are made with the [U|R|T|A] + number

  * U1 = /node/
  * U2 = /submission/
  * U3 = /submission/(submission_id)/
  * U4 = /submission/(submission_id)/finalize
  * U5 = /submission/(submission_id)/upload_file

  * R1 = /receiver/(Tip_ID)/overview
  * R2 = /receiver/(Tip_ID)/(module_type)/

  * T1 = /tip/(Tip_ID)
  * T2 = /tip/(Tip_ID)/add_comment
  * T3 = /tip/(Tip_ID)/update_file
  * T4 = /tip/(Tip_ID)/finalize_update
  * T5 = /tip/(Tip_ID)/download_material
  * T6 = /tip/(Tip_ID)/pertinence

  * A1 = /admin/node/
  * A2 = /admin/contexts/
  * A3 = /admin/receivers/(context_ID)/
  * A4 = /admin/modules/(context_ID)/(module_type)/

The method should be GET POST DELETE PUT, and permit to request only the specified method(s)

### special options

Two special options are available, that enable more creative usage and testing combos for
GLBackend.

    hand
    print-[*]

As the other options, they can be put in every section of the command line.

**hand** permit to edit by hand the JSON struct that is ready to be sent, it open a vim editor
and a pickle object (ok, nasty to be edited, but works)

**print-[*]** work in conjunction with other keywords, like "print-submission\_id". The output
printed is just the receiver submission\_id in this case, and its useful for script sequence
of operations that perform a complete submission, in example, or automated operations.

### ID selection

Tip, Context and Submission IDs shall be set via command line, like:

    python curteg.py U3 sid s_aFBKvAqTiZWhaIiHVnqSRUtFOGOnsAbeABMTrmaDUPoRyXyWUu

Just for remind, the expected format of the ID is defined in
**/globaleaks/utils/validregexps.py**

### Combined script

more complex sequence shall be organized using curteg, and emulate large amount of submission,
access and so on. Some example shall be found in the scripts subdirectory
