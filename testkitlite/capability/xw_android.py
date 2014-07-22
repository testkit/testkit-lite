def initCapability(test_app_name=None, appid=None):
    capability = {'xwalkOptions': {'androidPackage': 'org.xwalk.%s' %
                                   test_app_name, 'androidActivity': '.%sActivity' % test_app_name}}
    return {'desired_capabilities': capability, 'test_prefix': 'file:///android_asset/www/'}
