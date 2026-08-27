import base64
import hashlib
import re
from deep_translator import GoogleTranslator
from PIL import Image
import streamlit as st
from supabase import create_client

# 1. CẤU HÌNH GIAO DIỆN LIGHTWEIGHT FOR MOBILE
st.set_page_config(
    page_title="Anti KHANG KIÊN", page_icon="🔒", layout="centered"
)

st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #0f172a !important;
        background-color: #f1f5f9 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    div[data-testid="stChatInput"] {
        border: 1px solid #38bdf8 !important;
        border-radius: 12px !important;
    }
    .stTextInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
    .sender-name {
        color: #38bdf8;
        font-weight: bold;
        font-size: 1.05rem;
        margin-bottom: 4px;
    }
    .tag-inline {
        background-color: #0284c7;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 2. THUẬT TOÁN MÃ HÓA E2EE TỐI ƯU TỐC ĐỘ
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


# 3. KẾT NỐI SUPABASE CÓ CACHE (CHỐNG LAG MOBILE)
SUPABASE_URL = "https://mrsqzgghcijgujaerdxp.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yc3F6Z2doY2lqZ3VqYWVyZHhwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc4MzQwNjEsImV4cCI6MjEwMzQxMDA2MX0.UQ2s9VRtnPW9EqzPPW4Ywx3blCG3d1OeSM3WJ23CEmA".strip()


@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


supabase_client = init_supabase()

# 4. KHỞI TẠO BỘ NHỚ ĐỆM ĐỘC LẬP
if "e2ee_key" not in st.session_state:
    st.session_state.e2ee_key = "SecretKey_CyberVault_2026"

if "decrypted_cache" not in st.session_state:
    st.session_state.decrypted_cache = {}

if "expanded_msgs" not in st.session_state:
    st.session_state.expanded_msgs = set()

# 5. THANH SIDEBAR
st.sidebar.title("⚙️ Thẻ Định Danh")
user_name = st.sidebar.text_input("👤 Biệt danh của bạn:", value="User_Alpha")

avatar_type = st.sidebar.radio(
    "🎨 Kiểu Avatar:", ["Emoji / Bot có sẵn", "Tự tải ảnh lên"]
)
if avatar_type == "Emoji / Bot có sẵn":
    user_avatar = st.sidebar.selectbox(
        "🎭 Chọn biểu tượng:",
        ["🤖", "👾", "🧠", "🔮", "🥷", "🦊", "👑", "🔥", "🦄"],
        index=0,
    )
else:
    uploaded_avatar = st.sidebar.file_uploader(
        "📤 Chọn ảnh từ máy (PNG, JPG):", type=["png", "jpg", "jpeg"]
    )
    user_avatar = Image.open(uploaded_avatar) if uploaded_avatar else "🤖"

with st.sidebar.expander("🔑 Khóa Bí Mật E2EE"):
    st.code(st.session_state.e2ee_key, language="text")

st.sidebar.markdown("---")
st.sidebar.markdown("**👨‍💻 Tác giả:** N.Đ.K")

# 6. TIÊU ĐỀ ỨNG DỤNG
st.title("🔒 Anti KHANG KIÊN")
st.caption("Trò chuyện bảo mật E2EE — Đồng bộ Real-time PC & Mobile.")
st.divider()

# 7. KHU VỰC GỬI FILE MEDIA MÃ HÓA
with st.expander("📎 **Gửi Ảnh HD, Video hoặc Tệp đính kèm (Mã hóa E2EE)**"):
    file_upload = st.file_uploader(
        "Chọn file đính kèm (Ảnh HD, Video MP4, PDF...):", key="media_uploader"
    )
    if st.button("📤 Gửi File Mã Hóa", use_container_width=True):
        if file_upload is not None:
            file_bytes = file_upload.read()
            b64_file = base64.b64encode(file_bytes).decode("utf-8")
            cipher_file = encrypt_proportional(
                b64_file, st.session_state.e2ee_key
            )

            mime = file_upload.type
            media_kind = "file"
            if "image" in mime:
                media_kind = "image"
            elif "video" in mime:
                media_kind = "video"

            msg_data = {
                "sender_name": user_name,
                "avatar": (
                    user_avatar
                    if isinstance(user_avatar, str)
                    else "🤖"
                ),
                "cipher_text": f"🔒 [MEDIA {media_kind.upper()} ĐÃ MÃ HÓA E2EE: {file_upload.name}]",
                "raw_cipher_media": cipher_file,
                "media_kind": media_kind,
                "file_name": file_upload.name,
                "mime_type": mime,
                "tagged_user": "",
            }

            if supabase_client:
                try:
                    supabase_client.table("messages").insert(msg_data).execute()
                except Exception:
                    pass
            st.rerun()


# 8. KHU VỰC HIỂN THỊ TIN NHẮN TỰ ĐỘNG ĐỒNG BỘ (RUN EVERY 3S)
@st.fragment(run_every=3)
def render_chat_stream():
    messages = []
    if supabase_client:
        try:
            res = (
                supabase_client.table("messages")
                .select("*")
                .order("id", desc=False)
                .execute()
            )
            if res.data:
                messages = res.data
        except Exception:
            pass

    for msg in messages:
        msg_id = msg.get("id") or msg.get("cipher_text")
        sender = msg.get("sender_name", "Ẩn danh")
        avatar = msg.get("avatar", "🤖")

        with st.chat_message(sender, avatar=avatar):
            st.markdown(
                f'<div class="sender-name">👤 {sender}</div>',
                unsafe_allow_html=True,
            )
            st.code(msg["cipher_text"], language="text")

            is_media = (
                "raw_cipher_media" in msg
                and msg["raw_cipher_media"] is not None
            )
            btn_label = "🔓 Giải mã Media" if is_media else "🔓 Giải mã & Dịch"

            if st.button(btn_label, key=f"btn_{msg_id}"):
                if msg_id in st.session_state.expanded_msgs:
                    st.session_state.expanded_msgs.remove(msg_id)
                else:
                    st.session_state.expanded_msgs.add(msg_id)

                    if msg_id not in st.session_state.decrypted_cache:
                        if is_media:
                            dec_b64 = decrypt_proportional(
                                msg["raw_cipher_media"],
                                st.session_state.e2ee_key,
                            )
                            st.session_state.decrypted_cache[msg_id] = {
                                "media_data": base64.b64decode(
                                    dec_b64.encode("utf-8")
                                )
                            }
                        else:
                            dec = decrypt_proportional(
                                msg["cipher_text"], st.session_state.e2ee_key
                            )
                            try:
                                trans = GoogleTranslator(
                                    source="auto", target="vi"
                                ).translate(dec)
                            except Exception:
                                trans = dec
                            st.session_state.decrypted_cache[msg_id] = {
                                "decrypted_text": dec,
                                "translated_text": trans,
                            }
                st.rerun()

            if msg_id in st.session_state.expanded_msgs:
                cache = st.session_state.decrypted_cache.get(msg_id, {})
                if is_media:
                    st.success(f"📎 Tệp gốc: **{msg['file_name']}**")
                    media_bytes = cache.get("media_data")
                    if media_bytes:
                        if msg["media_kind"] == "image":
                            st.image(
                                media_bytes, caption="📷 Ảnh giải mã E2EE gốc"
                            )
                        elif msg["media_kind"] == "video":
                            st.video(media_bytes)
                        else:
                            st.download_button(
                                "📥 Tải File Giải Mã",
                                data=media_bytes,
                                file_name=msg["file_name"],
                                mime=msg["mime_type"],
                            )
                else:
                    raw_decrypted = cache.get("decrypted_text", "")
                    highlighted_text = re.sub(
                        r"(@\w+)",
                        r'<span class="tag-inline">\1</span>',
                        raw_decrypted,
                    )
                    st.markdown(
                        f"💬 **Nội dung gốc:** {highlighted_text}",
                        unsafe_allow_html=True,
                    )
                    st.info(
                        f"🌐 **Bản dịch (Tiếng Việt):** {cache.get('translated_text', '')}"
                    )


render_chat_stream()

# 9. Ô NHẬP TIN NHẮN
if user_input := st.chat_input("Nhập tin nhắn... (Ví dụ: @Khang chào bạn nhé!)"):
    tags_found = re.findall(r"@(\w+)", user_input)
    tagged_str = ", ".join(tags_found) if tags_found else ""

    cipher_text = encrypt_proportional(user_input, st.session_state.e2ee_key)

    msg_data = {
        "sender_name": user_name,
        "avatar": user_avatar if isinstance(user_avatar, str) else "🤖",
        "cipher_text": cipher_text,
        "tagged_user": tagged_str,
    }

    if supabase_client:
        try:
            supabase_client.table("messages").insert(msg_data).execute()
        except Exception:
            pass

    st.rerun()
