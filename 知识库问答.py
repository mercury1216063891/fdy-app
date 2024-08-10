import streamlit as st
from PIL import Image
import base64
import requests
import json
from voice_toolkit import voice_toolkit
import traceback

icon_path = "images/院徽.ico"

ICON = Image.open(icon_path)
with open(icon_path, "rb") as img_file:
    ICON_base64 = base64.b64encode(img_file.read()).decode()

st.set_page_config(
    page_title="辅导猿-知识库问答",
    layout="centered",
    page_icon=ICON,
)
with st.sidebar:
    icon_text = f"""
        <div class="icon-text-container" style="text-align: center;">
            <img src='data:image/png;base64,{ICON_base64}' alt='icon' style='width: 70px; height: 70px; margin: 0 auto; display: block;'>
            <span style='font-size: 24px;'>辅导猿-学生日常事务管家</span>
        </div>
        """
    st.markdown(
        icon_text,
        unsafe_allow_html=True,
    )


st.sidebar.title('输入')
option2 = st.sidebar.selectbox('方式', ['键盘', '语音'])

# 添加滑动条
if "n_results" not in st.session_state:
    st.session_state["n_results"] = 3
if "max_new_tokens" not in st.session_state:
    st.session_state["max_new_tokens"] = 500
    st.session_state["top_p"] = 0.9
    st.session_state["temperature"] = 0.1
    st.session_state["repetition_penalty"] = 1.0
st.sidebar.title('参数')
with st.sidebar.expander("文本生成"):
    parameter_5 = st.slider('n_results', min_value=1, max_value=5, value=st.session_state.n_results, step=1)
    parameter_1 = st.slider('max_new_tokens', min_value=50, max_value=1000,
                            value=st.session_state.max_new_tokens, step=50)
    parameter_2 = st.slider('top_p', min_value=0.5, max_value=0.95, value=st.session_state.top_p, step=0.01)
    parameter_3 = st.slider('temperature', min_value=0.1, max_value=5.0, value=st.session_state.temperature,
                            step=0.1)
    parameter_4 = st.slider('repetition_penalty', min_value=0.5, max_value=5.0,
                            value=st.session_state.repetition_penalty, step=0.1)

    st.session_state["n_results"] = parameter_5
    st.session_state["max_new_tokens"] = parameter_1
    st.session_state["top_p"] = parameter_2
    st.session_state["temperature"] = parameter_3
    st.session_state["repetition_penalty"] = parameter_4

st.title("📚 辅导猿")
st.caption("🌈 基于校园生活知识库来进行问答")


# 状态
if "chat_type" not in st.session_state or st.session_state["chat_type"] == "chat":
    st.session_state["chat_type"] = "chat_rag"

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

if "user_input_area" not in st.session_state:
    st.session_state.user_input_area = ""

if "user_voice_value" not in st.session_state:
    st.session_state.user_voice_value = ""

if "voice_flag" not in st.session_state:
    st.session_state["voice_flag"] = ""

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "message": "你好，我是湘潭大学学生日常事务管家“辅导猿”。"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["message"])


def send_message():
    payload = json.dumps({
        "chat_type": st.session_state.chat_type,
        "messages": st.session_state.messages,
        "max_new_tokens": st.session_state.max_new_tokens,
        "top_p": st.session_state.top_p,
        "temperature": st.session_state.temperature,
        "repetition_penalty": st.session_state.repetition_penalty,
        "n_results": st.session_state.n_results,
    })
    # print(type(payload), payload)
    headers = {'Content-Type': 'application/json'}
    url = "http://zklx.xtu.vip.cpolar.top/api-dev/qa/get_answer"
    try:
        response = requests.post(url, data=payload, headers=headers)
         # print(response, type(response))
        return response.text
    except Exception as e:
        error_message = f"错误: {e}\n{traceback.format_exc()}"
        print(error_message)
        return "未连接到服务器", 500



if option2 == "键盘":
    if prompt := st.chat_input(placeholder="输入..."):
        st.session_state.messages.append({"role": "user", "message": prompt})
        st.chat_message("user").write(prompt)
        answer = send_message()
        st.session_state.messages.append({"role": "assistant", "message": answer})
        st.chat_message("assistant").write(answer)
        print(st.session_state)

elif option2 == "语音":
    # 文本输入表单
    with st.form("input_form", clear_on_submit=True):
        prompt = st.text_area(
            "**输入：**",
            key="user_input_area",
            value=st.session_state.user_voice_value,
            help="在此输入文本或通过语音输入，语音输出暂不可用。"
        )
        submitted = st.form_submit_button("确认提交")

    # 处理提交
    if submitted:
        st.session_state.messages.append({"role": "user", "message": prompt})
        st.chat_message("user").write(prompt)
        answer = send_message()
        st.session_state.messages.append({"role": "assistant", "message": answer})
        st.chat_message("assistant").write(answer)

        st.session_state.user_voice_value = ""
        st.rerun()
    # 语音输入
    vocie_result = voice_toolkit()
    # vocie_result会保存最后一次结果
    if (
            vocie_result and vocie_result["voice_result"]["flag"] == "interim"
    ) or st.session_state["voice_flag"] == "interim":
        st.session_state["voice_flag"] = "interim"
        st.session_state["user_voice_value"] = vocie_result["voice_result"]["value"]
        if vocie_result["voice_result"]["flag"] == "final":
            st.session_state["voice_flag"] = "final"
            st.rerun()

