import streamlit as st
import google.generativeai as genai
import datetime

# 1. API 키 설정 (보안 규칙 준수)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. 페이지 설정
st.set_page_config(page_title="척척박사 AI", page_icon="🎓", layout="wide")

# 3. 세션 상태 초기화 (Playground 구조)
if "all_chats" not in st.session_state:
    # { "chat_id": {"name": "대화 제목", "messages": []} }
    st.session_state.all_chats = {}

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

if "chat_delete_mode" not in st.session_state:
    st.session_state.chat_delete_mode = False

if "selected_chat_ids" not in st.session_state:
    st.session_state.selected_chat_ids = set()

# 4. Gemini 모델 설정 (System Instruction 적용)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="너는 5살 아이에게 설명해주는 선생님이야. 모든 대답은 아주 쉽고 친절하게, 아이가 이해할 수 있는 단어만 사용해서 설명해줘."
)

# --- 사이드바: Playground 대화 관리 목록 ---
with st.sidebar:
    st.title("🎓 척척박사 AI")
    
    if st.button("➕ 새 대화 시작", use_container_width=True):
        new_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.all_chats[new_id] = {"name": f"새 대화 {len(st.session_state.all_chats)+1}", "messages": []}
        st.session_state.active_chat_id = new_id
        st.session_state.chat_delete_mode = False
        st.rerun()

    st.divider()
    st.subheader("대화 목록 (Playground)")

    # 대화 내용 지우기(관리) 모드 토글 버튼
    if st.button("🗑️ 목록 편집/삭제", use_container_width=True):
        st.session_state.chat_delete_mode = not st.session_state.chat_delete_mode
        st.rerun()

    if st.session_state.chat_delete_mode:
        st.warning("삭제할 대화를 선택하세요.")
        if st.button("🔥 선택한 대화 삭제", type="primary", use_container_width=True):
            for c_id in st.session_state.selected_chat_ids:
                del st.session_state.all_chats[c_id]
            st.session_state.selected_chat_ids = set()
            st.session_state.active_chat_id = None
            st.session_state.chat_delete_mode = False
            st.rerun()

    # 대화 세션 리스트 표시
    for chat_id, chat_data in list(st.session_state.all_chats.items()):
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            # 대화 선택 버튼
            if st.button(chat_data["name"], key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.active_chat_id = chat_id
        with cols[1]:
            # 삭제 선택 체크박스 (Playground 관리 기능)
            if st.session_state.chat_delete_mode:
                is_checked = st.checkbox("", key=f"chk_{chat_id}", 
                                         value=(chat_id in st.session_state.selected_chat_ids))
                if is_checked:
                    st.session_state.selected_chat_ids.add(chat_id)
                else:
                    st.session_state.selected_chat_ids.discard(chat_id)
            elif st.session_state.active_chat_id == chat_id:
                st.write("📍")

# --- 메인 채팅창 ---
if st.session_state.active_chat_id:
    current_chat = st.session_state.all_chats[st.session_state.active_chat_id]
    
    # 메시지 출력 루프
    for i, message in enumerate(current_chat["messages"]):
        role = message["role"]
        avatar = "🎓" if role == "assistant" else "👦"
        
        with st.chat_message(role, avatar=avatar):
            # 메시지 삭제 기능 (우클릭 대신 표시되는 삭제 버튼)
            col1, col2 = st.columns([0.92, 0.08])
            with col1:
                st.markdown(message["content"])
            with col2:
                if st.button("❌", key=f"del_msg_{i}", help="이 메시지 삭제"):
                    current_chat["messages"].pop(i)
                    st.rerun()

    # 채팅 입력
    if prompt := st.chat_input("척척박사님께 질문해보세요!"):
        # 첫 메시지인 경우 대화 제목 업데이트
        if not current_chat["messages"]:
            current_chat["name"] = prompt[:15] + ("..." if len(prompt) > 15 else "")
        
        # 사용자 메시지 추가
        current_chat["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👦"):
            st.markdown(prompt)

        # AI 응답 생성
        with st.chat_message("assistant", avatar="🎓"):
            # 대화 기록 구성 (Memory)
            history = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in current_chat["messages"][:-1]
            ]
            chat_session = model.start_chat(history=history)
            
            try:
                response = chat_session.send_message(prompt)
                full_response = response.text
                st.markdown(full_response)
                current_chat["messages"].append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"오류 발생: {e}")
else:
    st.info("왼쪽 사이드바에서 '새 대화 시작'을 눌러 척척박사님과 대화를 시작해보세요!")