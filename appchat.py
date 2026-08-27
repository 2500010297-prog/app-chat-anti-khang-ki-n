from cryptography.fernet import Fernet
from deep_translator import GoogleTranslator
import streamlit as st

# 1. CẤU HÌNH GIAO DIỆN & ĐỔI MÀU NỀN TỐI (CYBER DARK)
st.set_page_config(
    page_title="E2EE Secure Chat", page_icon="🔒", layout="centered"
)

st.markdown(
    """
<style>
    /* Nền ứng dụng màu xám xanh Slate Navy chống mỏi mắt */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    /* Ô nhập tin nhắn và Selectbox */
    .stTextInput input, div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 2. KHỞI TẠO KHÓA BẢO MẬT E2EE
if "e2ee_key" not in st.session_state:
    st.session_state.e2ee_key = Fernet.generate_key()

if "messages" not in st.session_state:
    st.session_state.messages = []

cipher = Fernet(st.session_state.e2ee_key)

# 3. CÀI ĐẶT BIỆT DANH & AVATAR TRÊN THANH SIDEBAR
st.sidebar.title("⚙️ Thẻ Định Danh")
user_name = st.sidebar.text_input("👤 Biệt danh của bạn:", value="User_Alpha")
user_avatar = st.sidebar.selectbox(
    "🎭 Chọn Avatar (Emoji):",
    ["🥷", "🤖", "🦊", "👑", "⚡", "👽", "🐯", "😎"],
    index=0,
)

with st.sidebar.expander("🔑 Xem Khóa E2EE"):
    st.code(st.session_state.e2ee_key.decode(), language="text")

# 4. TIÊU ĐỀ ỨNG DỤNG
st.title("🔒 E2EE Cyber Chat")
st.caption(
    "Tin nhắn hiển thị mã hóa E2EE trực tiếp. Bấm nút để Giải mã & Dịch."
)
st.divider()

# 5. HIỂN THỊ DANH SÁCH TIN NHẮN
for idx, msg in enumerate(st.session_state.messages):
    # Sử dụng Biệt danh và Avatar tùy chỉnh
    with st.chat_message(
        msg["sender_name"], avatar=msg.get("avatar", "👤")
    ):
        # HIỂN THỊ MÃ E2EE TRỰC TIẾP LÀM NỘI DUNG CHÍNH
        encrypted_str = msg["payload"].decode("utf-8")
        st.code(encrypted_str, language="text")

        # Nút Giải mã và Dịch
        col1, col2 = st.columns([1.5, 3])
        with col1:
            if st.button(f"🔓 Giải mã & Dịch", key=f"btn_{idx}"):
                if not msg["decrypted_text"]:
                    # Bước 1: Giải mã E2EE tại chỗ
                    dec = cipher.decrypt(msg["payload"]).decode("utf-8")
                    msg["decrypted_text"] = dec

                    # Bước 2: Dịch sang Tiếng Việt
                    try:
                        translated = GoogleTranslator(
                            source="auto", target="vi"
                        ).translate(dec)
                        msg["translated_text"] = translated
                    except Exception:
                        msg["translated_text"] = dec

                msg["show_trans"] = not msg["show_trans"]
                st.rerun()

        # Hiển thị nội dung gốc và bản dịch khi nhấn nút
        if msg.get("show_trans"):
            st.success(f"💬 **Nội dung gốc:** {msg['decrypted_text']}")
            if msg.get("translated_text"):
                st.info(f"🌐 **Bản dịch (Tiếng Việt):** {msg['translated_text']}")

# 6. Ô NHẬP TIN NHẮN MỚI
if user_input := st.chat_input("Nhập tin nhắn (Ví dụ: Hello, how are you?)..."):
    # Mã hóa E2EE ngay tại thiết bị trước khi lưu
    encrypted_payload = cipher.encrypt(user_input.encode("utf-8"))

    st.session_state.messages.append(
        {
            "sender_name": user_name,
            "avatar": user_avatar,
            "payload": encrypted_payload,
            "decrypted_text": "",
            "translated_text": "",
            "show_trans": False,
        }
    )
    st.rerun()
