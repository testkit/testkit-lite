#!/bin/bash

dpkg-buildpackage
ls .. -al
cp ../testkit-lite_*_all.deb ./dest/
chown travis:travis ./dest/testkit-lite_*_all.deb
ls ./dest/ -al
