def initCapability(device_id, test_suite_name):
    capability = {'xwalkOptions': {'binary': "", "iotPackage": test_suite_name}}
    return {'webdriver_url':"http://%s:9515" % device_id, 'desired_capabilities': capability}
