import tensorflow as tf
import ModelTrainer as mt
import DataPipeline
from VectorEmbedding import HangeulBiVector
from BasicOperator import BasicHangeulOperators

class FreqDistribution:
    pass # 피클파일 부르는 것 때문에 만든 abstract class입니다. 쓰지마세영

hanOp = BasicHangeulOperators()
hanBi = HangeulBiVector()

def classifySentence(dataPipe):
    while True:
        try:
            pump, _ = dataPipe.pumpData()
        except StopIteration:
            break
        rate0 = []
        rate1 = []
        for sent, rate in pump:
            sent = hanOp.processedSent(sent)
            if len(sent) < 2:
                print('{} is too short to evaluate.'.format(sent))
                continue
            if rate == 1:
                rate1.append(sent)
            else:
                rate0.append(sent)
    return rate0, rate1

def makeSeed(sentence, label):
    biSet = hanOp.nGramSlicer(sentence, 2)
    biSet = hanBi.biVectorEmbedding(biSet, label)
    return biSet

def getScore(uni1, uni2, bi):
    minScore = min(uni1, uni2, bi)
    bias = -1.1
    score = 1.8*bi + 1*minScore + bias
    # 여기서 그냥 return score 해야 밑에서 써먹겠나... 어째야하누.
    return score
    # if score >= 0.5:
    #     return 1
    # else:
    #     return 0

def predBi(rate0, rate1, sess, model): 
    vec0 = []
    vec1 = []
    truePos = 0 # 맞는 문장을 맞다고 했다.
    trueNeg = 0 # 틀린 문장을 틀렸다고 했다.
    falsePos = 0 # 틀린 문장을 맞다고 했다.
    falseNeg = 0 # 맞는 문장을 틀렸다고 했다. 가장 줄여야 할것.

    for sent in rate0:
        seedSet = makeSeed(sent, 0)
        vec0.append(seedSet)
    for sent in rate1:
        seedSet = makeSeed(sent, 1)
        vec1.append(seedSet)

    # import csv
    # f = open('bringItHome.csv', 'w')
    # csvw = csv.writer(f)
    for seedSet in vec0:
        scoreStack = []
        for seed in seedSet:
            vec = mt.index2Vec(1, [seed])
            a, b, c, d, e, f = next(vec)
            feedData = {model.uni_X1:a, model.uni_Y1:b, model.uni_X2:c, \
            model.uni_Y2:d, model.bi_X:e, model.bi_Y:f, model.prob:1}
            n,m,l = sess.run([model.model_uni1, model.model_uni2, model.model_bi], feed_dict = feedData)
            n,m,l = n[0][0],m[0][0],l[0][0]
            # csvw.writerow([n,m,l,0])
            # 여기서 그냥 nml 기록하면 문제인게 그럼 이게 어떻게 점수화가 된건지는 모르네.
            scr = getScore(n,m,l)
            scoreStack.append(scr)
        scr = min(scoreStack)
        if scr >= 0.6:
            falsePos += 1
        else:
            trueNeg += 1
           
    for seedSet in vec1:
        scoreStack = []
        for seed in seedSet:
            vec = mt.index2Vec(1, [seed])
            a, b, c, d, e, f = next(vec)
            feedData = {model.uni_X1:a, model.uni_Y1:b, model.uni_X2:c, \
            model.uni_Y2:d, model.bi_X:e, model.bi_Y:f, model.prob:1}
            n,m,l = sess.run([model.model_uni1, model.model_uni2, model.model_bi], feed_dict = feedData)
            n,m,l = n[0][0],m[0][0],l[0][0]
            # csvw.writerow([n,m,l,1])
            scr = getScore(n,m,l)
            scoreStack.append(scr)
        scr = min(scoreStack)
        # 여기선 미니멈을 스코어로 사용하는데 적절한 문장길이가 정립되면 그 근처에 가우시안을 둬서
        # 문장 길이에 따라 플러스 알파를 주는 방식을 쓰자. 이렇게 미니멈을 보면 틀리고 맞고만 가리지 그 이상은 못해낸다.
        # 예를 들어 문장이 길수록 미니멈이 낮을 확률은 높아지는데 이에 대한 보상이 없다.
        # 가우시안인 이유(익스포넨셜이 아니라)는 너무 긴 문장 또한 지양해야하기 때문.
        if scr < 0.6:
            falseNeg += 1
        else:
            truePos += 1

    print("#"*80)
    return truePos, trueNeg, falsePos, falseNeg

