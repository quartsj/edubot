import streamlit as st
from streamlit.components.v1 import html
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
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "summary_requested" not in st.session_state:
    st.session_state.summary_requested = False

# === 시스템 프롬프트 설정 ===
default_system_prompt = """
너는 이제부터 학생을 도와주는 **코드를 쉽게 분석해주는 튜터** 역할을 해.
너의 목표는 학생이 코드의 작동 원리를 스스로 이해할 수 있도록 돕는 거야.
설명은 **쉬운 말로**, 단계별로 진행하고, **학생이 이해하고 있는지 확인하기 위해 자주 질문**해.
처음엔 아래 3가지 질문을 한 번에 하지 말고 **하나씩**, **학생의 대답을 기다리며** 대화하듯 진행해:

1. "안녕하세요! 어떤 코드를 분석하고 싶은가요? 어떤 부분이 궁금한지 알려줄 수 있을까요?"
2. (대답 후) "좋아요! 혹시 학습 수준은 어떻게 되나요? 고등학생, 대학생, 직장인 중 어디에 속하나요?"
3. (대답 후) "이 코드에 대해서 이미 알고 있는 부분이 있다면 이야기해줄래요?"

학생의 답변을 받은 후 아래 규칙을 따라:

- 코드를 한 줄씩 또는 블록 단위로 나눠서 설명하고,
- 각 설명마다 "이 부분은 어떤 의미일까?" "이게 왜 필요했을까?"처럼 질문을 던지고,
- 헷갈릴 수 있는 부분은 간단한 예시나 비유로 풀어줘.
- 정답을 바로 말하지 말고, 학생이 생각하고 말하도록 유도해.
- 학생이 개념을 자기 말로 설명하거나, 비슷한 예시를 만들거나, 다른 문제에 적용할 수 있을 때까지 도와줘.

학생이 어느 정도 이해했다고 느껴지면 이렇게 마무리해:
"좋아요! 이제 이 코드를 네가 직접 설명할 수 있겠어요. 궁금한 게 더 있으면 언제든 물어봐!"
"""

# === 초기 메시지 설정 ===
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "system", "content": default_system_prompt})
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 코딩 도우미 챗봇 **에듀봇**입니다.\n알고 싶은 코드가 있다면 편하게 물어보세요 😊"})

# === 다크모드 CSS 적용 ===
def apply_theme():
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            .stApp {
                background-color: #121212;
                color: #e0e0e0;
            }
            .stTextInput>div>input, .stTextArea>div>textarea {
                background-color: #222222;
                color: #e0e0e0;
            }
            pre, code {
                background-color: #222222 !important;
                color: #e0e0e0 !important;
                padding: 10px;
                border-radius: 8px;
                overflow-x: auto;
            }
            .chat-user {
                background-color: #333a4d;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
            .chat-assistant {
                background-color: #003a6c;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            pre, code {
                background-color: #f5f5f5;
                color: #333333;
                padding: 10px;
                border-radius: 8px;
                overflow-x: auto;
            }
            .chat-user {
                background-color: #f0f0f5;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
            .chat-assistant {
                background-color: #e8f6ff;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
        </style>
        """, unsafe_allow_html=True)

# === 사이드바 설정 ===
st.sidebar.title("🔧 설정")
st.session_state.api_key = st.sidebar.text_input("🔐 OpenAI API Key", type="password", value=st.session_state.api_key)
model = st.sidebar.selectbox("💬 모델 선택", ["gpt-3.5-turbo", "gpt-4.1-mini"], index=1)
dark_mode_toggle = st.sidebar.checkbox("🌙 다크모드", value=st.session_state.dark_mode)
if dark_mode_toggle != st.session_state.dark_mode:
    st.session_state.dark_mode = dark_mode_toggle
    st.rerun()

if st.sidebar.button("📌 대화 요약하기"):
    st.session_state.summary_requested = True
    st.session_state.is_thinking = True
    st.rerun()

if st.sidebar.button("🧹 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": default_system_prompt}]
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 코딩 도우미 챗봇 **에듀봇**입니다.\n알고 싶은 코드가 있다면 편하게 물어보세요 😊"})
    st.session_state.chat_input = ""
    st.session_state.is_thinking = False
    st.session_state.clear_input = False
    st.rerun()

# 💾 대화 저장
def get_chat_log_text():
    chat_log = ""
    for msg in st.session_state.messages[1:]:
        role = "사용자" if msg["role"] == "user" else "GPT"
        chat_log += f"{role}: {msg['content']}\n\n"
    return chat_log

chat_log_text = get_chat_log_text()
st.sidebar.download_button(
    label="💾 대화 저장",
    data=chat_log_text,
    file_name=f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    mime="text/plain",
)

# === 클라이언트 생성 ===
if not st.session_state.api_key:
    st.warning("⚠️ OpenAI API 키가 필요합니다. 사이드바에서 입력해 주세요.")
    st.stop()

if st.session_state.client is None:
    st.session_state.client = OpenAI(api_key=st.session_state.api_key)

apply_theme()

# === 본문 ===
st.title("🤖 GPT-4.1 Mini 코딩봇")

# 채팅 메시지 출력
chat_messages = st.container()
with chat_messages:
    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>🧑‍💻 {msg['content']}</div>", unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            st.markdown(f"<div class='chat-assistant'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

# 자동 스크롤 처리
html("""
    <div id="scroll-anchor"></div>
    <script>
        const anchor = document.getElementById("scroll-anchor");
        if (anchor) {
            anchor.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    </script>
""", height=0, width=0)

# 입력창
if st.session_state.is_thinking:
    st.info("🤖 GPT가 응답 중입니다... 잠시만 기다려주세요.")
else:
    if st.session_state.clear_input:
        st.session_state.chat_input = ""
        st.session_state.clear_input = False

    user_input = st.text_area(
        "메시지를 입력하세요:",
        key="chat_input",
        height=150,
        placeholder="코드나 질문을 입력하세요. Shift+Enter로 줄바꿈 할 수 있어요.",
    )

if st.button("💬 물어보기", disabled=st.session_state.is_thinking) and st.session_state.chat_input.strip():
    st.session_state.is_thinking = True
    st.session_state.messages.append({"role": "user", "content": st.session_state.chat_input})
    st.rerun()

if st.session_state.is_thinking:
    with st.spinner("GPT가 생각 중입니다..."):
        try:
            if st.session_state.summary_requested:
                st.session_state.messages.append({
                    "role": "user",
                    "content": "지금까지의 대화를 학생이 복습할 수 있도록 간단하고 쉽게 요약해줘."
                })

            response = st.session_state.client.chat.completions.create(
                model=model,
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=500,
            )
            reply = response.choices[0].message.content

            if st.session_state.summary_requested:
                reply = f"📌 요약 결과:\n\n{reply}"
                st.session_state.summary_requested = False

            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"오류 발생: {e}")
        finally:
            st.session_state.is_thinking = False
            st.session_state.clear_input = True
            st.rerun()
