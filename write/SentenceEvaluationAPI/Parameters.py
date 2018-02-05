class Parameters:
    '''
    parameters 폴더에서 원하는 파라미터들을 불러오는 클래스입니다.
    인스턴스화 하고 someInstance.connectInfoList에서 불러다 쓰면 됩니다.
    세팅값을 변경시키고 싶으 면 Parameters.py에서 변경하세요.
    '''
    def __init__(self, name):
        module = self.importFrom('parameters', name)
        paramList = [(x,y) for x,y in module.__dict__.items() if 'Param' in x]
        self.paramInfoList = \
        list(map(self.updateParams, [module]*len(paramList), paramList))
        self.paramNameList = [x for x,y in paramList]
        self.getDefaultParams = \
        [y for x,y in module.__dict__.items() if 'defaults' in x][0]
        
    def updateParams(self, module, paramList):
        defaults = module.defaults.copy()
        defaults.update(paramList[1])
        return defaults

    def importFrom(self, module, name):
        module = __import__(module, fromlist=[name])
        return getattr(module, name)

if __name__ == '__main__':
    a = Parameters('Hangeul')
    print(a.getDefaultParams)