import streamlit as st
import os
import sys
import subprocess
import datetime
import json

# 自动安装缺失的库
def install_missing_libraries():
    required_libraries = ['openai']
    
    for library in required_libraries:
        try:
            __import__(library)
        except ImportError:
            st.info(f"正在安装缺失的库: {library}")
            try:
                # 使用pip安装库
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', library])
                st.success(f"成功安装: {library}")
            except Exception as e:
                st.error(f"安装失败: {library}, 错误: {str(e)}")

# 检查并安装缺失的库
install_missing_libraries()

# 现在导入openai库
try:
    from openai import OpenAI
except ImportError:
    st.error("无法导入openai库，请手动安装: pip install openai")
    st.stop()


def getDateTime():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# 保存会话
def save_session() -> list:
    if st.session_state.current_session:
        session_data = {
                'niki_name':st.session_state.niki_name,
                'niki_nature':st.session_state.niki_nature,
                'current_session':st.session_state.current_session,
                'messages':st.session_state.messages
            }

        # 如果没有则创建
        if not os.path.exists('sessions'):
            os.mkdir('sessions')

        with open(f'sessions/{st.session_state.current_session}.json', 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False,indent=2)

    

# 加载目录
def load_sessions():
    session_list = []
    if os.path.exists('sessions'):
        for file in os.listdir('sessions'):
            if file.endswith('.json'):
                session_list.append(file.replace('.json', ''))
    return session_list[::-1]

#  删除会话     
def delete_session(session):
    try:
        if os.path.exists(f'sessions/{session}.json'):
            os.remove(f'sessions/{session}.json')
            st.success(f"删除成功: {session}")
            if session == st.session_state.current_session:      # 如果删除的是当前会话，则切换到默认会话
                st.session_state.current_session = getDateTime()
                st.session_state.messages = []

    except Exception as e:
        st.error(f"删除失败: {e}")
 
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

# 加载指定会话
def load_session(session_name):
    try:
        with open(f'sessions/{session_name}.json', 'r', encoding='utf-8') as f:
            session_data : dict = json.load(f)
            st.session_state.messages = session_data['messages']
            st.session_state.niki_name = session_data['niki_name']
            st.session_state.niki_nature = session_data['niki_nature']
            st.session_state.current_session = session_name
    except Exception as e:
        st.error(f"加载会话失败: {str(e)}")

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
    st.session_state.current_session = getDateTime()

# 设置大标题
st.title("爱聊天")
# logo
st.logo("resource\\logo.png")
st.write(f'会话时间:{st.session_state.current_session}')



# 侧边栏
with st.sidebar:
    st.subheader("会话信息")
    if st.button("新建会话",width='stretch',icon='🖊'):
        # 1.保存当前会话信息
        if st.session_state.messages:
            save_session()

        
            # 2.创建新的会话
            st.session_state.messages = []
            st.session_state.current_session = getDateTime()
            st.rerun()

    st.write('会话记录')
    for session in load_sessions():
        log, delete = st.columns([4,1])
        with log:
            if st.button(session, icon='📄', width='stretch',key=f"log_{session}",type='primary' if session == st.session_state.current_session else 'secondary'):     # 相同参数的组件会被归于同一个id，现在需要指定唯一id
                load_session(session)
                st.rerun()


        with delete:
            if st.button('',icon='❌',width='stretch',key=f"delete_{session}"):         # 默认是以按钮名字为key的
                delete_session(session)
                st.rerun()


    # 分割线
    st.divider()
    
    st.subheader("对象信息")
    name = st.text_input("对象名称",placeholder = "请输入对象名称", value = st.session_state.niki_name)
    nature = st.text_area("对象性格",placeholder = "请输入对象性格", value = st.session_state.niki_nature)

    if name:
        st.session_state.niki_name = name
    if nature:
        st.session_state.niki_nature = nature


# 创建OpenAI客户端
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)





for message in st.session_state.messages:           # messages {"role": "user", "content": input}
        st.chat_message(message["role"]).write(message["content"])


# 聊天输入
input = st.chat_input("Say something")
if input:
    st.chat_message("user").write(input)
    # 缓存用户输入
    st.session_state.messages.append({"role": "user", "content": input})
    # 使用OpenAI库调用deepseek API
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": st.session_state.niki_nature},
                *st.session_state.messages
            ],
            stream=True
        )

        response_messages = st.empty()
        full_text = ""
        for chunk in response:
            text = chunk.choices[0].delta.content
            full_text += text
            response_messages.chat_message("ai").write(full_text)
            

        st.session_state.messages.append({"role": "assistant", "content": full_text})

        save_session()
        st.rerun()
        
    except Exception as e:
        st.error(f"API调用失败: {str(e)}")

# 打印消息
# print([
#                 {"role": "system", "content": "你是一只可爱的小猫娘，请用温柔的语气回答客服的问题，并在句子的末尾带上“喵”"},
#                 *st.session_state.messages
#             ], '\n')