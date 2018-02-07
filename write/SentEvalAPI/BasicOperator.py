import random

class BasicHangeulOperators:
    def __init__(self):
        # 정규식을 사용해서 영어와 숫자를 하나의 태그로 만든다.
        # 한국어 문장에서 영어단어가 쓰이는 경우는 고유 명사, 이름, 예시가 대부분이므로 이렇게 해도 문법상 오류는 없을 것.
        # 트랜잭션 순서대로 관리해주세영
        import re
        self.numRe = re.compile('[0-9]+')
        self.engRe = re.compile('[A-z]+')
        self.funcTransac = [self.engRe, self.numRe]
        self.varTransac = [chr(60982), chr(60983)]

    def nonHangeulTagger(self, sentence):
        # 한글과 구두점 쉼표 외는 unknow으로 하거나 유니코드 사용자 정의 영역에 할당함. num->uEE00, eng->uEE01       
        for regObj, var in zip(self.funcTransac, self.varTransac):
            sentence = regObj.sub(var, sentence)
        return sentence

    def nGramSlicer(self, sentence, n = 1):
        # 문장 받으면 쪼개서 출력하는거. 
        # n보다 작은 단어는 모두 공백으로 출력되어 학습에서 에러나 이상현상을 일으킬 수 있음
        # 데이터 베이스에서 한글자 짜리 데이터를 열심히 지워줄 것.
        return [sentence[i:i+n] for i in range(len(sentence)-n+1)]

    def hangeulCheck(self, alph):
        # 입력받은 글자가 완성된 한글인지 판별.
        if ord(alph) >= 44032 and ord(alph) <= 55203:
            return True
        else:
            return False

    def allowedUniCheck(self, alph):
        alph = ord(alph)
        # allowed = [A-z0-9ㄱ-ㅎㅏ-ㅢ가-힣',','.',' ']
        # if문 내에서는 자주 나오는 순서대로 배치함
        if alph >= 44032 and alph <= 55203: #[가-힣]
            return True
        elif alph == 32: # [ ] 공백
            return True
        elif alph >= 65 and alph <= 122: # [A-z]
            return True
        elif alph >= 48 and alph <= 57: # [0-9]
            return True
        elif alph >= 12593 and alph <= 12643: # [ㄱ-ㅢ]
            return True
        elif alph == 46 or alph == 44: #[.,] 
            return True
        else:
            return False

    def filterNotAllowedAlph(self, sentence):
        # 문장 중에서 허가되지 않은 문자를 걸러냄
        new = ''
        for alph in sentence:
            if self.allowedUniCheck(alph) == True:
                new += alph
        return new

    def processedSent(self, sentence):
        sentence = self.filterNotAllowedAlph(sentence)
        sentence = self.nonHangeulTagger(sentence)
        return sentence

class BasicOperators: # something frequently used.
    def reservoirSampling(items, k):
        # O(n)으로 n개 중 k개를 sampling하는 법. 제너레이터랑 합치면 메모리도 아낄 수 있음.
        if len(items) <= k:
            print('not enough items')
            raise
        sample = items[0:k]
        for i in range(k, len(items)):
            j = random.randrange(1, i + 1)
            if j <= k:
                sample[j-1] = items[i]
        return sample

    def randomTruncatedSampling(freqDict, numTruncate, k): 
        def freqDictIterator(freqDict):
            for i in freqDict:
                for _ in range(freqDict[i]):
                    yield i   
        truncFreq = {i:min(freqDict[i], numTruncate) for i in freqDict}
        truncTotal = sum(list(truncFreq.values()))
        if truncTotal <= k:
            return [x for x in freqDictIterator(truncFreq)]
        truncGen = freqDictIterator(truncFreq)
        sample = [next(truncGen) for x in range(k)]
        for i in range(k, truncTotal):
            j = random.randrange(1, i + 1)
            if j <= k:
                sample[j-1] = next(truncGen)
        return sample

    def filePath(self, name):
        from datetime import datetime as dt
        savepath = './data/'+name+'/'+dt.strftime(dt.now(),"%y%m%d_%H%M%S/")
        return savepath

class NGramVectorSeed:
    def __init__(self, biLabel, uni1Label, uni2Label, bi1Index, bi2Index, uni1Index, uni2Index):
        # 이거 kwargs같은 방법으로 풀 수 있을까요? ㅠㅠ
        '''
        biLabel: 바이그램 자체의 정오를 저장
        uni1Label = 첫번째 음절의 정오를 저장.
        uni2Label = 두번째 음절의 정오를 저장.
        bi1Index = 첫번째 음절의 dimVec내 순위를 저장.
        bi2Index = 두번째 음절의 dimVec내 순위를 저장.
        uni1Index = 첫번째 음절의 초, 중, 종성을 저장.
        uni2Index = 두번째 음절의 초, 중, 종성을 저장.
        '''
        self.biLabel = biLabel
        self.uni1Label = uni1Label
        self.uni2Label = uni2Label
        self.bi1Index = bi1Index
        self.bi2Index = bi2Index
        self.uni1Index = uni1Index
        self.uni2Index = uni2Index 
        
if __name__ == '__main__':
    a = BasicHangeulOperators()
    print(a.nGramSlicer(a.processedSent('wsdfa34534534534김ㅇ박1231235fafd'), 1))
    a = BasicOperator()
    print(a.filePath('kimchitry'))  


