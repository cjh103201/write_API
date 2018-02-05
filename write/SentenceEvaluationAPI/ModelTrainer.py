import os
import shutil
import time
import math
import numpy as np
import tensorflow as tf
from Parameters import Parameters
from VectorEmbedding import VectorFactory
from BasicOperator import BasicOperators

###################
batchSize = 1024
epochs = 100
keepProb = 0.5
numUniNeurons = 64
numBiNeurons = 128
###################
        
HanParams = Parameters('Hangeul').getDefaultParams
dimUniVec = HanParams['dimUniVec']
dimBiVec = HanParams['dimBiVec']


class FreqDistribution:
    pass # 피클파일 부르는 것 때문에 만든 abstract class입니다. 쓰지마세영

def getData():
    dataSet = VectorFactory().trainVector()
    np.random.shuffle(dataSet)
    return dataSet

def xavier_init(numInputs, numOutputs):
    init_range = math.sqrt(6.0/(numInputs+numOutputs))
    return tf.random_uniform([numInputs,numOutputs], -init_range, init_range)

def index2Vec(batchSize, dataSet):
    for itr in range(int(len(dataSet)/batchSize)):
        a = np.zeros([batchSize, dimUniVec]) # uni_X1
        b = np.zeros([batchSize, 1]) # uni_Y1
        c = np.zeros([batchSize, dimUniVec]) # uni_X2
        d = np.zeros([batchSize, 1]) # uni_Y2
        e = np.zeros([batchSize, dimBiVec*2]) # bi_X
        f = np.zeros([batchSize, 1]) # bi_Y
        for idx, vec in enumerate(dataSet[itr*batchSize: (itr+1)*batchSize]):
            for i in range(3):
                a[idx, vec.uni1Index[i]] = 1
                c[idx, vec.uni2Index[i]] = 1
            b[idx, 0] = vec.uni1Label
            d[idx, 0] = vec.uni2Label
            e[idx, vec.bi1Index] = 1
            e[idx, dimBiVec + vec.bi2Index] = 1
            f[idx, 0] = vec.biLabel
        yield a, b, c, d, e, f

def logLoss(pred, label):
    return tf.reduce_mean(-label*tf.log(pred+0.000001) - (1-label)*tf.log(1.000001 - pred))

def trainModel():
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        mdl = SurfaceModel()
        cnt = 0
        t = time.time()
        for epoch in range(epochs):
            dataSet = getData()
            trainVec = index2Vec(batchSize, dataSet)
            while True:
                try:
                    a, b, c, d, e, f = next(trainVec)
                except StopIteration:
                    break
                feedData = {mdl.uni_X1:a, mdl.uni_Y1:b, mdl.uni_X2:c, \
                mdl.uni_Y2:d, mdl.bi_X:e, mdl.bi_Y:f, mdl.prob:keepProb}
                sess.run(mdl.train_op, feed_dict = feedData)
                cnt += batchSize

            if epoch %1 == 0:
                feedData.update({mdl.prob:1})
                print('epoch', epoch+1,'loss:', sess.run(mdl.cost, feed_dict = feedData),
                    '#### about {:.2f} seconds left to be done...'.
                    format((epochs-epoch-1)*(time.time()-t)/(epoch+1)))

        saver = tf.train.Saver()
        savepath = BasicOperators().filePath('model')
        os.makedirs(savepath)
        saveModel = saver.save(sess,savepath+'/model.ckpt')
        shutil.copy('ModelTrainer.py', savepath+'/ModelTrainer.py')
        shutil.copytree('parameters', savepath+'parameters')
        print('{} bigrams learned'.format(cnt))

class SurfaceModel:
    uni_X1 = tf.placeholder(tf.float32)
    uni_X2 = tf.placeholder(tf.float32)

    uni_Y1 = tf.placeholder(tf.float32)
    uni_Y2 = tf.placeholder(tf.float32)

    bi_X = tf.placeholder(tf.float32)
    bi_Y = tf.placeholder(tf.float32)

    prob = tf.placeholder_with_default(1.0, shape=())

    uni_W1 = tf.Variable(xavier_init(dimUniVec, numUniNeurons), name = 'UniWeights1') #69, numNeurons
    uni_B1 = tf.Variable(tf.zeros([numUniNeurons]), name = 'UniBias1')
    uL11 = tf.add(tf.matmul(uni_X1, uni_W1), uni_B1)
    uL11 = tf.nn.relu(uL11)
    uL12 = tf.add(tf.matmul(uni_X2, uni_W1), uni_B1)
    uL12 = tf.nn.relu(uL12)
    uL11 = tf.nn.dropout(uL11, prob)
    uL12 = tf.nn.dropout(uL12, prob)

    uni_W2 = tf.Variable(xavier_init(numUniNeurons, 1), name = 'UniWeights2')
    uni_B2 = tf.Variable(tf.zeros([1]), name = 'UniBias2')
    uL21 = tf.add(tf.matmul(uL11, uni_W2), uni_B2)
    model_uni1 = tf.nn.sigmoid(uL21)
    uL22 = tf.add(tf.matmul(uL12, uni_W2), uni_B2)
    model_uni2 = tf.nn.sigmoid(uL22)

    bi_W1 = tf.Variable(xavier_init(dimBiVec*2 + 2, numBiNeurons), name = 'BiWeights1')
    bi_B1= tf.Variable(tf.zeros([numBiNeurons]), name = 'BiBias1')
    bL1 = tf.add(tf.matmul(tf.concat([bi_X, model_uni1, model_uni2], 1) ,bi_W1), bi_B1)
    bL1 = tf.nn.relu(bL1)
    bL1 = tf.nn.dropout(bL1, prob)

    bi_W2 = tf.Variable(xavier_init(numBiNeurons, numBiNeurons), name = 'BiWeights2')
    bi_B2= tf.Variable(tf.zeros([numBiNeurons]), name = 'BiBias2')
    bL2 = tf.add(tf.matmul(bL1, bi_W2), bi_B2)
    bL2 = tf.nn.relu(bL2)
    bL2 = tf.nn.dropout(bL2, prob)

    bi_W3 = tf.Variable(xavier_init(numBiNeurons, 1), name = 'BiWeights3')
    bi_B3= tf.Variable(tf.zeros([1]), name = 'BiBias3')
    bL3 = tf.add(tf.matmul(bL2 ,bi_W3), bi_B3)
    model_bi = tf.nn.sigmoid(bL3)

    cost1 = logLoss(model_uni1, uni_Y1)
    cost2 = logLoss(model_uni2, uni_Y2)
    cost3 = logLoss(model_bi, bi_Y)
    lossL2 = tf.add_n([tf.nn.l2_loss(v) for v in tf.trainable_variables() if 'Bias' not in v.name]) * 0.001
    cost = (cost1 + cost2)/2 + 5 * cost3 + lossL2

    optimizer = tf.train.AdamOptimizer(learning_rate=(10 ** -4))
    train_op = optimizer.minimize(cost)

if __name__ == '__main__':
    trainModel()