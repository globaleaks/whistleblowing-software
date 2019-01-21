# -*- coding: utf-8 -*-
#
#  Tar utilities
import os
import tarfile


def tardir(dst, src):
    with tarfile.open(dst, "w:gz") as tf:
        tf.dereference = True

        def exclude(x):
            if x.startswith(dst):
                return True

            return False

        tf.add(src, arcname=os.path.basename(src), exclude=exclude)
