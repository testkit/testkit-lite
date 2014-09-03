## Dependency:

1. python2.7
2. python-setuptools python-support python-pip
   1. Ubuntu
      `sudo apt-get install python-setuptools python-support python-pip`
   2. Fedora(RHEL)
      `sudo yum install python-setuptools python-support python-pip`
   3. openSUSE(TIZEN)
      `sudo zypper install python-setuptools python-support python-pip`
3. python-requests(>=1.1)
   `sudo pip install requests`

## How to build Debian package:

Host with Ubuntu OS recommended.

Run the command below to build from source code and get Debian package:

`dpkg-buildpackage`

## How to build RPM package:

Host with Fedora OS recommended.

Run the command below to build from source code and get RPM package:

```
make -C packaging/
rpmbuild -tb packaging/testkit-lite_<version>.tar.gz --nodeps
```

Host with Ubuntu OS, we need to add a workaround to support the RPM build:

`rpmbuild --define 'python_sitelib /usr/lib/python2.7/site-packages' -tb packaging/testkit-lite_<version>.tar.gz --nodeps`

## How to install:

Install testkit lite from source code:

`sudo python setup.py install --record /var/log/testkit-lite.files`

Install testkit lite from debian build:

`sudo dpkg -i ../testkit-lite_<version>_all.deb`

## How to uninstall:

Uninstall testkit-lite installed with `setup.py install`:

`cat /var/log/testkit-lite.files | sudo xargs rm -rf`

Uninstall testkit-lite installed with `debian`:

`sudo dpkg -r testkit-lite`

## How to use:

1. You can run case on target:
   1. For web test cases:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml" -e 'WRTLauncher <package_name>'`

   2. For native test cases:

     `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml"`

2. You can run case in single mode :
   1. For web test cases:

      `testkit-lite -f "<somewhere>/<package_name>/tests.xml" -e 'WRTLauncher <package_name>' --comm localhost`

   2. For native test cases:

      `testkit-lite -f "<somewhere>/<package_name>/tests.xml" --comm localhost`

3. You can select on parser engine to simply conduct one or more `tests.xml` on target:

   `testkit-lite -f device:"<somewhere>/<package_name1>/tests.xml ... <somewhere>/<package_namen>/tests.xml" -e 'WRTLauncher <package_name1> ... <package_namen>'`

4. If you want to execute both auto and manual tests:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml"`

5. If you just want to execute manual tests:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml" -M`

6. If you just want to execute auto tests:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml" -A`

7. If you want to save test result to another file, by default it'll be under `/opt/testkit/lite/latest`:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml" -o <somewhere>/xxx.xml`

8. If you want to choose some filters:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml" --status level1 --type type1 ...`

9. If you want to run test according capability:

   `testkit-lite -f device:"<somewhere>/<package_name>/tests.xml" --capability capability.xml`

10. At last, you can freely compose the above parameters together:

    `testkit-lite -f <somewhere1>/tests.xml <somewhere2>/tests.xml -A --priority P1 --type type1 ...`

## Get Results:

Test report will be generated as tests.result.xml.The result will be under `/opt/testkit/lite/latest` after execution, you can also check the history results in `/opt/testkit/lite/yyyy-mm-dd-HH:MM:SS.NNNNNN`.

## View Results:

Test report can be viewed in HTML format, so the data in the xml result file looks more human friendly.

Please follow the following steps to view test report:

1. Copy files: `application.js back_top.png jquery.min.js testresult.xsl tests.css` under directory `/opt/testkit/lite/xsd/`
2. Put the files from step 1) under the same directory as the xml result file
3. Open xml result file with a web browser(IE, Chrome or Firefox)

## Known Issues:

N/A
