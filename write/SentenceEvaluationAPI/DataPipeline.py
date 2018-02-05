import pymysql
from Parameters import Parameters

class DataPipe:
    '''
    파라미터에 입력된 정보를 가지고 접근할 수 있는 모든 테이블에서 정보를 가져옵니다(currentParams).
    이때 순서대로 불러오기 때문에 구문/ 형태 모델에서 배치 단위로 가져오면 배치에 편향이 생깁니다.
    따라서 전부 불러온 다음 랜덤샘플링 하거나(이 경우가 이전 버전이었고, 자원이 매우 많이 필요합니다.),
    데이터베이스 서버에서 모든 데이터를 불러온 뷰를 만들고 그 뷰를 랜덤하게 정렬한 뒤 순차적으로 불러오는 방법이 있습니다.
    이 경우 트리거를 걸어서 integrity를 보장하는 등 귀찮은 작업이 있겠지만, 모든 데이터를 매우 빠르게 사용할 수 있습니다.
    '''
    def __init__(self, name):
        # 미리 설정한 파라미터를 오면서 지금 초기화를 진행합니다.
        # 리스트들은 앞으로 데이터를 뽑아낼 작업목록이고 current~ 는 시작시 없으므로 None으로 초기화합니다.
        DBparams = Parameters(name)
        self.zippedLine = zip(DBparams.paramNameList, DBparams.paramInfoList)
        self.currentLine = None
        self.currentParams = None

    def lineChange(self):
        # 이 함수를 실행하면 데이터를 가져오던 라인을 바꿉니다. 여기서는 테이블이 바뀝니다.
        # 만약 진행중인 작업을 모두 완료했다면 index error를 뱉습니다.
        try:
           self.currentLine, self.currentParams = next(self.zippedLine)
        except StopIteration:
            raise StopIteration

    def pump(self):
        # 말그대로 펌프입니다. 현재 설정된 라인으로부터 파라미터를 가져오고 연결해서 데이터를 가져오는 함수입니다.
        # 편의상 실제로 사용하는 것은 밑의 pumpData입니다. 가져올때 끼워넣어야할 함수가 있으면 밑에 같이 끼우시면 됩니다.
        args = self.currentParams['authenticationInfo']
        query = self.currentParams['query']
        numRows = self.currentParams['rowsPerPumping']
        cnt = 0
        while True:
            try:
                with pymysql.connect(*args, charset='utf8') as conn:
                    conn.execute(query)
                    # data processor가 db에 접근해서 문장을 가져올때, select문의 순서는
                    # 첫번째로 문장, 두번째로 표면 평점, 세번째로 심층 평점, 그 뒤에 필요한 다른 정보 순으로 하셔야 합니다.
                    while True:
                        rows = conn.fetchmany(numRows)
                        if rows == ():
                            break
                        for row in rows:
                            yield row
                    conn.close()
                    break
            except pymysql.err.OperationalError as errr:
                print('No response from the DB.')
                cnt += 1
                if cnt >= 3:
                    raise errr

    def pumpData(self):
        self.lineChange()
        return self.pump(), self.currentLine

if __name__ == '__main__':
    pipe = DataPipe()
    cnt = 0
    i, j = pipe.pumpData()
    for k in i:
        print(k, end = '\n')
        cnt += 1
        if cnt > 300:
            break


# 어디를 최적화 할까... 파라미터 받아오는 것 하나 고치고, 속도 올리도록 하나 고치고, 파이프라인 여러개 파도록 하나 고치고,
# 데이터 프로세서를 여러개 만들어서 합쳐버리는건 어떨까. 그렇게 데이터를 머징해버리고, 불러와서 학습시켜버리는거지 히히.
# 앗 근데 앱노말시켜논것들 문제가 잇다 문제가 잇어 이거 빼서 트랜잭션 만들고 비율정해줘야하는데...
