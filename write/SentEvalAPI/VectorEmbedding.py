import random
import SentEvalAPI.FakeHangeulGenerator
from SentEvalAPI.Parameters import Parameters
from SentEvalAPI.BasicOperator import *
from SentEvalAPI.BiGramFrequency import FreqDistExtractor
from SentEvalAPI.BiGramFrequency import weightedMerge

class FreqDistribution:
    pass # 피클파일 부르는 것 때문에 만든 abstract class입니다. 쓰지마세영


'''
벡터 임베딩이라 적어놨지만 사실은 벡터시드로 만드는 것입니다.
벡터로 만들면 메모리가 많이 들기 때문에 그것은 마지막의 마지막까지 미뤄둡니다.
'''
HanParams = Parameters('Hangeul').getDefaultParams
if HanParams['dimUniVec'] != 67+1+1:
    print('#####Dimesion of univector does not match.######')
    raise

class HangeulUniVector:
    def __init__(self):
        # Memoization. 겹치는 글자가 많을수록 빨라진다.
        self.decomposerMemo = {}
        self.uniVectorMemo = {}
        # 굳이 아래의 이상한 과정을 거치는 이유는 유니코드 상 초성 ㄱㄴㄷㄹ, 종성 ㄱㄴㄷㄹ, 홑낱말 ㄱㄴㄷㄹ가 모두 달라서임.
        # 해당 단어열을 분해해서 순서를 달아 딕셔너리로 만듬. 
        # 마지막의 뜬금없는 '가'는 종성없음을 표현하기 위해서 넣음.
        # 따라서 tdict의 마지막 4519는 종성없음을 의미.
        self.tagDict = {}
        alphSet = '각냔덛렬몸뵵숫융즞칯캨턭펲혷꽊뙜뾗쒅쮆귉긞갋갌갍갎갏값가'
        for idx in range(len(alphSet)):
            i, m, t = self.hangeulDecomposer(alphSet[idx])
            if idx <= 18:
                self.tagDict[i] = idx
            if idx <= 20:
                self.tagDict[m] = idx+19
            if idx <= 27:
                self.tagDict[t] = idx+40
             
    def hangeulDecomposer(self, uni):
        # 한글을 넣으면 초,중,종성으로 쪼개주는 함수. i,m,t = 초,중,종
        # 예를 들어 '값'은 ㄱ ㅏ ㅄ으로 변한다. 다만, 글 대신 유니코드를 사용함.
        if uni in self.decomposerMemo:
            return self.decomposerMemo[uni]
        alphNum = ord(uni)
        i = int((alphNum - 44032)/(28*21)) + 4352
        m = int(((alphNum - 44032)/28) %21) + 4449
        t = int((alphNum - 44032) % 28) + 4520 - 1
        # 여기서 4519는 한글이 아닌데, 종성없음이 나타나는 영역이다.
        self.decomposerMemo[uni] = (i, m, t)
        return i, m, t

    def uniVectorEmbedding(self, uni):
        if uni in self.uniVectorMemo:
            return self.uniVectorMemo[uni]
        retList = []
        if BasicHangeulOperators().hangeulCheck(uni):
            for tag in self.hangeulDecomposer(uni):
                retList.append(self.tagDict[tag])
            self.uniVectorMemo[uni] = retList
            return retList
        else:
        # 만약 한글이 아닌 문자가 들어왔으면 마지막 자리에다 태깅해준다.
            retList = [68, 68, 68]
            self.uniVectorMemo[uni] = retList
            return retList

