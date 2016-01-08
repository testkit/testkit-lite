#!/bin/bash

dpkg-buildpackage
chown travis:travis ../testkit-lite_*_all.deb
ls .. -al