def evaluateTestDB(path):
    dataPipe = DataPipeline.DataPipe('TestDB')
    saver = tf.train.Saver()
    with tf.Session() as sess:
        # 여기서 모델 부를때 직접 그곳 까지 가서 부르는 펑션이 있어야함. 그리고 피클파일도 마찬가지고.
        # 패쓰를 저장하는 적당한 방법이 있다면 좋을텐데. 수작업이 아니라, 자동으로 버전이 관리되도록.
        model = mt.SurfaceModel()
        saver.restore(sess, path + "/model.ckpt")
        rate0, rate1 = classifySentence(dataPipe)
        tp, tn, fp, fn = predBi(rate0, rate1, sess, model)
        print(tp, tn, fp, fn)
    return tp, tn, fp, fn



# bias = -0.8 # bigramBias
# score = 1.5*bi + minScore + bias
# scr < 0.6 # scoreCut
# val = evaluateTestDB('./mdl')
# print('tp, tn, fp, fn')
# print(val)


def evaluateSentence(sess, model, sent):
    sent = hanOp.processedSent(sent)
    if len(sent) < 2:
        raise ValueError
    # print('biGram    Uni1P     Uni2P    BiP    Scr')
    biSet = hanOp.nGramSlicer(sent, 2)
    biZip = zip(hanBi.biVectorEmbedding(biSet, 1), biSet)
    minScr = 9999
    for seed, bi in biZip:
        vec = mt.index2Vec(1, [seed])
        a, b, c, d, e, f = next(vec)
        feedData = {model.uni_X1:a, model.uni_Y1:b, model.uni_X2:c, \
                    model.uni_Y2:d, model.bi_X:e, model.bi_Y:f, model.prob:1}
        n,m,l = sess.run([model.model_uni1, model.model_uni2, model.model_bi], feed_dict = feedData)
        n,m,l = n[0][0],m[0][0],l[0][0]
        scr = getScore(n, m, l)
        if scr <= minScr:
            minScr = scr
            minBi = bi
        # print(bi, n, m, l, scr)
    return minScr, minBi

def sent_eval_api(sent, path):
    saver = tf.train.Saver()
    with tf.Session() as sess:
        model = mt.SurfaceModel()
        saver.restore(sess, path + "/model.ckpt")
        try:
            sent = hanOp.processedSent(sent)
        except ValueError:
            print('Not enough length.')
            # 만약 한글자 짜리 문장도 평가하고 싶다면 분기문을 설정하고 유니그램 모델평가치를 가져오면 될듯.
            # 다만 그 자체로는 효과가 없을 수도 있고 마찬가지로 새로운 평가방법을 정해야할 것이다.
        else:
            evaluateSentence(sess, model, sent)

# def sent_eval_api(path):
#     saver = tf.train.Saver()
#     with tf.Session() as sess:
#         model = mt.SurfaceModel()
#         saver.restore(sess, path + "/model.ckpt")
#         while True:
#             print('write sent')
#             sent = input()
#             if sent == 'q':
#                 break
#             try:
#                 sent = hanOp.processedSent(sent)
#             except ValueError:
#                 print('Not enough length.')
#                 # 만약 한글자 짜리 문장도 평가하고 싶다면 분기문을 설정하고 유니그램 모델평가치를 가져오면 될듯.
#                 # 다만 그 자체로는 효과가 없을 수도 있고 마찬가지로 새로운 평가방법을 정해야할 것이다.
#                 continue
#             else:
#                 evaluateSentence(sess, model, sent)

if __name__ == '__main__':
    sent_eval_api('./mdl')