class HangeulBiVector:
    def __init__(self):
        path = HanParams['hangeulPicklePath']
        self.dimBiVec = HanParams['dimBiVec']
        freqDict = FreqDistExtractor.loadFreqDist(path)
        self.freqDict = weightedMerge(freqDict)
        self.syllableDict = self.freqDict.dictByRate[1]['wordFreqDict']
        # 밑은 모든 음절 중 빈도 상위만을 뽑아내는 과정.
        temp = [(v, k) for k, v in self.syllableDict.items()]
        temp.sort()
        temp.reverse()          
        temp = [k for v, k in temp]
        # 빈도 상위 dimBiVec개 음절만 뽑아서 순위를 저장한 sylUnderDim
        self.sylUnderDim = {j:i for i,j in enumerate(temp[:self.dimBiVec-1])} # -1은 사용하지 않는 한칸
        self.uniVecEmbedd = HangeulUniVector()

    def biVectorEmbedding(self, biList, label = None):
        retList = []
        for bi in biList:
            biClass = NGramVectorSeed(label, 0, 0, self.dimBiVec-1, self.dimBiVec-1, 1, 1)
            if bi[0] in self.syllableDict:
                biClass.uni1Label = 1
            if bi[1] in self.syllableDict:
                biClass.uni2Label = 1
            if bi[0] in self.sylUnderDim:
                biClass.bi1Index = self.sylUnderDim[bi[0]]
            if bi[1] in self.sylUnderDim:
                biClass.bi2Index = self.sylUnderDim[bi[1]]
            biClass.uni1Index = self.uniVecEmbedd.uniVectorEmbedding(bi[0])
            biClass.uni2Index = self.uniVecEmbedd.uniVectorEmbedding(bi[1])
            retList.append(biClass)
        return retList

class BiGramResrvoir:
    '''
    말 그대로 바이그램 저수지입니다. 한 에폭의 학습에 사용된 데이터를 모두 풀링합니다.
    만약 데이터의 확률 분포에 변형을 가하는 등의 오퍼레이션이 필요하면 여기서 하시는게 좋습니다.
    이 이후에는 truncate과 dimBiVec의 제한으로 정보를 잃습니다.
    '''
    def __init__(self):
        self.abnormVecGenerator = FakeHangeulGenerator.AbnormalPipeline()
        self.freqDict = self.abnormVecGenerator.freqDict

    def getDatas(self, numNeeded):
        abnormalRate = HanParams['abnormalRate']
        randVec, glitchedBi = self.abnormVecGenerator.performAbnormals(int(abnormalRate*numNeeded))
        wrongAnswers = list(self.freqDict.dictByRate[0]['biFreqDict'].keys()) * HanParams['foreignWrongAns']
        ordinalBi = self.freqDict.dictByRate[1]['biFreqDict']
        trainBi = BasicOperators.randomTruncatedSampling(ordinalBi, upperBound, numSamples)
        abnormalBi = glitchedBi + wrongAnswers
        return randVec, abnormalBi, ordinalBi

class VectorFactory:
    '''    
    벡터를 달라고 하면 정해진 개수만큼 찍어냅니다.
    randomTruncatedSampling은 확률 분포를 그대로 따라서 샘플링을 하면
    하위 단어를 거의 고려 못하기 때문에 일정 빈도 이상은 모두 같은 확률로 샘플링하는 방법입니다.
    ''' 
    def __init__(self):
        self.biGramResrvoir = BiGramResrvoir()
        self.hanBiVecEmbed = HangeulBiVector()

    def trainVector(self):
        # 창의력이 떨어져서 더 이름을 못 짓겠는데 섞어서 벡터화만 하면 되는 학습셋을 돌려주는 역할입니다.
        upperBound = HanParams['truncSamplingParam']['upperBound']
        numSamples = HanParams['truncSamplingParam']['numSamples']
        randVec, abnormalBi, ordinalBi = self.biGramResrvoir.getDatas(numSamples)
        retList = []
        retList.extend(self.hanBiVecEmbed.biVectorEmbedding(trainBi, 1))
        retList.extend(self.hanBiVecEmbed.biVectorEmbedding(abnormalBi, 0))
        retList.extend(randVec)
        return retList

if __name__ == '__main__':
    aa = VectorFactory()
    aa.trainVector()
