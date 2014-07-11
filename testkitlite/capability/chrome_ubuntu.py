def initCapability(test_app_name=None):
    capability = {'chrome.binary': '/usr/bin/chromium-browser'}
    return {'desired_capabilities': capability, 'test_prefix': 'file:///'}
