#코딩 교육 챗봇은 이곳에 작성해주세요.
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="GPT-4.1 Mini 챗봇", layout="centered")

# === API Key 입력 및 세션 상태 저장 ===
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
api_key_input = st.text_input("OpenAI API Key를 입력하세요:", type="password", value=st.session_state.api_key)
st.session_state.api_key = api_key_input

st.title("GPT-4.1 Mini 챗봇")

# === 초기 세션 상태 설정 ===
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "당신은 코딩 교육을 위한 챗봇 AI입니다.당신의 역할은 초보자에게 낯설 수 있는 코딩 용어들을 이해하기 쉽게 자연어로 가르쳐주는 것입니다."}]
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# === 모델 및 temperature 설정 ===
model = st.selectbox("사용할 모델을 선택하세요:", ["gpt-3.5-turbo", "gpt-4.1-mini"], index=1, key="chat_model")

# === Clear 버튼 ===
if st.button("🧹 Clear 대화 초기화"):
    st.session_state.messages = [{"role": "system", "content": "당신은 코딩 교육을 위한 챗봇 AI입니다.당신의 역할은 초보자에게 낯설 수 있는 코딩 용어들을 이해하기 쉽게 자연어로 가르쳐주는 것입니다."}]
    st.session_state.chat_input = ""

# === 이전 메시지 출력 ===
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"**🧑 사용자:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 GPT:** {msg['content']}")

# === 사용자 입력 ===
user_input = st.text_input("메시지를 입력하세요:", value=st.session_state.chat_input, key="chat_input_box")

if user_input and st.session_state.api_key:
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
