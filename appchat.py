from cryptography.fernet import Fernet
from deep_translator import GoogleTranslator
import streamlit as st

# Cấu hình giao diện
st.set_page_config(
    page_title="E2EE Secure Chat", page_icon="🔒", layout="centered"
)

# 1. KHỞI TẠO KHÓA E2EE BẢO MẬT & BỘ NHỚ
if "e2ee_key" not in st.session_state:
    # Trong thực tế, khóa này do 2 thiết bị tự thỏa thuận (Diffie-Hellman)
    st.session_state.e2ee_key = Fernet.generate_key()

if "messages" not in st.session_state:
    st.session_state.messages = []

cipher = Fernet(st.session_state.e2ee_key)

# 2. GIAO DIỆN CHAT
st.title("🔒 E2EE Chat & Translator")
st.caption(
    "Tin nhắn được mã hóa E2EE trên thiết bị. Chỉ dịch khi bạn bấm vào tin nhắn."
)

# Hiển thị khóa bí mật (Minh họa E2EE)
with st.expander("🔑 Xem Khóa Bí Mật E2EE (Client-Side Key)"):
    st.code(st.session_state.e2ee_key.decode(), language="text")

# 3. DANH SÁCH TIN NHẮN
st.divider()
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["sender"]):
        # Giải mã E2EE ngay tại thiết bị
        decrypted_text = cipher.decrypt(msg["payload"]).decode("utf-8")

        st.write(decrypted_text)

        # Hiện chi tiết chuỗi mã hóa bị mù trên Server
        with st.expander("📦 Xem mã hóa E2EE lưu trên Server"):
            st.code(msg["payload"].decode("utf-8")[:40] + "...", language="text")

        # NÚT BẤM ĐỂ DỊCH (Chỉ kích hoạt khi người dùng bấm)
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(f"🌐 Dịch", key=f"btn_{idx}"):
                if not msg["translated_text"]:
                    # Gọi API dịch tại chỗ
                    translated = GoogleTranslator(
                        source="auto", target="vi"
                    ).translate(decrypted_text)
                    msg["translated_text"] = translated
                msg["show_trans"] = not msg["show_trans"]
                st.rerun()

        # Hiển thị bản dịch nếu được bật
        if msg.get("show_trans") and msg.get("translated_text"):
            st.info(f"🔤 Bản dịch (Tiếng Việt): {msg['translated_text']}")

# 4. Ô NHẬP TIN NHẮN MỚI
if user_input := st.chat_input("Nhập tin nhắn (Ví dụ: Hello, how are you?)..."):
    # Bước A: Mã hóa E2EE văn bản trước khi "gửi lên server"
    encrypted_payload = cipher.encrypt(user_input.encode("utf-8"))

    # Bước B: Lưu gói dữ liệu mã hóa
    st.session_state.messages.append(
        {
            "sender": "user",
            "payload": encrypted_payload,
            "translated_text": "",
            "show_trans": False,
        }
    )
    st.rerun()