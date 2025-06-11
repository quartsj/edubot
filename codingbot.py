import streamlit as st
from openai import OpenAI
from datetime import datetime
from streamlit.components.v1 import html

# === 페이지 설정 ===
st.set_page_config(page_title="코딩 도우미 코딩봇", layout="centered")

# === 세션 상태 초기화 ===
state_defaults = {
    "api_key": "",
    "messages": [],
    "chat_input": "",
    "is_thinking": False,
    "client": None,
    "clear_input": False,
    "dark_mode": False,
    "summary_requested": False,
}
for key, value in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

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

if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "system", "content": default_system_prompt})
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 코딩 도우미 챗봇 **에듀봇**입니다.\n알고 싶은 코드가 있다면 편하게 물어보세요 😊", "time": datetime.now()})

# === 다크모드 CSS 적용 ===
def apply_theme():
    dark = st.session_state.dark_mode
    css = """
        <style>
            .stApp { background-color: %s; color: %s; }
            .chat-box { background-color: %s; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
            .chat-time { font-size: 0.75rem; opacity: 0.6; }
            pre, code {
                background-color: %s !important; color: %s !important;
                padding: 10px; border-radius: 8px;
                overflow-x: auto;
            }
        </style>
    """ % (
        "#121212" if dark else "white",
        "#e0e0e0" if dark else "#333333",
        "#333a4d" if dark else "#f0f0f5",
        "#222222" if dark else "#f5f5f5",
        "#e0e0e0" if dark else "#333333"
    )
    st.markdown(css, unsafe_allow_html=True)

# === 사이드바 ===
st.sidebar.title("🔧 설정")
st.session_state.api_key = st.sidebar.text_input("🔐 OpenAI API Key", type="password", value=st.session_state.api_key)
model = st.sidebar.selectbox("💬 모델 선택", ["gpt-3.5-turbo", "gpt-4.1-mini"], index=1)
st.session_state.dark_mode = st.sidebar.checkbox("🌙 다크모드", value=st.session_state.dark_mode)

if st.sidebar.button("📌 대화 요약하기"):
    st.session_state.summary_requested = True
    st.session_state.is_thinking = True
    st.rerun()

if st.sidebar.button("🧹 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": default_system_prompt}]
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 코딩 도우미 챗봇 **에듀봇**입니다.\n알고 싶은 코드가 있다면 편하게 물어보세요 😊", "time": datetime.now()})
    st.session_state.chat_input = ""
    st.session_state.is_thinking = False
    st.session_state.clear_input = False
    st.rerun()

# === 대화 저장 기능 ===
def get_chat_log_text():
    chat_log = ""
    for msg in st.session_state.messages[1:]:
        role = "사용자" if msg["role"] == "user" else "GPT"
        time_str = msg.get("time", datetime.now()).strftime("%Y-%m-%d %H:%M")
        chat_log += f"[{time_str}] {role}: {msg['content']}\n\n"
    return chat_log

chat_log_text = get_chat_log_text()
st.sidebar.download_button(
    label="💾 대화 저장",
    data=chat_log_text,
    file_name=f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    mime="text/plain",
)

# === API Key 확인 ===
if not st.session_state.api_key:
    st.warning("⚠️ OpenAI API 키가 필요합니다. 사이드바에서 입력해 주세요.")
    st.stop()

if st.session_state.client is None:
    st.session_state.client = OpenAI(api_key=st.session_state.api_key)

# === 테마 적용 ===
apply_theme()

st.title("🤖 GPT-4.1 Mini 코딩봇")

# === 대화 출력 ===
with st.container():
    for msg in st.session_state.messages[1:]:
        role = "🧑‍💻 사용자" if msg["role"] == "user" else "🤖 GPT"
        time_str = msg.get("time", datetime.now()).strftime("%H:%M:%S")
        css_class = "chat-box"
        st.markdown(
            f"<div class='{css_class}'><strong>{role}</strong><br>{msg['content']}<div class='chat-time'>{time_str}</div></div>",
            unsafe_allow_html=True
        )

# === 자동 스크롤 ===
html("""
    <div id="scroll-anchor"></div>
    <script>
        const anchor = document.getElementById("scroll-anchor");
        if (anchor) {
            anchor.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    </script>
""", height=0)

# === 입력 폼 ===
if st.session_state.clear_input:
    st.session_state.chat_input = ""
    st.session_state.clear_input = False

# 자동 포커스 스크립트 (textarea에 포커스)
html("""
    <script>
        window.onload = function() {
            const ta = document.querySelector('textarea[aria-label="메시지를 입력하세요:"]');
            if (ta) ta.focus();
        }
    </script>
""", height=0)

user_input = st.text_area(
    "메시지를 입력하세요:",
    key="chat_input",
    height=150,
    placeholder="코드나 질문을 입력하세요. Shift+Enter로 줄바꿈 할 수 있어요.",
)

if st.button("💬 물어보기", disabled=st.session_state.is_thinking) and st.session_state.chat_input.strip():
    st.session_state.is_thinking = True
    st.session_state.messages.append({
        "role": "user",
        "content": st.session_state.chat_input,
        "time": datetime.now()
    })
    st.rerun()

# === GPT 응답 처리 ===
if st.session_state.is_thinking:
    with st.spinner("GPT가 생각 중입니다..."):
        try:
            if st.session_state.summary_requested:
                st.session_state.messages.append({
                    "role": "user",
                    "content": "지금까지의 대화를 학생이 복습할 수 있도록 간단하고 쉽게 요약해줘.",
                    "time": datetime.now()
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

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "time": datetime.now()
            })
        except Exception as e:
            st.error(f"오류 발생: {e}")
        finally:
            st.session_state.is_thinking = False
            st.session_state.clear_input = True
            st.rerun()
