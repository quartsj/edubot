import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="GPT-4.1 Mini 챗봇", layout="centered")

# === API Key 입력 및 세션 상태 저장 ===
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
api_key_input = st.text_input("OpenAI API Key를 입력하세요:", type="password", value=st.session_state.api_key)
st.session_state.api_key = api_key_input

st.title("GPT-4.1 Mini 챗봇")

# === 초기 시스템 메시지 ===
default_system_prompt = """
너는 Streamlit과 ChatGPT 연동 코딩을 처음 배우는 사람을 위한 친절한 교육용 챗봇이야.

사용자가 코딩 용어나 개념(예: API, 함수, 변수, 프롬프트 등)을 물어보면,
전문 용어처럼 어렵게 설명하지 말고, 초등학생에게 말하듯 아주 쉽게 설명해줘.

예를 들어 'API'를 물어보면 “인터넷에 있는 자판기처럼, 원하는 정보를 달라고 하면 주는 것”처럼 비유를 들어서 말해줘.

설명할 때는:
- 어려운 용어는 먼저 자연어로 풀어 설명하고
- 쉬운 예시나 비유를 꼭 포함하고
- 질문자가 더 물어보도록 “혹시 더 궁금한 거 있어요?” 같은 말로 대화를 이어가줘.

항상 친절하고 천천히, 부담 없게 설명해줘.
"""

# === 초기 세션 상태 설정 ===
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": default_system_prompt}]
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# === 모델 및 temperature 설정 ===
model = st.selectbox("사용할 모델을 선택하세요:", ["gpt-3.5-turbo", "gpt-4.1-mini"], index=1, key="chat_model")
temperature = 0.7  # 안정적인 창의성 제공

# === Clear 버튼 ===
if st.button("🧹 Clear 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": default_system_prompt}]
    st.session_state.chat_input = ""

# === 이전 메시지 출력 ===
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"**🧑 사용자:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 GPT:** {msg['content']}")

# === 사용자 입력 ===
user_input = st.text_input("메시지를 입력하세요:", value=st.session_state.chat_input, key="chat_input_box")

# === '물어보기' 버튼 추가 ===
if st.button("💬 물어보기") and user_input and st.session_state.api_key:
    # 입력값 저장 후 초기화
    st.session_state.chat_input = user_input
    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        client = OpenAI(api_key=st.session_state.api_key)
        response = client.chat.completions.create(
            model=model,
            messages=st.session_state.messages,
            temperature=temperature,
            max_tokens=500,
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.chat_input = ""  # 입력창 초기화

    except Exception as e:
        st.error(f"오류 발생: {str(e).encode('utf-8', errors='ignore').decode('utf-8')}")
