def initCapability(test_app=None, debug_ip=None):
    capability = {'xwalkOptions': {'tizenDebuggerAddress': debug_ip, 'tizenAppId': test_app}}
    return {'webdriver_url': 'http://127.0.0.1:9515', 'desired_capabilities': capability, 'test_prefix': ''}
