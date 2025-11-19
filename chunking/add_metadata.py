import json
import sys

# 파일 경로
input_file = "./output/2024-04-22_우리은행_비정형 데이터 자산화 시스템 2단계 구축_Ⅳ.기술부문.json"

# 추가할 메타데이터
metadata_prefix = "[문서연도: 2024] [기관: 우리은행] [프로젝트명: 우리은행 비정형 데이터 자산화 시스템 2단계 구축] [섹션: 기술 부문]\n\n"

# JSON 파일 읽기
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 각 content 앞에 메타데이터 추가
for key in data:
    for item in data[key]:
        if "content" in item:
            item["content"] = metadata_prefix + item["content"]

# 수정된 데이터를 같은 파일에 저장
with open(input_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 메타데이터 추가 완료!")
print(f"파일: {input_file}")
