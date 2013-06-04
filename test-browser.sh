#!/bin/sh

#By local file:///
#sudo cp -a tests/webapi-w3c-fileapi-tests /opt
#./testkit-lite -f $PWD/tests/webapi-w3c-fileapi-tests/tests.xml -e "chromium-browser --allow-file-access-from-files web/index.html" -A

#By http://
#mkdir -p $HTTP_ROOT/opt && cp -a tests/webapi-w3c-fileapi-tests $HTTP_ROOT/opt
#cp -a web $HTTP_ROOT
#./testkit-lite -f $PWD/tests/webapi-w3c-fileapi-tests/tests.xml -e "chromium-browser http://localhost/web/index.html" -A
