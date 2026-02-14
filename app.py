import streamlit as st
import google.generativeai as genai
import datetime

# 1. API 키 설정 (보안 규칙 준수)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. 페이지 설정
st.set_page_config(page_title="척척박사 AI", page_icon="🎓", layout="wide")

# --- 테마 적용 함수 (CSS 주입 - 오타 수정 완료) ---
def apply_theme(theme):
    if theme == "다크 모드":
        st.markdown("""
            <style>
                .stApp { background-color: #0E1117; color: white; }
                [data-testid="stSidebar"] { background-color: #262730; }
                .stChatMessage { background-color: #1E1E1E !important; border-radius: 15px; border: 1px solid #333; }
                .stMarkdown { color: white; }
            </style>
        """, unsafe_allow_html=True) # 여기서 발생한 에러를 수정했습니다.
    else:
        st.markdown("""
            <style>
                .stApp { background-color: white; color: black; }
                [data-testid="stSidebar"] { background-color: #F0F2F6; }
                .stChatMessage { background-color: #F8F9FA !important; border-radius: 15px; border: 1px solid #EEE; }
                .stMarkdown { color: black; }
            </style>
        """, unsafe_allow_html=True)

# 3. 세션 상태 초기화
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "chat_delete_mode" not in st.session_state:
    st.session_state.chat_delete_mode = False
if "selected_chat_ids" not in st.session_state:
    st.session_state.selected_chat_ids = set()
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "라이트 모드(default)"

# 테마 즉시 적용
apply_theme(st.session_state.app_theme)

# 4. Gemini 모델 설정 (gemini-2.5-flash)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="너는 5살 아이에게 설명해주는 선생님이야. 모든 대답은 아주 쉽고 친절하게, 아이가 이해할 수 있는 단어만 사용해서 설명해줘."
)

# --- 사이드바 구성 ---
with st.sidebar:
    # 좌측 상단 설정 창
    with st.expander("⚙️ 설정 및 피드백"):
        st.subheader("테마 설정")
        theme_choice = st.radio("모드 선택", ["라이트 모드(default)", "다크 모드"], 
                                index=0 if st.session_state.app_theme == "라이트 모드(default)" else 1)
        if theme_choice != st.session_state.app_theme:
            st.session_state.app_theme = theme_choice
            st.rerun()
        
        st.divider()
        st.subheader("피드백 보내기")
        feedback_text = st.text_area("의견을 남겨주세요", placeholder="척척박사 AI에게 바라는 점...")
        if st.button("피드백 전송"):
            if feedback_text:
                st.toast("피드백이 전송되었습니다! 감사합니다. ❤️")
            else:
                st.warning("내용을 입력해주세요.")

    st.divider()
    
    # Playground 스타일 대화 목록 관리
    if st.button("➕ 새 대화 시작", use_container_width=True):
        new_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.all_chats[new_id] = {"name": f"새 대화 {len(st.session_state.all_chats)+1}", "messages": []}
        st.session_state.active_chat_id = new_id
        st.session_state.chat_delete_mode = False
        st.rerun()

    st.subheader("대화 목록 (Playground)")
    if st.button("🗑️ 목록 편집/삭제", use_container_width=True):
        st.session_state.chat_delete_mode = not st.session_state.chat_delete_mode
        st.rerun()

    if st.session_state.chat_delete_mode:
        if st.button("🔥 선택한 대화 확정 삭제", type="primary", use_container_width=True):
            for c_id in list(st.session_state.selected_chat_ids):
                if c_id in st.session_state.all_chats:
                    del st.session_state.all_chats[c_id]
            st.session_state.selected_chat_ids = set()
            st.session_state.active_chat_id = None
            st.session_state.chat_delete_mode = False
            st.rerun()

    # 대화 세션 리스트 렌더링
    for chat_id, chat_data in list(st.session_state.all_chats.items()):
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            if st.button(chat_data["name"], key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.active_chat_id = chat_id
        with cols[1]:
            if st.session_state.chat_delete_mode:
                is_checked = st.checkbox("", key=f"chk_{chat_id}", value=(chat_id in st.session_state.selected_chat_ids))
                if is_checked: st.session_state.selected_chat_ids.add(chat_id)
                else: st.session_state.selected_chat_ids.discard(chat_id)

# --- 메인 채팅창 ---
st.title("🎓 척척박사 AI")

if st.session_state.active_chat_id:
    current_chat = st.session_state.all_chats[st.session_state.active_chat_id]
    
    # 메시지 출력 루프
    for i, message in enumerate(current_chat["messages"]):
        role = message["role"]
        avatar = "🎓" if role == "assistant" else "👦"
        
        with st.chat_message(role, avatar=avatar):
            col1, col2 = st.columns([0.95, 0.05])
            with col1:
                st.markdown(message["content"])
            with col2:
                # 개별 메시지 삭제 버튼 (우클릭 대용)
                if st.button("❌", key=f"del_msg_{i}", help="이 메시지 삭제"):
                    current_chat["messages"].pop(i)
                    st.rerun()

    # 채팅 입력
    if prompt := st.chat_input("척척박사님께 질문해보세요!"):
        # 첫 질문으로 대화 제목 자동 생성
        if not current_chat["messages"]:
            current_chat["name"] = prompt[:15] + ("..." if len(prompt) > 15 else "")
        
        # 사용자 메시지 저장 및 표시
        current_chat["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👦"):
            st.markdown(prompt)

        # AI 응답 생성
        with st.chat_message("assistant", avatar="🎓"):
            # 이전 대화 맥락 구성
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                       for m in current_chat["messages"][:-1]]
            chat_session = model.start_chat(history=history)
            
            try:
                response = chat_session.send_message(prompt)
                st.markdown(response.text)
                current_chat["messages"].append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 '새 대화 시작'을 눌러 척척박사님과 대화를 시작하세요!")