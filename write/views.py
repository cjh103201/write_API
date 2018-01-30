from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
class JSONResponse(HttpResponse) :
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

"""
post 방식으로 문장을 입력받아, 점수와 상/중/하 결과 반환
json data 형식으로 통신
parameter : { "sentence": "안녕하세요. 저는 집에 가고 싶어요." }
return : {"score": 90, "evaluation": "상"}
"""
@csrf_exempt
def write_api(request) :
    if request.method == 'POST' :
        # input
        data = JSONParser().parse(request)
        sentence = data["sentence"]

        #입력된 문장 평가 진행!


        #output
        score = 90
        evaluation = "상"
        result = {
            "score" : score,
            "evaluation" : evaluation
        }
        dump = json.dumps(result, ensure_ascii=False)
        return JSONResponse(dump, content_type="application/json")




"""
get 방식으로 문장을 입력받아, 점수와 상/중/하 결과 반환
"""
@csrf_exempt
def get_write(request, sentence) :
    #get으로 입력받은 데이터 = sentence
    print(sentence)
    score = 60
    evaluation = "하"
    result = {
        "score": score,
        "evaluation": evaluation
    }
    dump = json.dumps(result, ensure_ascii=False)
    return JSONResponse(dump, content_type="application/json")
