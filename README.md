# Overview
Testkit-lite is a light-weight testing execution framework, composed by 5 components:

* "testkit-lite" is the command line interface(CLI) of Testkit-lite. Which provides comprehensive options for web/core testing and supports cross platform. In TCT, CATS usage, it is usually invoked as a background test runner.
* "test engines" is distribute engine responsible for handling various tests types.
* "com-module" is a common module responsible for handling interaction with target device, such as TIZEN device, Android device or localhost workstation.
* "testkit-stub" is a native process running on test target, which work as proxy between test suite and testkit-lite.
* "xDriver" is a special WebDriver implementation. 

#Architecture
![image-name](https://github.com/testkit/testkit-lite/blob/master/doc/resources/testkit-lite-arch.jpg)

The detailed description hosts on ["doc"](https://github.com/testkit/testkit-lite/tree/master/doc) folder.
