import streamlit as st
from openai import OpenAI
from datetime import datetime

# === 페이지 설정 ===
st.set_page_config(page_title="코딩 도우미 코딩봇", layout="centered")

# === 세션 상태 초기화 ===
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""
if "is_thinking" not in st.session_state:
    st.session_state.is_thinking = False
if "client" not in st.session_state:
    st.session_state.client = None
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# === 시스템 프롬프트 설정 ===
default_system_prompt = """
너는 이제부터 학생을 도와주는 **코드를 쉽게 분석해주는 튜터** 역할을 해.
너의 목표는 학생이 코드의 작동 원리를 스스로 이해할 수 있도록 돕는 거야.
설명은 **쉬운 말로**, 단계별로 진행하고, **학생이 이해하고 있는지 확인하기 위해 자주 질문**해.

처음엔 학생이 먼저 말을 꺼낼 수도 있고, 너에게 질문을 먼저 할 수도 있어.
그럴 땐 무조건 네가 먼저 묻지 말고, **학생이 말한 내용을 바탕으로 답변을 시작해.**

만약 학생이 아무 말도 하지 않았다면 아래와 같이 천천히 질문을 유도해:

1. "안녕하세요! 어떤 코드를 분석하고 싶은가요? 어떤 부분이 궁금한지 알려줄 수 있을까요?"
2. (대답 후) "좋아요! 혹시 학습 수준은 어떻게 되나요? 고등학생, 대학생, 직장인 중 어디에 속하나요?"
3. (대답 후) "이 코드에 대해서 이미 알고 있는 부분이 있다면 이야기해줄래요?"

학생이 먼저 질문을 했다면, 그 코드나 내용에 맞춰 아래 방식으로 대화해:

- 코드를 한 줄씩 또는 블록 단위로 나눠서 설명하고,
- 각 설명마다 "이 부분은 어떤 의미일까?" "이게 왜 필요했을까?"처럼 질문을 던지고,
- 헷갈릴 수 있는 부분은 간단한 예시나 비유로 풀어줘.
- 정답을 바로 말하지 말고, 학생이 생각하고 말하도록 유도해.
- 학생이 개념을 자기 말로 설명하거나, 비슷한 예시를 만들거나, 다른 문제에 적용할 수 있을 때까지 도와줘.

학생이 어느 정도 이해했다고 느껴지면 이렇게 마무리해:

"좋아요! 이제 이 코드를 네가 직접 설명할 수 있겠어요. 궁금한 게 더 있으면 언제든 물어봐!"

절대 하지 말아야 할 것:
- 코드를 한 번에 다 설명하지 마.
- 학생에게 “이해했어?”라고 묻지 마. 대신, 직접 설명하거나 적용하게 해.
- 학생이 수동적으로 듣게 만들지 말고, 계속 질문을 던져서 능동적으로 참여하게 해.
"""

# 초기 system 메시지
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "system", "content": default_system_prompt})

# === 사이드바 설정 ===
st.sidebar.title("🔐 OpenAI API 설정")
api_key_input = st.sidebar.text_input("API Key를 입력하세요:", type="password", value=st.session_state.api_key)
st.session_state.api_key = api_key_input

if not api_key_input:
    st.sidebar.warning("⚠️ API Key를 입력해야 챗봇이 작동합니다. 사이드바에서 Key를 입력해주세요.")
else:
    if st.session_state.client is None:
        st.session_state.client = OpenAI(api_key=api_key_input)

# 모델 선택
model = st.sidebar.selectbox("모델 선택:", ["gpt-3.5-turbo", "gpt-4.1-mini"], index=1)
temperature = 0.7

# 대화 초기화
if st.sidebar.button("🧹 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": default_system_prompt}]
    st.session_state.chat_input = ""
    st.session_state.is_thinking = False
    st.success("대화가 초기화되었습니다.")

# === 대화 저장 ===
def save_chat_log():
    filename = f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in st.session_state.messages[1:]:
            role = "사용자" if msg["role"] == "user" else "GPT"
            f.write(f"{role}: {msg['content']}\n\n")
    st.success(f"💾 대화가 `{filename}` 파일로 저장되었습니다.")

if st.sidebar.button("💾 대화 저장하기"):
    save_chat_log()

# === 메인 화면 ===
st.title("🤖 코딩 도우미 코딩봇 ")

# 첫 인사 출력
if len(st.session_state.messages) == 1:
    st.markdown("""
    👋 **안녕하세요! 코딩봇입니다.**
    
    코딩 관련해서 궁금한 코드가 있다면 자유롭게 물어보세요!
    """)

# 대화 출력
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.markdown(f"<div style='background-color:#f0f0f5;padding:10px;border-radius:10px;margin-bottom:10px'><b>🧑 사용자:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            st.markdown(f"<div style='background-color:#e8f6ff;padding:10px;border-radius:10px;margin-bottom:10px'><b>🤖 코딩봇:</b><br>{msg['content']}</div>", unsafe_allow_html=True)

# 입력창
if st.session_state.is_thinking:
    st.info("🤖 코딩봇이 응답 중입니다... 잠시만 기다려주세요.")
else:
    if st.session_state.clear_input:
        st.session_state.chat_input = ""
        st.session_state.clear_input = False

    st.text_area(
        "메시지를 입력하세요:",
        key="chat_input",
        height=150,
        placeholder="코드나 질문을 입력하세요. Shift+Enter로 줄바꿈 할 수 있어요.",
    )

# GPT 응답 처리
if st.button("💬 물어보기", disabled=st.session_state.is_thinking) and st.session_state.chat_input.strip():
    if not api_key_input:
        st.error("❗ API Key가 필요합니다. 사이드바에서 입력해 주세요.")
    else:
        st.session_state.is_thinking = True
        st.session_state.messages.append({"role": "user", "content": st.session_state.chat_input})

        with st.spinner("GPT가 생각 중입니다..."):
            try:
                response = st.session_state.client.chat.completions.create(
                    model=model,
                    messages=st.session_state.messages,
                    temperature=temperature,
                    max_tokens=500,
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"오류 발생: {e}")
            finally:
                st.session_state.is_thinking = False
                st.session_state.clear_input = True
                st.rerun()
