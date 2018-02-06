###############################################################################
# Default parameters

defaults = {
'hangeulPicklePath': './mdl/DistributionPickle.bin',
'dimUniVec': 67+1+1, # +1: 종성없음, +1: 한글이 아닌 글자. 만약 필요하다면 공백등을 유니그램 취급할 수
                     # 있겠지만 코드를 뜯어고쳐야할 것임. 사전에 문자를 추가하고 검사에 예외문을 넣는 등
'dimBiVec': 1750+1, # +1 은 인식할 수 없는 변수를 위해서 할당. 이건 밑에서 덮어씌우지 말것!!!!
'abnormalMethodRatio': {'randomVec': 0.7, 'glitchedBi': 0.3}, 
'biGramMutation': 0.2, # 말이 조금 애매한데 이건 두 글자 모두 한글인 바이그램이 얼마나 변이할지에 대한 확률임
'uniGlitchPoolSize': 5000, # 바이그램 glitch에서 얼마나 많은 유니그램을 참조할지에 대한 내용입니다.
'truncSamplingParam': {'upperBound': 4, 'numSamples': 100000},
'mergingWeight': 1, # 테이블 별로 비중을 두고 합칠때 곱하는 계수. 웨이트가 높을 수록 많이 반영한다.

#perform abnormal 할때 numNeeded를 받는데 이걸 실제 가진 학습데이터 저 위의 트렁케이티드 샘플링의 몇배로 할 것인지 지정하는 변수가 필요허미....
'abnormalRate': 5, # 정상 데이터에 비해 얼마나 많은 비정상 데이터를 가져올 것인가.
'foreignWrongAns': 5, # 얼마나 자주 외국인이 실제로 틀린 데어틀 쓸 것인가에 대한 기준입니다.
}

###############################################################################


###############################################################################
# User settings. Must have string 'Param' inside of the variable name.
daumParam = {
'mergingWeight' : 1, 
}

iirParam = {
'mergingWeight' : 1.7,
}

###############################################################################