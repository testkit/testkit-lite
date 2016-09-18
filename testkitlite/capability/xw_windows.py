def initCapability(test_name, device_id):
    capability = {'xwalkOptions': { 'binary': 'C:\\Program Files\\%s' % test_name}}
    return {'webdriver_url': "http://%s:9515" % device_id, 'desired_capabilities': capability, 'test_prefix': "file:///C:\\Program Files\\%s\\%s" % (test_name, test_name)}
