
## Simple develoing notes

bin/globaleaksadmin safexport workingdir/db/glbackend-10.db print 

## using ramdisk with unit test

    mount -t tmpfs -o size=10M tmpfs ./testing_dir/

Ran 130 tests in 71.365s
PASSED (successes=130)

real	1m13.023s
user	1m7.724s
sys	0m4.828s

# without ramdisk 

    umount ./testing_dir && rm -rf testing_dir) :

Ran 130 tests in 112.558s
PASSED (successes=130)

real	1m54.200s
user	1m11.036s
sys	0m7.624s


