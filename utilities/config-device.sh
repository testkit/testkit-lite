#!/bin/bash
#set -x

DIRP=`readlink -f $0`
PWD=`dirname "$DIRP"`
PLATFORM="tizen"
SERNO=""
EXE_MODE=""
DEV_ARCH=""

NAME=app
while getopts --tizen-user: name
do
    case $name in 
    --tizen-user)
        NAME=$name;;
    esac
done
show_usage()
{
    echo "Usage: $0 command [parameters]"
    echo "commands:"
    echo "    $0 [--install] [platform=<tizen/android/localhost>] [deviceid=<serial_no>]    - Install web-utilities to device,'--install' can be omitted."
    echo "    $0 --purge [platform=<tizen/android/localhost>] [deviceid=<serial_no>]        - Clean up web-utilities from device."
    echo "     --tizen-user=* --It will install package to tizen-user directory"
    exit 0
}

sdb_init()
{
    echo "set sdb root on. Please wait..."
    sdb $SERNO root on
    if [ $? -ne 0 ]; then
        echo "Error: set root mode for Tizen device failed."
        echo "       Please confirm your device connected to machine and flashed with proper TIZEN image"
        echo "       And then re-run tct-config-device.sh script"
        exit 255
    fi
    echo "init document_root. Please wait..."
    sdb $SERNO shell "mkdir -p /home/$NAME/content/tct/" > /dev/null 2>&1
    sdb $SERNO shell "chmod 777 /home/$NAME/content/tct/" > /dev/null 2>&1
    echo "get tizen device cpu abi type. Please wait..."
    STRM=`sdb $SERNO shell "uname -m"`
    STRM=`echo $STRM | sed 's/\\r//g' | awk '{print $NF}'`
    echo "get cpu_arch: $STRM"
    case "$STRM" in
      i686*) DEV_ARCH="ia32" ;;
      arm*) DEV_ARCH="arm" ;;
      x86_64*) DEV_ARCH="x64" ;;
      *) echo "unsupported cpu_arch of current device" && exit 255 ;;
    esac
}

kill_process_sdb()
{
    echo "Kill process $1. Please wait..."
    PRID=`sdb $SERNO shell "ps aux | grep $1 | grep -v grep" | awk '{print $2}'  `
    if [ -z "$PRID" ]; then 
        echo "No process of $1 activated"
    else
        sdb $SERNO shell "kill -9 $PRID"
        echo "$1 process has been killed"
    fi
}

install_stub_sdb()
{
    echo "Install testkit-stub. Please wait..."
    TESTSTUBSRC=$PWD/testkit-stub/$DEV_ARCH
    sdb $SERNO push $TESTSTUBSRC/testkit-stub /opt/home/developer/testkit-stub > /dev/null 2>&1
    sdb $SERNO shell "chmod +x /opt/home/developer/testkit-stub" > /dev/null 2>&1
}


launch_stub_sdb()
{
    sdb $SERNO shell "/opt/home/developer/testkit-stub; sleep 2s" > /dev/null 2>&1
    STUBSTATUS=`sdb $SERNO shell "ps aux | grep testkit-stub | grep -v grep"`
    if [ -z "$STUBSTATUS" ]; then 
        echo "Active process testkit-stub failed."
        exit 255
    else
        echo "Active process testkit-stub successfully."
    fi
}


remove_stub_sdb()
{
    echo "Clean testkit-stub. Please wait..."
    sdb $SERNO shell "rm -f /opt/home/developer/testkit-stub" > /dev/null 2>&1
}


