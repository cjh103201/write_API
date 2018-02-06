import os
import random
from collections import defaultdict
import pickle
import SentEvalAPI.BasicOperator
from SentEvalAPI.Parameters import Parameters

class FreqDistExtractor:
    def __init__(self):
        # 자주 사용하는 작업이 저장되어있습니다. 저는 인스턴스화 시켜서 쓰는 것을 좋아합니다.
        self.hangeulOperator = BasicOperator.BasicHangeulOperators()
        self.basicOperator = BasicOperator.BasicOperators()

    def performFreqDist(self, dataPipe, name = 'LoveInMotion'):
        # 데이터가 들어오는 라인(DataPipe 클래스)를 연결시켜주면 데이터를 가져옵니다.
        # 이 파일은 표층모델을 학습시키는 데이터를 만듭니다. 분석할 어절/ 문장이 biGram의 sequence라 생각할 수 있지만,
        # 여기서는 그런 부분은 생각하지 않았습니다. 이 표층모델에서는 문장 내 각 바이그램/ 유니그램을 개별적으로 봅니다.
        # 따라서 데이터는 바이그램/ 유니그램의 빈도수로 요약될 수 있습니다.
        # 이 경우 계산속도가 빨라지고, 메모리 사용이 줄어들고, 다양한 변형이 가능합니다.
        freqDict = {}
        # 빈도수의 묶음을 저장할 딕셔너리를 만듭니다. 이 딕셔너리가 리턴값입니다.
        while True:  
            try:
                pump, line = dataPipe.pumpData()
                # 데이터를 가져오는 라인을 표시하고 제너레이터를 가져옵니다.
                distrb  = FreqDistribution(line)
                # 분류에 따라 빈도수를 저장하는 클래스를 만듭니다. 밑의 클래스를 참조하세요.
                freqDict[line] = distrb
                for data in pump:
                    cont = data[0]
                    # 문장입니다.
                    surfRate = data[1]
                    # 라벨값입니다. 만약 심층모델을 만들 경우 거기서는 data[2]를 받을 것입니다.
                    cont = self.hangeulOperator.processedSent(cont)
                    # 특수문자를 처리하고 영어, 숫자에 태그를 답니다.
                    uniGramList = self.hangeulOperator.nGramSlicer(cont, 1)
                    biGramList = self.hangeulOperator.nGramSlicer(cont, 2)
                    # 문장을 잘라서 리스트로 만듭니다
                    for uni in uniGramList:
                        if surfRate == 1:
                            distrb.dictByRate[surfRate]['wordFreqDict'][uni] += 1
                            # 적절하지 않은 유니그램은 필요없으니 걸러냅니다. 
                    for bi in biGramList:
                        distrb.dictByRate[surfRate]['biFreqDict'][bi] += 1
                    # 리스트를 보면서 해당 유니/바이그램의 카운트를 하나씩 올려줍니다.
                    # FreqDistribution 클래스의 주석을 참조하세요.
            except StopIteration:
                break
            # DataPipe의 lineChange함수가 끝이라고 하면 멈춥니다.
        freqDict = self.confirmDict(freqDict)
        path = self.basicOperator.filePath('freqDict')
        os.makedirs(path)
        f = open(path+name+'.bin', 'wb')
        pickle.dump(freqDict, f)
        f.close()
        print(path+name+'.bin')
        return freqDict
        # 빈도 분포를 피클파일로 저장하고 리턴합니다.

    @staticmethod
    def loadFreqDist(path):
        # 빈도 분포를 불러오는 파일입니다.
        f = open(path, 'rb')
        freqDict = pickle.load(f)
        f.close()
        return freqDict

    def confirmDict(self, freqDict):
        # FreqDistribution의 defaultdict에서 기본값 0을 줄때 lambda를 써서 그대로 피클에 안들어갑니다.
        # 따라서 defaultdict을 기본 dictionary로 바꾸는 작업을 여기서 합니다.
        # 또한 라벨로 터프하게 걸렀기 때문에 rate0에도 정상적인 바이그램이 많이 섞여있습니다.
        # 이들을 제거하는 작업을 병행합니다.
        # 딕셔너리를 세번이나 겹쳐 선언하는 안좋은 자료형이지만 클래스 만들기가 싫어서 이렇게 합니다.
        temp = {}
        for name, dist in freqDict.items():
            for rate, dic in dist.dictByRate.items():
                for name, defdic in dic.items():
                    dist.dictByRate[rate][name] = dict(defdic)
            for k, v in dist.dictByRate[0]['biFreqDict'].items():
                if k in dist.dictByRate[1]['biFreqDict'].keys():
                    temp[k] = True
        for name, dist in freqDict.items():
            for k in temp:
                dist.dictByRate[0]['biFreqDict'].pop(k, None)
        return freqDict

class FreqDistribution:
    def __init__(self, dataFrom):
        self.__name = dataFrom
        # 어떤 파라미터로 가져온 데이터인지 알려줍니다.
        self.dictByRate =\
        {
         1:{
          'wordFreqDict' : defaultdict(lambda :0),
          'biFreqDict' : defaultdict(lambda :0)
           },
         0:{
          'biFreqDict' : defaultdict(lambda :0)
           }
        }
        # 이 부분은 클래스로 다시 표현하셔야할 것 같습니다. 혹은 JSON을 사용해야할 듯 합니다.
        # 먼저 라벨이 1인지 0인지에 따라 분류하고 내부에서 다시 바이그램인지 유니그램인지 분류하고
        # 그 다음 딕셔너리에 해당 nGram의 빈도를 넣습니다.
        # 딕셔너리라서 속도는 느리지 않지만, 만약 분기가 더 늘어나거나 저장해야할 데이터의 수가 늘어나면
        # 감당하기 힘들어질 듯 합니다.

    def __str__(self):
        return self.__name

def weightedMerge(freqDict):
    param = Parameters('Hangeul')
    mergedFreqDict = FreqDistribution('mergedFreqDict')
    zippedList = zip(param.paramNameList, param.paramInfoList)
    for line, info in zippedList:
        lineWeight = info['mergingWeight']
        for rate, dicts in freqDict[line].dictByRate.items():
            for dicName, dic in dicts.items():
                for k, v in dic.items():
                    mergedFreqDict.dictByRate[rate][dicName][k] += int(lineWeight*v)
    return mergedFreqDict

if __name__ == '__main__':
    import DataPipeline
    b = DataPipeline.DataPipe('TrainDB')
    a = FreqDistExtractor()
    p = a.performFreqDist(b, 'LoveInMotion')
    # p = a.loadFreqDist('./data/freqDict/180125_183423/LoveInMotion.bin')
    print(weightedMerge(p).dictByRate)
    # pppp = {**p['iirParam'].dictByRate[0]['biFreqDict'],**p['daumParam'].dictByRate[0]['biFreqDict']}
    # for k in pppp:
    #     print(k)
    # 위에서 클래스가 아니라 딕셔너리의 중첩을 사용한 결과로 코드가 꼬였습니다.
    # p['iirParam'].dictByRate[0]['biFreqDict'].items() 이렇게 불러다 써야합니다.