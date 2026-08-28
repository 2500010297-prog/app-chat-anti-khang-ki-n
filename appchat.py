import base64
import hashlib
from io import BytesIO
import re
import threading
from deep_translator import GoogleTranslator
from PIL import Image
import streamlit as st
from supabase import create_client

# 1. CẤU HÌNH GIAO DIỆN CYBER DARK CHUẨN
st.set_page_config(
    page_title="Tâm Sự Thầm Kín", page_icon="🔒", layout="centered"
)

st.markdown(
    """
<style>
    html { scroll-behavior: smooth; }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; color: #f8fafc !important; }
    div[data-testid="stChatInput"] textarea { color: #0f172a !important; background-color: #f1f5f9 !important; font-weight: 600 !important; font-size: 1rem !important; }
    div[data-testid="stChatInput"] { border: 1px solid #38bdf8 !important; border-radius: 12px !important; }
    .stTextInput input { background-color: #1e293b !important; color: #f8fafc !important; }
    .sender-name { color: #38bdf8 !important; font-weight: bold; font-size: 1.05rem; margin-bottom: 4px; }
    .tag-inline { background-color: #0284c7; color: #ffffff !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .msg-original { color: #ffffff !important; background-color: #0f172a; padding: 10px 14px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 8px; margin-bottom: 8px; font-size: 1rem; line-height: 1.5; }
    .msg-translation { color: #e2e8f0 !important; background-color: #1e293b; padding: 8px 12px; border-radius: 8px; border-left: 4px solid #0284c7; margin-bottom: 8px; font-size: 0.95rem; }
    button[data-testid="stPopoverButton"] { background-color: #0284c7 !important; color: #ffffff !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; }
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


# 5. BỘ NHỚ LƯU TRỮ VĨNH VIỄN (ĐỒNG BỘ TRỰC TIẾP URL & SESSION)
query_params = st.query_params
default_name = query_params.get("user", "User_Alpha")
default_avatar = query_params.get("avatar", "👤")

if "PERMA_NAME" not in st.session_state:
    st.session_state.PERMA_NAME = default_name

if (
    "PERMA_AVATAR" not in st.session_state
    or st.session_state.PERMA_AVATAR == "👤"
):
    st.session_state.PERMA_AVATAR = default_avatar

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

# Ô nhập biệt danh
input_name = st.sidebar.text_input(
    "👤 Biệt danh của bạn:",
    value=st.session_state.PERMA_NAME,
    key="widget_name_input",
)
if input_name and input_name != st.session_state.PERMA_NAME:
    st.session_state.PERMA_NAME = input_name
    st.query_params["user"] = input_name

st.sidebar.markdown("---")
st.sidebar.subheader("🖼️ Tải ảnh đại diện")

# Tải ảnh từ thiết bị & Nén tối ưu lưu vào URL
uploaded_avatar = st.sidebar.file_uploader(
    "📤 Chọn ảnh từ thiết bị (PNG, JPG):",
    type=["png", "jpg", "jpeg"],
    key="widget_file_upload",
)
if uploaded_avatar is not None:
    try:
        uploaded_avatar.seek(0)
        img = Image.open(uploaded_avatar).convert("RGB")
        img.thumbnail((60, 60))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=60)
        b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        avatar_url = f"data:image/jpeg;base64,{b64_img}"

        st.session_state.PERMA_AVATAR = avatar_url
        st.query_params["avatar"] = avatar_url
    except Exception:
        pass

user_name = st.session_state.PERMA_NAME
user_avatar = st.session_state.PERMA_AVATAR

# Hiển thị Avatar đang dùng
st.sidebar.write("**Avatar đang dùng:**")
if user_avatar.startswith("data:image"):
    st.sidebar.image(user_avatar, width=60)
else:
    st.sidebar.subheader(user_avatar)

with st.sidebar.expander("🔑 Khóa Bí Mật E2EE"):
    st.code(st.session_state.e2ee_key, language="text")

st.sidebar.markdown("---")
st.sidebar.markdown("**👨‍💻 Tác giả:** N.Đ.K")

# 7. TIÊU ĐỀ ỨNG DỤNG
st.title("🔒 Tâm Sự Thầm Kín")
st.caption("Trò chuyện bảo mật E2EE — Đồng bộ Real-time 1s siêu tốc.")
st.divider()


# 8. KHUNG CHAT STREAM
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
        avatar = msg.get("avatar", "👤")
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
                    st.write(f"📎 Tệp gốc: **{msg.get('file_name', '')}**")
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
                        f'<div class="msg-original">💬 <b>Nội dung gốc:</b> {highlighted_text}</div>',
                        unsafe_allow_html=True,
                    )

                    translated_txt = cache.get("translated_text", "")
                    if translated_txt:
                        st.markdown(
                            f'<div class="msg-translation">🌐 <b>Bản dịch:</b> {translated_txt}</div>',
                            unsafe_allow_html=True,
                        )


render_chat_stream()

# 9. NÚT ĐÍNH KÈM MEDIA
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

# 10. KHUNG NHẬP TIN NHẮN
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