install_tinyweb_sdb()
{
    echo "Install tinyweb. Please wait..."
    TINYWEBSRC=$PWD/tinyweb/$DEV_ARCH
    sdb $SERNO push $TINYWEBSRC/tinyweb /opt/home/developer/ > /dev/null 2>&1
    sdb $SERNO shell "chmod a+x /opt/home/developer/tinyweb" > /dev/null 2>&1
    sdb $SERNO push $TINYWEBSRC/cgi-getcookie /opt/home/developer/ > /dev/null 2>&1
    sdb $SERNO shell "chmod a+x /opt/home/developer/cgi-getcookie" > /dev/null 2>&1
    sdb $SERNO push $TINYWEBSRC/cgi-getfield /opt/home/developer/ > /dev/null 2>&1
    sdb $SERNO shell "chmod a+x /opt/home/developer/cgi-getfield" > /dev/null 2>&1
    sdb $SERNO push $TINYWEBSRC/libmongoose.so /opt/home/developer/ > /dev/null 2>&1
    sdb $SERNO shell "chmod 666 /opt/home/developer/libmongoose.so" > /dev/null 2>&1
    sdb $SERNO push $TINYWEBSRC/echo.so /opt/home/developer/  > /dev/null 2>&1
    sdb $SERNO shell "chmod 666 /opt/home/developer/echo.so" > /dev/null 2>&1
    sdb $SERNO push $TINYWEBSRC/server.pem /opt/home/developer/  > /dev/null 2>&1
    sdb $SERNO shell "chmod 666 /opt/home/developer/server.pem" > /dev/null 2>&1
    if [ "$DEV_ARCH"x = "x64"x ]; then
        sdb $SERNO shell "ln -s /usr/lib64/libssl.so.1.0.0 /opt/home/developer/libssl.so" > /dev/null 2>&1
        sdb $SERNO shell "ln -s /usr/lib64/libcrypto.so.1.0.0 /opt/home/developer/libcrypto.so" > /dev/null 2>&1
    else
        sdb $SERNO shell "ln -s /usr/lib/libssl.so.1.0.0 /opt/home/developer/libssl.so" > /dev/null 2>&1
        sdb $SERNO shell "ln -s /usr/lib/libcrypto.so.1.0.0 /opt/home/developer/libcrypto.so" > /dev/null 2>&1
    fi
}

launch_tinyweb_sdb()
{
    DPATH=`sdb $SERNO shell "printenv PATH"`
    timeout 5 sdb $SERNO shell "env LD_LIBRARY_PATH=/opt/home/developer PATH=$DPATH:/opt/home/developer tinyweb -ssl_certificate /opt/home/developer/server.pem -document_root /home/$NAME/content/tct/ -listening_ports 80,8080,8081,8082,8083,8443s; sleep 3s" > /dev/null 2>&1
    TINYWEBSTATUS=`sdb $SERNO shell "ps aux | grep tinyweb | grep -v grep"`
    if [ -z "$TINYWEBSTATUS" ]; then 
        echo "Active process tinyweb failed."
        exit 255
    else
        echo "Active process tinyweb successfully."
    fi
}

remove_tinyweb_sdb()
{
    echo "Clean tinyweb. Please wait..."
    sdb $SERNO shell "rm -f /opt/home/developer/server.pem" > /dev/null 2>&1
    sdb $SERNO shell "rm -f /opt/home/developer/tinyweb" > /dev/null 2>&1
    sdb $SERNO shell "rm -f /opt/home/developer/cgi-getcookie" > /dev/null 2>&1
    sdb $SERNO shell "rm -f /opt/home/developer/cgi-getfield" > /dev/null 2>&1
    sdb $SERNO shell "rm -f /opt/home/developer/libmongoose.so" > /dev/null 2>&1
    sdb $SERNO shell "rm -f /opt/home/developer/echo.so" > /dev/null 2>&1
}

### android platform ###
adb_init()
{
    #TODO
    echo "adb device init..."
}

kill_process_adb()
{
    echo "Kill process $1. Please wait..."
    PRID=`adb $SERNO shell ps | grep $1 | awk '{print $2}'`
    if [ -z "$PRID" ]; then
        echo "No process of $1 activated"
    else
        sdb $SERNO shell "kill -9 $PRID" > /dev/null 2>&1
        echo "$1 process has been killed"
    fi
}

install_stub_adb()
{
    echo "Install testkit-stub. Please wait..."
    TESTSTUBSRC=$PWD/testkit-stub
    adb $SERNO install -r $TESTSTUBSRC/testkit-stub_all.apk
}


launch_stub_adb()
{
    adb $SERNO shell "am start -n testkit.stub/.TestkitStub" > /dev/null 2>&1
    STUBSTATUS=`adb $SERNO shell ps | grep testkit-stub`
    if [ -z "$STUBSTATUS" ]; then 
        echo "Active process testkit-stub failed."
        exit 255
    else
        echo "Active process testkit-stub successfully."
    fi
}


remove_stub_adb()
{
    echo "Clean testkit-stub. Please wait..."
    adb $SERNO shell "pm uninstall testkit.stub" > /dev/null 2>&1
}


