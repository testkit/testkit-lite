def initCapability(test_app=None, test_ext=None):
    capability = {'chrome.binary': '/usr/bin/chromium-browser'}
    return {'webdriver_url': 'http://127.0.0.1:9515', 'desired_capabilities': capability, 'test_prefix': 'file:///'}
