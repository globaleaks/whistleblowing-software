#!/bin/sh

# for some not investigated reasons, the tests need to be started one by one.

testfiles=`ls globaleaks/tests/test_*.py globaleaks/tests/*/test_*.py`
for tf in $testfiles;
    do trial $tf
done
