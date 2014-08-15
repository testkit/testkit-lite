def initCapability(test_name=None, test_ext=None, webdriver_url='http://127.0.0.1:9515', test_prefix='file:///android_asset/www/'):
    capability = {'xwalkOptions': {'androidPackage':test_name, 'androidActivity': test_ext}}
    return {'webdriver_url': webdriver_url, 'desired_capabilities': capability, 'test_prefix': test_prefix }
