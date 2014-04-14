## Development hardcore option

**Option --XXX permit to specify some options that broke GLBackend security and reliability **

Usage:

    --XXX number_position_one,string_position_two,string_position_three


  * number_position_one: the number of seconds added every time the current data is checked, this can emulate GLBackend run in the future of the specified seconds
  * string_position_two: if this string is enabled, every UUIDv4 is generated not by random sources but with YOURSTRING-XXX-XXX-[sameformat]-NNN where NNN is an incremental number. Its considered if something longer that two bytes is present
  * string_position_three if something longer than 1 byte is present, enable mlockall


## Monitoring GLBackend behavior 

watch -d bin/globaleaksadmin safexport workingdir/db/glbackend-12.db print 

## using ramdisk with unit test

    mount -t tmpfs -o size=10M tmpfs ./testing_dir/

Ran 130 tests in 71.365s
PASSED (successes=130)

real	1m13.023s
user	1m7.724s
sys	0m4.828s

# without ramdisk 

    umount ./testing_dir && rm -rf testing_dir 

Ran 130 tests in 112.558s
PASSED (successes=130)

real	1m54.200s
user	1m11.036s
sys	0m7.624s


