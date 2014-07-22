def initCapability(test_app_name=None, appid=None):
    capability = {'xwalkOptions': {'tizenDebuggerAddress': test_app_name, 'tizenAppId': appid}}
    return {'desired_capabilities': capability, 'test_prefix': ''}
