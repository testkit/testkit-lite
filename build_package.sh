#!/bin/bash

dpkg-buildpackage
ls .. -al
cp ../testkit-lite_*_all.deb ./dest/
