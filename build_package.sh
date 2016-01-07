#!/bin/bash

dpkg-buildpackage
ls .. -al
cp ../testkit-lite_*_all.deb ./dest/
chown travis:travis testkit-lite_*_all.deb
ls ./dest/ -al
