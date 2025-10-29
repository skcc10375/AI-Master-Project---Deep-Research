# 🔬 Deep Researcher 디버깅 가이드

이 가이드는 Deep Researcher의 흐름을 이해하고 디버깅하는 방법을 설명합니다.

## 📋 목차
- [VS Code 디버거 설정](#vs-code-디버거-설정)
- [기본 디버깅 방법](#기본-디버깅-방법)
- [특정 노드 테스트](#특정-노드-테스트)
- [디버깅 팁](#디버깅-팁)

---

## VS Code 디버거 설정

### 1. 설정 파일

프로젝트에 `.vscode/launch.json` 파일을 만들었습니다. 
이 파일에는 두 가지 디버깅 설정이 포함되어 있습니다:

- **Python: Deep Researcher Debug**: 전체 그래프 실행
- **Python: Current File**: 현재 열린 파일 실행

### 2. 필요한 확장 프로그램

VS Code에서 **Python** 확장 프로그램이 설치되어 있어야 합니다.

---

## 기본 디버깅 방법

### 방법 1: 전체 그래프 실행

1. **중단점(Breakpoint) 설정**
   - `deep_researcher.py` 파일을 엽니다
   - 디버깅하고 싶은 라인 번호 왼쪽을 클릭하여 빨간 점을 만듭니다
   - 예: `clarify_with_user` 함수의 첫 줄에 중단점 설정

2. **디버거 실행**
   - `F5` 키를 누르거나
   - 좌측 사이드바에서 🐛 아이콘 클릭 → "Python: Deep Researcher Debug" 선택 → 재생 버튼

3. **실행 중 탐색**
   - **F10**: Step Over (현재 줄 실행 후 다음으로)
   - **F11**: Step Into (함수 안으로 들어가기)
   - **Shift+F11**: Step Out (함수에서 나오기)
   - **F5**: Continue (다음 중단점까지 실행)

4. **변수 확인**
   - 좌측 **Variables** 패널에서 현재 변수들 확인
   - **Watch** 패널에 관심있는 표현식 추가
   - 코드 위에 마우스를 올려서 값 확인

### 방법 2: 특정 노드만 테스트

`debug_specific_node.py` 파일을 사용해서 특정 함수만 실행할 수 있습니다.

```python
# debug_specific_node.py에서
test_clarify_with_user()  # 원하는 함수 호출
```

---

## 그래프 흐름 이해

### 전체 플로우

```
START → clarify_with_user → write_research_brief → research_supervisor → final_report_generation → END
```

### 주요 노드 설명

#### 1. **clarify_with_user** (라인 65-169)
- **역할**: 사용자의 질문이 명확한지 확인
- **입력**: 사용자 메시지
- **출력**: clarifications 또는 research_brief로 이동
- **중단점 추천**: 라인 79, 104, 119

#### 2. **write_research_brief** (라인 171-261)
- **역할**: 연구 계획 작성
- **입력**: 사용자 질문
- **출력**: 연구 계획 (research_brief)
- **중단점 추천**: 라인 184, 218, 253

#### 3. **research_supervisor** (서브그래프, 라인 263-494)
- **역할**: 실제 연구 수행 (여러 서브-노드 포함)
- **서브 노드들**:
  - `lead_researcher_step`: 연구 계획 실행
  - `scraper_step`: 정보 수집
  - `planner_step`: 다음 단계 계획
  - `note_compression`: 메모 압축

#### 4. **final_report_generation** (라인 496-698)
- **역할**: 최종 리포트 생성
- **입력**: 수집된 연구 데이터
- **출력**: 최종 리포트

---

## 디버깅 팁

### 1. State 추적

각 노드는 `state`를 받아서 반환합니다. 중단점을 설정해서 state를 확인하세요:

```python
def some_node(state: AgentState, config: RunnableConfig):
    # 여기에 중단점 설정
    messages = state["messages"]  # messages 상태 확인
    return {"messages": [...]}   # 반환값 확인
```

### 2. Config 확인

각 노드는 `config`를 받습니다. configurable 값을 확인하세요:

```python
def some_node(state: AgentState, config: RunnableConfig):
    # Config 확인
    configurable = Configuration.from_runnable_config(config)
    model = configurable.research_model  # 어떤 모델 사용하는지
```

### 3. 메시지 체인 추적

messages를 확인해서 전체 대화 흐름을 파악하세요:

```python
for msg in state["messages"]:
    print(msg.type, msg.content)
```

### 4. Tool 호출 확인

도구가 어떻게 호출되는지 확인:

```python
# anthropic_websearch_called 같은 함수 사용
if anthropic_websearch_called(messages):
    print("Web search was called!")
```

---

## 실제 사용 예시

### 예시 1: clarify_with_user의 흐름 따라가기

1. `deep_researcher.py` 파일에서 라인 65에 중단점 설정
2. `debug_runner.py` 실행 (F5)
3. 함수 내부로 들어가서 (F11) step-by-step 실행
4. 라인 79에서 `allow_clarification` 값 확인
5. 라인 104에서 clarification model 확인
6. 라인 119에서 결과 확인

### 예시 2: research_brief 생성 과정 확인

1. `write_research_brief` 함수 (라인 171)에 중단점
2. 라인 184에서 topic 확인
3. 라인 218에서 brief 생성 확인
4. 라인 253에서 최종 output 확인

### 예시 3: 연구 노드의 내부 흐름

1. `lead_researcher_step` 함수에 중단점
2. 어떤 도구가 호출되는지 확인
3. 메시지가 어떻게 추가되는지 확인

---

## 문제 해결

### 문제: "Module not found"
**해결**: `.env` 파일에 필요한 환경변수 설정 확인

### 문제: "Timeout error"
**해결**: `max_tokens` 값을 늘리거나 `stream=False` 설정

### 문제: "Model not found"
**해결**: config에서 사용 가능한 모델 이름으로 변경

---

## 추가 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [LangSmith 추적](https://smith.langchain.com/)
- 프로젝트 README.md 파일 참조

