import streamlit as st
from openai import OpenAI
from datetime import datetime
from streamlit.components.v1 import html

# 페이지 설정
st.set_page_config(page_title="코딩 도우미 코딩봇", layout="centered")

# 세션 상태 초기화
for key, default in {
    "api_key": "",
    "messages": [],
    "chat_input": "",
    "is_thinking": False,
    "client": None,
    "clear_input": False,
    "dark_mode": False,
    "summary_requested": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 시스템 프롬프트
default_system_prompt = """너는 이제부터 학생을 도와주는 **코드를 쉽게 분석해주는 튜터** 역할을 해... (생략)"""
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "system", "content": default_system_prompt})
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 코딩 도우미 챗봇 **에듀봇**입니다.\n알고 싶은 코드가 있다면 편하게 물어보세요 😊"})

# 테마 적용
def apply_theme():
    style = """
    <style>
        pre, code {
            background-color: %s !important;
            color: %s !important;
            padding: 10px;
            border-radius: 8px;
            overflow-x: auto;
        }
        .chat-user {
            background-color: %s;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .chat-assistant {
            background-color: %s;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }
    </style>
    """ % (
        "#222222" if st.session_state.dark_mode else "#f5f5f5",
        "#e0e0e0" if st.session_state.dark_mode else "#333333",
        "#333a4d" if st.session_state.dark_mode else "#f0f0f5",
        "#003a6c" if st.session_state.dark_mode else "#e8f6ff",
    )
    st.markdown(style, unsafe_allow_html=True)

# 사이드바 설정
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

chat_log_text = "\n\n".join(
    f"{'사용자' if msg['role']=='user' else 'GPT'}: {msg['content']}"
    for msg in st.session_state.messages[1:]
)
st.sidebar.download_button(
    label="💾 대화 저장",
    data=chat_log_text,
    file_name=f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    mime="text/plain",
)

# API 키가 없으면 중단
if not st.session_state.api_key:
    st.warning("⚠️ OpenAI API 키가 필요합니다. 사이드바에서 입력해 주세요.")
    st.stop()
if st.session_state.client is None:
    st.session_state.client = OpenAI(api_key=st.session_state.api_key)

apply_theme()
st.title("🤖 GPT-4.1 Mini 코딩봇")

# === 메시지 출력 및 자동 스크롤 ===
messages_html = ""
for msg in st.session_state.messages[1:]:
    role_class = "chat-user" if msg["role"] == "user" else "chat-assistant"
    icon = "🧑‍💻" if msg["role"] == "user" else "🤖"
    messages_html += f"<div class='{role_class}'>{icon} {msg['content']}</div>"

html(f"""
    {messages_html}
    <div id="scroll-anchor"></div>
    <script>
        setTimeout(function() {{
            var anchor = document.getElementById("scroll-anchor");
            if (anchor) {{
                anchor.scrollIntoView({{ behavior: "smooth" }});
            }}
        }}, 100);
    </script>
""", height=600, scrolling=True)

# === 사용자 입력 ===
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

# === GPT 응답 ===
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