install_tinyweb_adb()
{
    echo "Install tinyweb. Please wait..."
    TESTSTUBSRC=$PWD/tinyweb
    adb $SERNO install -r $TESTSTUBSRC/tinyweb_all.apk
}

launch_tinyweb_adb()
{
    adb $SERNO shell "am start -n com.intel.tinywebtestservice/.FullscreenActivity" > /dev/null 2>&1
    STUBSTATUS=`adb $SERNO shell ps | grep tinyweb`
    if [ -z "$STUBSTATUS" ]; then 
        echo "Active process tinyweb failed."
        exit 255
    else
        echo "Active process tinyweb successfully."
    fi
}

remove_tinyweb_adb()
{
    echo "Clean tinyweb. Please wait..."
    adb $SERNO shell "pm uninstall com.intel.tinywebtestservice" > /dev/null 2>&1
}

### localhost ###
localhost_init()
{
    CUR_U=`whoami`
    if [ "$CUR_U"x != "root"x ];then
       echo "Please enter root mode first!" && exit 255
    fi
    echo "init document_root. Please wait..."
    mkdir -p /home/$NAME/content/tct/ > /dev/null 2>&1
    chmod 777 /home/$NAME/content/tct/ > /dev/null 2>&1
    echo "get cpu abi type. Please wait..."
    STRM=`uname -m`
    STRM=`echo $STRM | sed 's/\\r//g' | awk '{print $NF}'`
    echo "get cpu_arch: $STRM"
    case "$STRM" in
      i686*) DEV_ARCH="ia32" ;;
      arm*) DEV_ARCH="arm" ;;
      x86_64*) DEV_ARCH="x64" ;;
      *) echo "unsupported cpu_arch of current device" && exit 255 ;;
    esac
}

kill_process()
{
    echo "Kill process $1. Please wait..."
    PRID=`ps aux | grep $1 | grep -v grep | awk '{print $2}'`
    if [ -z "$PRID" ]; then
        echo "No process of $1 activated"
    else
        kill -9 $PRID
        echo "$1 process has been killed"
    fi
}

install_stub()
{
    echo "Install testkit-stub. Please wait..."
    TESTSTUBSRC=$PWD/testkit-stub/$DEV_ARCH
    cp $TESTSTUBSRC/testkit-stub /usr/bin/testkit-stub > /dev/null 2>&1
    chmod +x /usr/bin/testkit-stub > /dev/null 2>&1
}

launch_stub()
{
    testkit-stub > /dev/null 2>&1
    STUBSTATUS=`ps aux | grep testkit-stub | grep -v grep`
    if [ -z "$STUBSTATUS" ]; then 
        echo "Active process testkit-stub failed."
        exit 255
    else
        echo "Active process testkit-stub successfully."
    fi
}

remove_stub()
{
    echo "Clean testkit-stub. Please wait..."
    rm -f /usr/bin/testkit-stub > /dev/null 2>&1
}

