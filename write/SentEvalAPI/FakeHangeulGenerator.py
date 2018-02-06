# LoveInMotion
import random
from SentEvalAPI.BasicOperator import BasicHangeulOperators
from SentEvalAPI.BasicOperator import NGramVectorSeed
from SentEvalAPI.BiGramFrequency import FreqDistExtractor
from SentEvalAPI.BiGramFrequency import weightedMerge
from SentEvalAPI.Parameters import Parameters

class FreqDistribution:
    pass # 피클파일 부르는 것 때문에 만든 abstract class입니다. 쓰지마세영

class UniMutator:
    def __init__(self, validNGram):
        self.validNGram = validNGram

    def mutatation(self, uni):
    # 지금은 너무 황당한 단어들이 나오기 때문에 바이그램 학습에서 미묘한 틀림을 인식하지 못한다.
    # 미묘하게 틀린 한글을 만들어내려면, 외국인이 틀리는 모습을 모방할 필요가 있다. 
    # 예를 들자면, 외국인은 ㄴ과 ㅇ의 발음을 헷갈려하고 이것이 글쓰기에 반영되는 경우가 있다.
    # 마찬가지로 ㅊ, ㅉ은 ㅈ으로 수렴하는 경향이 있다. 이런 규칙들을 찾아내면 각 음소 자질을 노드로 삼는
    # 마르코프 체인의 계를 만들 수 있고, 그 매트릭스를 구한다면 단어에 미묘한 오류를 추가하기가 매우 쉽고 빨라질것.
    # 이는 비문생성에서도 마찬가지일 것이라 생각함.
    # 간단하게는 마르코프 체인이겠지만 뭐가 되었던 간에 비슷해 보이면서 말도 안되는, 오류가 남발하는 문장을
    # 대량으로 생성할 필요가 잇음.
        pass

    def glitch(self, numNeeded):
        wordSet = {ord(i) for i in self.validNGram.keys() if len(i) == 1}
        wordRange = set(range(44032,55203))
        wordRange = wordRange - wordSet
        abnormalList = []
        cnt = numNeeded
        while True:
            word = random.choice(list(wordRange))
            wordRange -= set([word])
            abnormalList.append(chr(word))
            cnt -= 1
            if cnt == 0:
                return abnormalList
            if len(wordRange) == 0:
                wordRange = set(range(44032,55203)) - wordSet

class BiMutator:
    def __init__(self, HanParams, validNGram):
        self.HanParams = HanParams
        self.validNGram = validNGram
        self.glitchedUni = UniMutator(self.validNGram).glitch(self.HanParams['uniGlitchPoolSize'])

    def mutatation(self, bi):
        pass

    def glitch(self, numNeeded):
        mutationRatio = self.HanParams['biGramMutation'] 
        biGramList = list({i for i in self.validNGram.keys() if len(i) == 2})
        cnt = numNeeded
        retList = []
        # 뭐가 긴데 별거 없는 그냥 반복, 조건문이다.
        # 0까지 카운트 다운하면서 바이그램 내 한글 개수에 따라서 망가진 한글로 치환하는 것.
        ############################################################
        ################ 이 함수 조금 수정해야 할 듯. #####################
        ############################################################
        while True:
            if cnt == 0:
                return retList
            mutatedBi = random.choice(biGramList)
            numHan = 0
            for i in range(len(mutatedBi)):
                if BasicHangeulOperators().hangeulCheck(mutatedBi[i]) == True:
                    numHan += 1
                    point = i
            if numHan == 0:
                continue
            if numHan == 2:
                if random.uniform(0,1) >= mutationRatio:
                    numHan = 1
                    point = random.randint(0,1)
                else:
                    cnt -= 1
                    a = random.choice(self.glitchedUni)
                    b = random.choice(self.glitchedUni)
                    mutatedBi = a+b
            if numHan == 1:
                cnt -= 1
                if point == 0:
                    mutatedBi = random.choice(self.glitchedUni)+mutatedBi[1]
                else:
                    mutatedBi = mutatedBi[0]+random.choice(self.glitchedUni)                
            retList.append(mutatedBi)

class RandomVector:
    def randomVector(self, numNeeded, dimBiVec = None, dimUniVec = None):
        retList = []
        for i in range(numNeeded):
            rndVec = NGramVectorSeed(0, 0, 0, dimBiVec-1, dimBiVec-1, 1, 1)
            rndVec.uni1Index = [random.randrange(dimUniVec) for i in range(3)]
            rndVec.uni2Index = [random.randrange(dimUniVec) for i in range(3)]
            rndVec.bi1Index = random.randrange(dimBiVec)
            rndVec.bi2Index = random.randrange(dimBiVec)
            retList.append(rndVec)
        return retList 

class AbnormalPipeline:
    def __init__(self):
        self.HanParams = Parameters('Hangeul').getDefaultParams
        path = self.HanParams['hangeulPicklePath']
        freqDict = FreqDistExtractor.loadFreqDist(path)
        self.freqDict = weightedMerge(freqDict)
        self.validNGram = {}
        for k, v in self.freqDict.dictByRate[1].items():
            self.validNGram.update(v)

    def performAbnormals(self, numNeeded):
        ratio = self.HanParams['abnormalMethodRatio']
        numNeededDic = {k:int(v*numNeeded) for k,v in ratio.items()}
        dimUni, dimBi = self.HanParams['dimUniVec'], self.HanParams['dimBiVec']
        rnV = RandomVector().randomVector(numNeededDic['randomVec'], dimBi, dimUni)
        glB = BiMutator(self.HanParams, self.validNGram).glitch(numNeededDic['glitchedBi'])
        # 여기서 주의할 것은 randomVector는 벡터형식으로, 나머지는 스트링으로 값을 돌려준다는것!!!!!
        # 그래서 이거 잘 분리해서 써야합니다. 저는 이 함수 쓸때마다 맨 처음이 랜덤벡터인 것으로 하겠습니다.
        # 랜덤벡터는 벡터임베딩에 넣어도 애매하고 여기 넣어도 애매한 계륵인데 여기가 낫다 생각햇습니ㅏ.
        return rnV, glB

if __name__ == '__main__':
    a, _ = AbnormalPipeline().performAbnormals(50000)
    print(a[0])
    print(a[0].bi1Index)

