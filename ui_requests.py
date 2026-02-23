import streamlit as st
import os
import requests
import datetime
import json
import time

# 设置页面配置
st.set_page_config(
    page_title="爱聊天",
    page_icon="😋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# 对话信息
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 名称信息
if 'niki_name' not in st.session_state:
    st.session_state.niki_name = "小猫娘"

# 性格信息
if 'niki_nature' not in st.session_state:
    st.session_state.niki_nature = "你是一只可爱的小猫娘，请用温柔的语气回答客服的问题，并在句子的末尾带上“喵”"

# 会话时间
if 'current_session' not in st.session_state:
    st.session_state.current_session = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 设置大标题
st.title("爱聊天")
# logo - 增强路径处理
logo_path = "resource/logo.png"
# 尝试多种路径格式
possible_paths = [
    logo_path,
    "resource\\logo.png",
    os.path.join(os.getcwd(), "resource", "logo.png"),
    os.path.join(os.path.dirname(__file__), "resource", "logo.png")
]

logo_found = False
for path in possible_paths:
    try:
        if os.path.exists(path):
            st.logo(path)
            logo_found = True
            break
    except Exception as e:
        # 捕获任何路径相关的错误
        pass

if not logo_found:
    # 如果所有路径都失败，使用默认图标
    st.info("Logo文件不存在或无法访问，使用默认图标")
st.write("一个基于deepseek的聊天机器人")

# 保存会话
def save_session():
    # 确保会话数据完整
    session_data = {
        'niki_name': st.session_state.niki_name,
        'niki_nature': st.session_state.niki_nature,
        'current_session': st.session_state.current_session,
        'messages': st.session_state.messages
    }

    # 如果没有则创建 sessions 目录
    if not os.path.exists('sessions'):
        os.makedirs('sessions', exist_ok=True)

    # 保存会话数据
    try:
        with open(f'sessions/{st.session_state.niki_name}.json', 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        # 显示临时成功提示
        success_placeholder = st.empty()
        success_placeholder.success("会话已保存")
        # 3秒后清除提示
        time.sleep(3)
        success_placeholder.empty()
    except Exception as e:
        st.error(f"保存会话失败: {str(e)}")

# 侧边栏
with st.sidebar:
    st.subheader("会话信息")
    if st.button("新建会话", width='stretch', icon='🖊'):
        # 1.保存当前会话信息
        save_session()

        # 2.创建新的会话
        st.session_state.messages = []
        st.session_state.current_session = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_session()

    st.subheader("对象信息")
    name = st.text_input("对象名称", placeholder="请输入对象名称", value=st.session_state.niki_name)
    nature = st.text_area("对象性格", placeholder="请输入对象性格", value=st.session_state.niki_nature)

    if name != st.session_state.niki_name:
        st.session_state.niki_name = name
        save_session()
    if nature != st.session_state.niki_nature:
        st.session_state.niki_nature = nature
        save_session()

# 显示历史消息
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# 聊天输入
input = st.chat_input("Say something")
if input:
    # 显示用户消息
    st.chat_message("user").write(input)
    
    # 添加到会话历史
    st.session_state.messages.append({"role": "user", "content": input})
    
    # 使用requests库直接调用deepseek API
    try:
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            st.error("请设置DEEPSEEK_API_KEY环境变量")
        else:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": st.session_state.niki_nature},
                    *st.session_state.messages
                ],
                "stream": True
            }
            
            # 发送流式请求
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status()
            
            # 处理流式响应
            response_messages = st.empty()
            full_text = ""
            
            # 解析SSE格式的响应
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_part = line[6:]
                        if data_part == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_part)
                            if chunk.get('choices') and chunk['choices'][0].get('delta'):
                                text = chunk['choices'][0]['delta'].get('content', '')
                                if text:
                                    full_text += text
                                    response_messages.chat_message("ai").write(full_text)
                        except json.JSONDecodeError:
                            pass
            
            # 添加AI响应到会话历史
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            
            # 保存会话
            save_session()
    except requests.exceptions.RequestException as e:
        st.error(f"API调用失败: {str(e)}")
    except Exception as e:
        st.error(f"处理响应失败: {str(e)}")