install_tinyweb()
{
    echo "Install tinyweb. Please wait..."
    TINYWEBSRC=$PWD/tinyweb/$DEV_ARCH
    cp $TINYWEBSRC/* /usr/bin/ > /dev/null 2>&1
    cp $TINYWEBSRC/*.so /usr/bin/ > /dev/null 2>&1
    chmod a+x /usr/bin/tinyweb > /dev/null 2>&1
    chmod a+x /usr/bin/cgi-getcookie > /dev/null 2>&1
    chmod a+x /usr/bin/cgi-getfield > /dev/null 2>&1
    chmod 666 /usr/bin/libmongoose.so > /dev/null 2>&1
    chmod 666 /usr/bin/echo.so > /dev/null 2>&1
    chmod 666 /usr/bin/server.pem > /dev/null 2>&1
    if [ "$DEV_ARCH"x = "x64"x ]; then
        ln -s /usr/lib64/libssl.so.1.0.0 /usr/bin/libssl.so > /dev/null 2>&1
        ln -s /usr/lib64/libcrypto.so.1.0.0 /usr/bin/libcrypto.so > /dev/null 2>&1
    else
        ln -s /usr/lib/libssl.so.1.0.0 /usr/bin/libssl.so > /dev/null 2>&1
        ln -s /usr/lib/libcrypto.so.1.0.0 /usr/bin/libcrypto.so > /dev/null 2>&1
    fi
}

launch_tinyweb()
{
    env LD_LIBRARY_PATH=/usr/bin tinyweb -ssl_certificate /usr/bin/server.pem -document_root /home/$NAME/content/tct/ -listening_ports 80,8080,8081,8082,8083,8443s > /dev/null 2>&1
    TINYWEBSTATUS=`ps aux | grep tinyweb | grep -v grep`
    if [ -z "$TINYWEBSTATUS" ]; then
        echo "Active process tinyweb failed."
        exit 255
    else
        echo "Active process tinyweb successfully."
    fi
}

remove_tinyweb()
{
    echo "Clean tinyweb. Please wait..."
    rm -f /usr/bin/server.pem > /dev/null 2>&1
    rm -f /usr/bin/tinyweb > /dev/null 2>&1
    rm -f /usr/bin/cgi-getcookie > /dev/null 2>&1
    rm -f /usr/bin/cgi-getfield > /dev/null 2>&1
    rm -f /usr/bin/libmongoose.so > /dev/null 2>&1
    rm -f /usr/bin/echo.so > /dev/null 2>&1
}

if [ $# -ge 1 ] ; then
    for arg in "$@"
    do
        if [ "$arg"x = "-h"x -o "$arg"x = "--help"x ]; then
            show_usage
        fi
        devstring=`echo $arg | grep deviceid`
        pltstring=`echo $arg | grep platform`
        if [ -n "$devstring" ]; then
            export $arg
            SERNO="-s $deviceid"
        fi
        if [ -n "$pltstring" ]; then
            export $arg
            PLATFORM=$platform
        fi
        if [ "$arg"x = "-p"x -o "$arg"x = "--purge"x ]; then
            EXE_MODE="--purge"
        elif [ "$arg"x = "-i"x -o "$arg"x = "--install"x ]; then
            EXE_MODE="--install"
        fi
    done
fi

case "$PLATFORM" in
    tizen) sdb_init ;;
    android) adb_init ;;
    localhost) localhost_init ;;
    *) echo "unsupported device type '$PLATFORM'." && exit 255 ;;
esac

if [ "$EXE_MODE"x = "--purge"x ]; then
    echo "----------------------------------------------"
    echo "[ Uninstall test resource on device. Please wait...]"
    case "$PLATFORM" in
      tizen) kill_process_sdb "tinyweb" && remove_tinyweb_sdb
              kill_process_sdb "testkit-stub" && remove_stub_sdb;;
      android) kill_process_adb "tinyweb" && remove_tinyweb_adb
                kill_process_adb "testkit-stub" && remove_stub_adb;;
      localhost) kill_process "tinyweb" && remove_tinyweb
                kill_process "testkit-stub" && remove_stub;;
      *) echo "unsupported device type '$PLATFORM'." && exit 255 ;;
    esac

    echo "Clean the packages in device successfully."
    echo "----------------------------------------------"
    exit 0
elif [ "$EXE_MODE"x = ""x -o "$EXE_MODE"x = "--install"x ]; then
    echo "------------------------------------------------------------------------"
    echo "[ Clean old test resource on device. Please wait...]"
    case "$PLATFORM" in
        tizen) kill_process_sdb "tinyweb" && remove_tinyweb_sdb
                kill_process_sdb "testkit-stub" && remove_stub_sdb;;
        android) kill_process_adb "tinyweb" && remove_tinyweb_adb
                  kill_process_adb "testkit-stub" && remove_stub_adb;;
        localhost)  kill_process "tinyweb" && remove_tinyweb
                kill_process "testkit-stub" && remove_stub ;;
        *) echo "unsupported device type $PLATFORM." && exit 255 ;;
    esac

    echo "Clean the packages in device successfully."
    echo "------------------------------------------------------------------------"
    echo "[ Install test resource on device. Please wait...]"
    case "$PLATFORM" in
      tizen) install_stub_sdb && launch_stub_sdb
              install_tinyweb_sdb && launch_tinyweb_sdb ;;
      android) install_stub_adb && launch_stub_adb
                install_tinyweb_adb && launch_tinyweb_adb ;;
      localhost) install_stub
                 launch_stub
                 install_tinyweb
                 launch_tinyweb;;
      *) echo "unsupported device type '$PLATFORM'." && exit 255 ;;
    esac

    echo "All of installation process on device completed."
    exit 0
fi

