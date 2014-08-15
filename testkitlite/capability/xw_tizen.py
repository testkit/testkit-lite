def initCapability(test_app=None, test_ext=None, webdriver_url='http://127.0.0.1:9515', test_prefix=''):
    capability = {'xwalkOptions': {'tizenDebuggerAddress': test_ext, 'tizenAppId': test_app}}
    return {'webdriver_url':webdriver_url , 'desired_capabilities': capability, 'test_prefix': test_prefix}
