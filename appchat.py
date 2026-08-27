import base64
import hashlib
from io import BytesIO
import re
import threading
from deep_translator import GoogleTranslator
from PIL import Image
import streamlit as st
from supabase import create_client

# 1. CẤU HÌNH GIAO DIỆN CYBER DARK
st.set_page_config(
    page_title="Anti KHANG KIÊN", page_icon="🔒", layout="centered"
)

st.markdown(
    """
<style>
    html {
        scroll-behavior: smooth;
    }
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
    div[data-testid="stAlert"] {
        background-color: #1e293b !important;
        border: 1px solid #38bdf8 !important;
    }
    div[data-testid="stAlert"] p, div[data-testid="stAlert"] span, div[data-testid="stAlert"] div {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    button[data-testid="stPopoverButton"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 2. CACHE DỊCH THUẬT SIÊU TỐC
@st.cache_data(show_spinner=False)
def fast_translate(text: str) -> str:
    if not text.strip():
        return ""
    try:
        return GoogleTranslator(source="auto", target="vi").translate(text)
    except Exception:
        return text


# 3. THUẬT TOÁN MÃ HÓA E2EE
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


# 4. KẾT NỐI SUPABASE
SUPABASE_URL = "https://mrsqzgghcijgujaerdxp.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yc3F6Z2doY2lqZ3VqYWVyZHhwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc4MzQwNjEsImV4cCI6MjEwMzQxMDA2MX0.UQ2s9VRtnPW9EqzPPW4Ywx3blCG3d1OeSM3WJ23CEmA".strip()


@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


supabase_client = init_supabase()


def async_send_to_supabase(data):
    if supabase_client:
        try:
            supabase_client.table("messages").insert(data).execute()
        except Exception:
            pass


# 5. KHỞI TẠO BỘ NHỚ TẠM
if "e2ee_key" not in st.session_state:
    st.session_state.e2ee_key = "SecretKey_CyberVault_2026"

if "decrypted_cache" not in st.session_state:
    st.session_state.decrypted_cache = {}

if "expanded_msgs" not in st.session_state:
    st.session_state.expanded_msgs = set()

if "optimistic_msgs" not in st.session_state:
    st.session_state.optimistic_msgs = []

# 6. SIDEBAR - THẺ ĐỊNH DẠNH
st.sidebar.title("⚙️ Thẻ Định Danh")
user_name = st.sidebar.text_input("👤 Biệt danh của bạn:", value="User_Alpha")

avatar_type = st.sidebar.radio(
    "🎨 Kiểu Avatar:", ["Emoji có sẵn", "Tải ảnh từ thiết bị"]
)

if avatar_type == "Emoji có sẵn":
    user_avatar = st.sidebar.selectbox(
        "🎭 Chọn biểu tượng:",
        [
            "🤖",
            "👾",
            "🧠",
            "🔮",
            "🥷",
            "🦊",
            "👑",
            "🔥",
            "🦄",
            "🐱",
            "🐶",
            "🐼",
            "🦁",
            "🚀",
            "🛡️",
            "😎",
        ],
        index=0,
    )
else:
    uploaded_avatar = st.sidebar.file_uploader(
        "📤 Chọn ảnh (PNG, JPG):", type=["png", "jpg", "jpeg"]
    )
    if uploaded_avatar:
        try:
            img = Image.open(uploaded_avatar)
            img.thumbnail((60, 60))
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=60)
            b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
            user_avatar = f"data:image/jpeg;base64,{b64_img}"
            st.sidebar.image(img, caption="Avatar đã tối ưu", width=60)
        except Exception:
            user_avatar = "🤖"
    else:
        user_avatar = "🤖"

with st.sidebar.expander("🔑 Khóa Bí Mật E2EE"):
    st.code(st.session_state.e2ee_key, language="text")

st.sidebar.markdown("---")
st.sidebar.markdown("**👨‍💻 Tác giả:** N.Đ.K")

# 7. TIÊU ĐỀ
st.title("🔒 Anti KHANG KIÊN")
st.caption("Trò chuyện bảo mật E2EE — Đồng bộ Real-time 1s siêu tốc.")
st.divider()


# 8. DÒNG PHẢN HỒI TIN NHẮN (ĐỒNG BỘ 1S)
@st.fragment(run_every=1)
def render_chat_stream():
    db_messages = []
    if supabase_client:
        try:
            res = (
                supabase_client.table("messages")
                .select(
                    "id, sender_name, avatar, cipher_text, media_kind, file_name, mime_type, tagged_user"
                )
                .order("id", desc=True)
                .limit(30)
                .execute()
            )
            if res.data:
                db_messages = list(reversed(res.data))
        except Exception:
            pass

    db_ciphers = {m.get("cipher_text") for m in db_messages}
    st.session_state.optimistic_msgs = [
        m
        for m in st.session_state.optimistic_msgs
        if m.get("cipher_text") not in db_ciphers
    ]

    all_messages = db_messages + st.session_state.optimistic_msgs

    for msg in all_messages:
        msg_id = msg.get("id") or msg.get("cipher_text")
        sender = msg.get("sender_name", "Ẩn danh")
        avatar = msg.get("avatar", "🤖")
        media_k = msg.get("media_kind")

        with st.chat_message(sender, avatar=avatar):
            st.markdown(
                f'<div class="sender-name">👤 {sender}</div>',
                unsafe_allow_html=True,
            )
            st.code(msg["cipher_text"], language="text")

            is_media = bool(media_k)
            btn_label = "🔓 Giải mã Media" if is_media else "🔓 Giải mã & Dịch"

            if st.button(btn_label, key=f"btn_{msg_id}"):
                if msg_id in st.session_state.expanded_msgs:
                    st.session_state.expanded_msgs.remove(msg_id)
                else:
                    st.session_state.expanded_msgs.add(msg_id)

                    if msg_id not in st.session_state.decrypted_cache:
                        if is_media:
                            raw_media = msg.get("raw_cipher_media")
                            if not raw_media and msg.get("id"):
                                try:
                                    media_res = (
                                        supabase_client.table("messages")
                                        .select("raw_cipher_media")
                                        .eq("id", msg.get("id"))
                                        .single()
                                        .execute()
                                    )
                                    raw_media = media_res.data.get(
                                        "raw_cipher_media", ""
                                    )
                                except Exception:
                                    raw_media = ""

                            if raw_media:
                                dec_b64 = decrypt_proportional(
                                    raw_media, st.session_state.e2ee_key
                                )
                                try:
                                    st.session_state.decrypted_cache[msg_id] = {
                                        "media_data": base64.b64decode(
                                            dec_b64.encode("utf-8")
                                        )
                                    }
                                except Exception:
                                    pass
                        else:
                            dec = decrypt_proportional(
                                msg["cipher_text"], st.session_state.e2ee_key
                            )
                            trans = fast_translate(dec)
                            st.session_state.decrypted_cache[msg_id] = {
                                "decrypted_text": dec,
                                "translated_text": trans,
                            }

            if msg_id in st.session_state.expanded_msgs:
                cache = st.session_state.decrypted_cache.get(msg_id, {})
                if is_media:
                    st.success(f"📎 Tệp gốc: **{msg.get('file_name', '')}**")
                    media_bytes = cache.get("media_data")
                    if media_bytes:
                        if media_k == "image":
                            st.image(
                                media_bytes, caption="📷 Ảnh giải mã E2EE gốc"
                            )
                        elif media_k == "video":
                            st.video(media_bytes)
                        else:
                            st.download_button(
                                "📥 Tải File Giải Mã",
                                data=media_bytes,
                                file_name=msg.get("file_name", "file"),
                                mime=msg.get(
                                    "mime_type", "application/octet-stream"
                                ),
                            )
                    else:
                        st.error("❌ Không thể nạp dữ liệu tệp đính kèm.")
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

# 9. NÚT ĐÍNH KÈM MEDIA DẠNG POPOVER ĐẶT NGAY TRÊN KHUNG CHAT
with st.popover(
    "📎 **Gửi Ảnh, Video hoặc File (Mã hóa E2EE)**", use_container_width=True
):
    file_upload = st.file_uploader(
        "Chọn file từ thiết bị:", key="media_uploader_popover"
    )
    if st.button("📤 Tải Lên & Gửi Ngay", use_container_width=True):
        if file_upload is not None:
            mime = file_upload.type
            media_kind = "file"
            if "image" in mime:
                media_kind = "image"
            elif "video" in mime:
                media_kind = "video"

            file_bytes = file_upload.read()

            if media_kind == "image":
                try:
                    img = Image.open(BytesIO(file_bytes))
                    img.thumbnail((1280, 1280))
                    buf = BytesIO()
                    img.save(buf, format="JPEG", quality=75)
                    file_bytes = buf.getvalue()
                    mime = "image/jpeg"
                except Exception:
                    pass

            if len(file_bytes) > 3 * 1024 * 1024:
                st.error("❌ Dung lượng file quá 3MB!")
            else:
                b64_file = base64.b64encode(file_bytes).decode("utf-8")
                cipher_file = encrypt_proportional(
                    b64_file, st.session_state.e2ee_key
                )

                msg_data = {
                    "sender_name": user_name,
                    "avatar": user_avatar,
                    "cipher_text": f"🔒 [MEDIA {media_kind.upper()} ĐÃ MÃ HÓA E2EE: {file_upload.name}]",
                    "raw_cipher_media": cipher_file,
                    "media_kind": media_kind,
                    "file_name": file_upload.name,
                    "mime_type": mime,
                    "tagged_user": "",
                }

                if supabase_client:
                    try:
                        supabase_client.table("messages").insert(
                            msg_data
                        ).execute()
                        st.success("✅ Gửi Media thành công!")
                    except Exception:
                        st.error("❌ Lỗi kết nối Cloud.")

                st.rerun()

# 10. KHUNG NHẬP TIN NHẮN CHÍNH
if user_input := st.chat_input("Nhập tin nhắn... (Ví dụ: @Khang chào bạn nhé!)"):
    tags_found = re.findall(r"@(\w+)", user_input)
    tagged_str = ", ".join(tags_found) if tags_found else ""

    cipher_text = encrypt_proportional(user_input, st.session_state.e2ee_key)

    msg_data = {
        "sender_name": user_name,
        "avatar": user_avatar,
        "cipher_text": cipher_text,
        "tagged_user": tagged_str,
    }

    st.session_state.optimistic_msgs.append(msg_data)

    threading.Thread(
        target=async_send_to_supabase, args=(msg_data,), daemon=True
    ).start()

    st.rerun()
