"""
Module tự động hóa tương tác với ChatGPT qua Google Chrome bằng DrissionPage.
Hỗ trợ tương thích toàn diện cả giao diện ChatGPT cổ điển và giao diện mới (ProseMirror, GPT-4o / GPT-6 UI):
- Tự động nhận diện trạng thái đăng nhập, menu tài khoản người dùng
- Tìm chính xác ô soạn thảo (ProseMirror / #prompt-textarea)
- Đính kèm ảnh chuẩn xác qua input[type=file] (accept="image/*")
- Tự động mở New Chat cho mỗi ảnh để tránh dồn file cũ
- Chờ trợ lý AI suy luận và hoàn thành câu trả lời (loại bỏ hoàn toàn việc bắt nhầm tin nhắn người dùng)
- Trích xuất chuẩn xác nội dung dịch thuật từ ChatGPT
"""

import os
import time
from typing import Optional, Callable, Dict, Any, List, Tuple
from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.common import Keys


def find_chrome_path() -> Optional[str]:
    """Tìm đường dẫn thực thi của Google Chrome trên máy Windows"""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


class ChatGPTAutomation:
    def __init__(self, profile_dir: Optional[str] = None, port: int = 9555):
        if profile_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.profile_dir = os.path.join(base_dir, "chrome_profile")
        else:
            self.profile_dir = profile_dir

        os.makedirs(self.profile_dir, exist_ok=True)
        self.port = port
        self.chrome_path = find_chrome_path()
        self.page: Optional[ChromiumPage] = None

    def get_options(self, headless: bool = False) -> ChromiumOptions:
        """Khởi tạo cấu hình Chrome với profile lưu trữ phiên đăng nhập"""
        co = ChromiumOptions()
        if self.chrome_path:
            co.set_browser_path(self.chrome_path)
        co.set_user_data_path(self.profile_dir)
        co.set_local_port(self.port)
        co.headless(headless)
        co.set_argument('--no-first-run')
        co.set_argument('--no-default-browser-check')
        co.set_argument('--start-maximized')
        co.set_argument('--disable-blink-features=AutomationControlled')
        return co

    def open_for_login(self, callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Mở cửa sổ Chrome bình thường với profile cố định để người dùng đăng nhập ChatGPT.
        """
        try:
            if callback:
                callback("Đang khởi động Chrome đăng nhập ChatGPT...")

            co = self.get_options(headless=False)
            self.page = ChromiumPage(co)
            
            # Điều hướng tới ChatGPT
            self.page.get("https://chatgpt.com/")
            
            if callback:
                callback("Chrome đã mở! Vui lòng đăng nhập tài khoản ChatGPT của bạn trên trình duyệt.")
            return True
        except Exception as e:
            if callback:
                callback(f"Lỗi khi mở Chrome: {str(e)}")
            return False

    def check_login_status(self) -> Tuple[bool, str]:
        """
        Kiểm tra chi tiết trạng thái đăng nhập trên trang ChatGPT.
        Trả về (is_logged_in: bool, user_info: str)
        """
        if not self.page:
            try:
                co = self.get_options(headless=False)
                self.page = ChromiumPage(co)
            except Exception:
                return False, "Chưa kết nối được với trình duyệt Chrome."

        try:
            # 1. Kiểm tra nút hồ sơ cá nhân (Profile Menu)
            profile_btn = (
                self.page.ele('xpath://button[contains(@aria-label, "profile") or contains(@aria-label, "Profile")]', timeout=2) or
                self.page.ele('xpath://button[contains(@aria-label, "Open profile menu")]', timeout=1) or
                self.page.ele('tag:button@aria-label*="profile"', timeout=1)
            )

            user_name = ""
            if profile_btn:
                user_name = profile_btn.text.strip()
                if not user_name:
                    user_name = "Tài khoản ChatGPT"
                return True, user_name

            # 2. Kiểm tra ô soạn thảo prompt (ProseMirror hoặc #prompt-textarea)
            editor = self._find_editor(timeout=2)
            login_btn = (
                self.page.ele('xpath://button[contains(text(), "Log in") or contains(text(), "Đăng nhập") or @data-testid="login-button"]', timeout=1)
            )

            if editor and not login_btn:
                return True, "Đã sẵn sàng"

            return False, "Chưa phát hiện tài khoản đăng nhập trên ChatGPT."
        except Exception as e:
            return False, f"Lỗi kiểm tra: {str(e)}"

    def is_logged_in(self) -> bool:
        """Hàm rút gọn trả về True nếu đã đăng nhập"""
        status, _ = self.check_login_status()
        return status

    def connect_or_start(self, callback: Optional[Callable[[str], None]] = None) -> ChromiumPage:
        """Kết nối tới Chrome hiện có hoặc khởi động phiên mới"""
        if self.page:
            try:
                _ = self.page.title
                return self.page
            except Exception:
                self.page = None

        if callback:
            callback("Đang kết nối tới trình duyệt Chrome...")

        co = self.get_options(headless=False)
        self.page = ChromiumPage(co)
        return self.page

    def _find_editor(self, timeout: float = 5):
        """Tìm ô soạn thảo tin nhắn của ChatGPT (hỗ trợ cả ProseMirror và textarea)"""
        if not self.page:
            return None
        return (
            self.page.ele('xpath://div[@contenteditable="true"]', timeout=timeout) or
            self.page.ele('tag:div@class*="ProseMirror"', timeout=timeout) or
            self.page.ele('#prompt-textarea', timeout=timeout) or
            self.page.ele('tag:textarea', timeout=timeout)
        )

    def _find_image_file_input(self, timeout: float = 3):
        """Tìm input upload file hình ảnh"""
        if not self.page:
            return None
        return (
            self.page.ele('xpath://input[@type="file" and contains(@accept, "image")]', timeout=timeout) or
            self.page.ele('tag:input@type=file', timeout=timeout)
        )

    def _extract_latest_response(self) -> str:
        """
        Trích xuất câu trả lời MỚI NHẤT của trợ lý ChatGPT.
        CHỈ lấy nội dung của trợ lý (bắt đầu bằng ChatGPT said: hoặc thẻ markdown),
        tuyệt đối KHÔNG lấy nội dung tin nhắn của người dùng (You said:).
        """
        if not self.page:
            return ""

        try:
            js_code = """
            return (() => {
                // 1. Tìm thẻ tiêu đề hoặc span có chữ "ChatGPT said:"
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, span'))
                                      .filter(el => el.innerText && el.innerText.trim() === 'ChatGPT said:');
                
                if (headings.length > 0) {
                    const lastHeading = headings[headings.length - 1];
                    let p = lastHeading.parentElement;
                    while (p && p.innerText.length < 25 && p.parentElement && p.parentElement.tagName !== 'BODY') {
                        p = p.parentElement;
                    }
                    let text = p ? p.innerText.trim() : '';
                    if (text.startsWith('ChatGPT said:')) {
                        text = text.replace('ChatGPT said:', '').trim();
                    }
                    if (text && !text.includes('You said:')) {
                        return text;
                    }
                }
                
                // 2. Dự phòng: Tìm qua các khối markdown của trợ lý
                const markdowns = Array.from(document.querySelectorAll('.markdown'));
                if (markdowns.length > 0) {
                    const lastMd = markdowns[markdowns.length - 1].innerText.trim();
                    if (lastMd && !lastMd.includes('You said:')) {
                        return lastMd;
                    }
                }
                
                return '';
            })();
            """
            result = self.page.run_js(js_code)
            return (result or "").strip()
        except Exception:
            return ""

    def process_single_image(
        self,
        image_path: str,
        target_lang: str = "Tiếng Việt",
        custom_instructions: str = "",
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Tự động tải 1 ảnh lên ChatGPT, gửi câu lệnh dịch thuật, chờ nhận kết quả và trích xuất bản dịch.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Không tìm thấy file ảnh: {image_path}")

        page = self.connect_or_start(log_callback)

        # 1. Mở đoạn chat mới (New Chat) để làm sạch khung nhập và file cũ
        if log_callback:
            log_callback("Đang tạo phiên chat mới trên ChatGPT...")

        try:
            page.get("https://chatgpt.com/")
            time.sleep(2.5)
        except Exception:
            pass

        # 2. Chờ ô soạn thảo sẵn sàng
        if log_callback:
            log_callback("Chờ giao diện soạn thảo sẵn sàng...")

        editor = self._find_editor(timeout=15)
        if not editor:
            raise RuntimeError("Không tìm thấy ô nhập tin nhắn trên ChatGPT. Hãy chắc chắn bạn đã đăng nhập!")

        # 3. Upload file ảnh vào ChatGPT
        filename = os.path.basename(image_path)
        if log_callback:
            log_callback(f"Đang đính kèm ảnh: {filename} ...")

        file_input = self._find_image_file_input(timeout=3)
        if not file_input:
            plus_btn = (
                page.ele('xpath://button[contains(@aria-label, "Add files") or contains(@aria-label, "Attach") or contains(@aria-label, "kẹp")]', timeout=2) or
                page.ele('tag:button@data-testid*="attach"', timeout=2)
            )
            if plus_btn:
                plus_btn.click()
                time.sleep(0.5)
            file_input = self._find_image_file_input(timeout=3)

        if file_input:
            file_input.input(os.path.abspath(image_path))
        else:
            raise RuntimeError("Không tìm thấy cổng đính kèm ảnh của ChatGPT.")

        # Chờ ảnh tải lên thành công (khoảng 3.5 giây để nạp xong thumbnail)
        if log_callback:
            log_callback("Đang tải ảnh lên ChatGPT...")
        time.sleep(3.5)

        # 4. Soạn prompt dịch thuật ngắn gọn, đúng trọng tâm
        default_prompt = (
            f"Nhận diện toàn bộ chữ/văn bản có trong hình ảnh này và dịch sang {target_lang} "
            f"(định dạng: [Chữ gốc] -> [Bản dịch {target_lang}]). "
            f"Chỉ trả về nội dung dịch văn bản, tuyệt đối không thêm bất kỳ phân tích, giải thích hay nội dung nào khác."
        )
        if custom_instructions:
            default_prompt += f" {custom_instructions}"

        if log_callback:
            log_callback(f"Đang nhập yêu cầu nhận diện và dịch sang {target_lang}...")

        editor = self._find_editor(timeout=5)
        if editor:
            editor.click()
            time.sleep(0.3)
            editor.input(default_prompt)
        time.sleep(1)

        # 5. Bấm nút gửi (Send)
        if log_callback:
            log_callback("Đang gửi yêu cầu tới ChatGPT...")

        send_btn = (
            page.ele('xpath://button[@aria-label="Send" or @data-testid="send-button" or contains(@aria-label, "Send") or contains(@aria-label, "Gửi")]', timeout=4)
        )
        if send_btn and not send_btn.attr("disabled"):
            send_btn.click()
        else:
            try:
                page.actions.click(editor).key_down(Keys.ENTER).key_up(Keys.ENTER)
            except Exception:
                editor.input('\n')

        # 6. Chờ ChatGPT tạo phản hồi (tính toán suy luận và trả lời)
        if log_callback:
            log_callback("ChatGPT đang đọc chữ trên ảnh và dịch thuật...")

        time.sleep(3)
        start_wait = time.time()
        max_wait = 180  # tối đa 3 phút
        last_text = ""
        stable_count = 0

        while time.time() - start_wait < max_wait:
            time.sleep(2)

            # Kiểm tra nút stop còn tồn tại không
            stop_btn = page.ele('xpath://button[@data-testid="stop-button" or contains(@aria-label, "Stop") or contains(@aria-label, "Dừng") or contains(@aria-label, "Cancel")]', timeout=0.5)

            # Lấy text phản hồi hiện tại của ChatGPT (không lấy text người dùng)
            current_text = self._extract_latest_response()

            if current_text and len(current_text) > 5:
                if current_text == last_text:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_text = current_text
                    if log_callback:
                        preview_short = current_text.replace('\n', ' ')[:50]
                        log_callback(f"  [Đang dịch]: {preview_short}...")

                # Hoàn tất nếu nút stop không còn và văn bản ổn định ít nhất 2 lần quét
                if not stop_btn and stable_count >= 2:
                    break

        if log_callback:
            log_callback("Đã nhận xong toàn bộ nội dung dịch từ ChatGPT!")

        final_text = last_text or self._extract_latest_response()
        if not final_text:
            final_text = "Không nhận diện được chữ trong ảnh."

        return {
            "success": True,
            "text": final_text,
            "generated_images": []
        }

    def close(self):
        """Đóng kết nối trình duyệt"""
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None
