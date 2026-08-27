import base64
import hashlib
from deep_translator import GoogleTranslator
import streamlit as st

# 1. CẤU HÌNH GIAO DIỆN CYBER DARK
st.set_page_config(
    page_title="E2EE Secure Chat", page_icon="🔒", layout="centered"
)

st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    .stTextInput input, div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 2. THUẬT TOÁN MÃ HÓA TỈ LỆ THEO ĐỘ DÀI VĂN BẢN (STREAM CIPHER)
def encrypt_proportional(text: str, key_str: str) -> str:
    raw_bytes = text.encode("utf-8")
    key_bytes = hashlib.sha256(key_str.encode("utf-8")).digest()
    cipher_bytes = bytearray()
    for i, b in enumerate(raw_bytes):
        k = key_bytes[i % len(key_bytes)] ^ ((i * 17) & 0xFF)
        cipher_bytes.append(b ^ k)
    return base64.b64encode(cipher_bytes).decode("utf-8")


def decrypt_proportional(cipher_str: str, key_str: str) -> str:
    try:
        cipher_bytes = base64.b64decode(cipher_str.encode("utf-8"))
        key_bytes = hashlib.sha256(key_str.encode("utf-8")).digest()
        raw_bytes = bytearray()
        for i, b in enumerate(cipher_bytes):
            k = key_bytes[i % len(key_bytes)] ^ ((i * 17) & 0xFF)
            raw_bytes.append(b ^ k)
        return raw_bytes.decode("utf-8")
    except Exception:
        return "[Lỗi giải mã]"


# 3. KHỞI TẠO BỘ NHỚ
if "e2ee_key" not in st.session_state:
    st.session_state.e2ee_key = "SecretKey_CyberVault_2026"

if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. THANH SIDEBAR TÙY CHỈNH BIỆT DANH & AVATAR
st.sidebar.title("⚙️ Thẻ Định Danh")
user_name = st.sidebar.text_input("👤 Biệt danh của bạn:", value="User_Alpha")
user_avatar = st.sidebar.selectbox(
    "🎭 Chọn Avatar (Emoji):",
    ["🥷", "🤖", "🦊", "👑", "⚡", "👽", "🐯", "😎"],
    index=0,
)

with st.sidebar.expander("🔑 Khóa Bí Mật E2EE"):
    st.code(st.session_state.e2ee_key, language="text")

# 5. TIÊU ĐỀ ỨNG DỤNG
st.title("🔒 E2EE Cyber Chat")
st.caption("Độ dài chuỗi mã hóa tự động điều chỉnh linh hoạt theo tin nhắn.")
st.divider()

# 6. HIỂN THỊ DANH SÁCH TIN NHẮN
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(
        msg["sender_name"], avatar=msg.get("avatar", "👤")
    ):
        # HIỂN THỊ CHUỖI MÃ HÓA NGẮN/DÀI TƯƠNG ỨNG
        st.code(msg["cipher_text"], language="text")

        # NÚT BẤM GIẢI MÃ & DỊCH
        col1, col2 = st.columns([1.5, 3])
        with col1:
            if st.button(f"🔓 Giải mã & Dịch", key=f"btn_{idx}"):
                if not msg["decrypted_text"]:
                    # Bước 1: Giải mã
                    dec = decrypt_proportional(
                        msg["cipher_text"], st.session_state.e2ee_key
                    )
                    msg["decrypted_text"] = dec

                    # Bước 2: Dịch tự động
                    try:
                        translated = GoogleTranslator(
                            source="auto", target="vi"
                        ).translate(dec)
                        msg["translated_text"] = translated
                    except Exception:
                        msg["translated_text"] = dec

                msg["show_trans"] = not msg["show_trans"]
                st.rerun()

        # HIỂN THỊ KẾT QUẢ KHI NHẤN NÚT
        if msg.get("show_trans"):
            st.success(f"💬 **Nội dung gốc:** {msg['decrypted_text']}")
            if msg.get("translated_text"):
                st.info(f"🌐 **Bản dịch (Tiếng Việt):** {msg['translated_text']}")

# 7. Ô NHẬP TIN NHẮN MỚI
if user_input := st.chat_input("Nhập tin nhắn (Ví dụ: Hi hoặc Hello World)..."):
    # Mã hóa với độ dài tương ứng trực tiếp
    cipher_text = encrypt_proportional(
        user_input, st.session_state.e2ee_key
    )

    st.session_state.messages.append(
        {
            "sender_name": user_name,
            "avatar": user_avatar,
            "cipher_text": cipher_text,
            "decrypted_text": "",
            "translated_text": "",
            "show_trans": False,
        }
    )
    st.rerun()
