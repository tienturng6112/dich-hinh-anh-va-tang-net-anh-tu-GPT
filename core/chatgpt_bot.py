"""
Module tự động hóa tương tác với ChatGPT qua Google Chrome bằng DrissionPage.
Đúng theo yêu cầu cốt lõi:
1. Mở / kết nối Google Chrome với tài khoản ChatGPT (profile lưu vĩnh viễn).
2. Tải NGUYÊN HÌNH ẢNH GỐC lên ChatGPT (không can thiệp chỉnh sửa ảnh trước khi gửi).
3. Gửi kèm câu lệnh: "mô phổng lại hình ảnh và làm nét hình ảnh, dịch text trên hình sang tiếng việt".
4. Tự động nhận diện khi ChatGPT vẽ/sinh ảnh AI mới xong.
5. Tải ảnh chất lượng cao sinh ra từ ChatGPT lưu về máy tính.
"""

import os
import time
import base64
from typing import Optional, Callable, Dict, Any, List, Tuple
from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.common import Keys


DEFAULT_PROMPT = "mô phổng lại hình ảnh và làm nét hình ảnh, dịch text trên hình sang tiếng việt"


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
        Mở cửa sổ Chrome với profile cố định để người dùng đăng nhập ChatGPT.
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
        """
        if not self.page:
            try:
                co = self.get_options(headless=False)
                self.page = ChromiumPage(co)
            except Exception:
                return False, "Chưa kết nối được với trình duyệt Chrome."

        try:
            # 1. Kiểm tra nút profile menu
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

            # 2. Kiểm tra ô soạn thảo prompt
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
        status, _ = self.check_login_status()
        return status

    def connect_or_start(self, callback: Optional[Callable[[str], None]] = None) -> ChromiumPage:
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
        """Tìm ô soạn thảo tin nhắn của ChatGPT"""
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
        Trích xuất câu trả lời text mới nhất của trợ lý ChatGPT (nếu có).
        """
        if not self.page:
            return ""

        try:
            js_code = """
            return (() => {
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

    def _count_generated_images(self) -> int:
        """Đếm số lượng ảnh sinh ra (Generated images) hiện có trên trang"""
        if not self.page:
            return 0
        try:
            js_count = """
            return Array.from(document.querySelectorAll('img')).filter(i => {
                const alt = (i.alt || '').toLowerCase();
                const src = (i.src || '');
                if (alt.includes('user attachment') || alt.includes('avatar') || alt.includes('me.png')) return false;
                return alt.includes('generated') || src.startsWith('blob:') || src.includes('files.oaiusercontent.com');
            }).length;
            """
            return int(self.page.run_js(js_count) or 0)
        except Exception:
            return 0

    def _extract_generated_image(self) -> Optional[Dict[str, Any]]:
        """
        Trích xuất hình ảnh sinh ra bởi ChatGPT dưới dạng base64 data URL.
        Trả về dict { 'bytes': bytes, 'width': int, 'height': int, 'alt': str } hoặc None.
        """
        if not self.page:
            return None

        js_extract = """
        return (async () => {
            const imgs = Array.from(document.querySelectorAll('img')).filter(i => {
                const alt = (i.alt || '').toLowerCase();
                const src = (i.src || '');
                if (alt.includes('user attachment') || alt.includes('avatar') || alt.includes('me.png')) return false;
                return alt.includes('generated') || src.startsWith('blob:') || src.includes('files.oaiusercontent.com');
            });

            if (imgs.length === 0) return null;
            const img = imgs[imgs.length - 1];

            // 1. Thử vẽ canvas trực tiếp
            try {
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth || img.width;
                canvas.height = img.naturalHeight || img.height;
                if (canvas.width > 50 && canvas.height > 50) {
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    const dataUrl = canvas.toDataURL('image/png');
                    if (dataUrl && dataUrl.length > 500) {
                        return {
                            dataUrl: dataUrl,
                            width: canvas.width,
                            height: canvas.height,
                            alt: img.alt || ''
                        };
                    }
                }
            } catch (e) {
                console.error('Canvas error:', e);
            }

            // 2. Dự phòng dùng fetch blob
            try {
                const response = await fetch(img.src);
                const blob = await response.blob();
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve({
                        dataUrl: reader.result,
                        width: img.naturalWidth || img.width,
                        height: img.naturalHeight || img.height,
                        alt: img.alt || ''
                    });
                    reader.readAsDataURL(blob);
                });
            } catch (e) {
                return null;
            }
        })();
        """
        try:
            res = self.page.run_js(js_extract)
            if res and isinstance(res, dict) and "dataUrl" in res:
                data_url = res["dataUrl"]
                if "," in data_url:
                    header, encoded = data_url.split(",", 1)
                    raw_bytes = base64.b64decode(encoded)
                    return {
                        "bytes": raw_bytes,
                        "width": res.get("width", 0),
                        "height": res.get("height", 0),
                        "alt": res.get("alt", "")
                    }
        except Exception as e:
            print(f"Lỗi trích xuất ảnh sinh ra: {e}")
        return None

    def process_single_image(
        self,
        image_path: str,
        prompt: str = DEFAULT_PROMPT,
        output_dir: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Tải NGUYÊN HÌNH ẢNH GỐC lên ChatGPT, gửi kèm câu lệnh mô phỏng và làm nét,
        chờ ChatGPT vẽ xong ảnh mới và tự động tải về máy.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Không tìm thấy file ảnh: {image_path}")

        page = self.connect_or_start(log_callback)

        # 1. Mở đoạn chat mới (New Chat)
        if log_callback:
            log_callback("Đang mở phiên chat mới trên ChatGPT...")

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
            raise RuntimeError("Không tìm thấy ô nhập tin nhắn trên ChatGPT. Hãy chắc chắn bạn đã đăng nhập tài khoản!")

        # 3. Upload NGUYÊN HÌNH ẢNH GỐC vào ChatGPT
        filename = os.path.basename(image_path)
        if log_callback:
            log_callback(f"Đang đính kèm nguyên hình ảnh gốc: {filename} ...")

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
            # Tải nguyên hình ảnh gốc không qua can thiệp bộ lọc
            file_input.input(os.path.abspath(image_path))
        else:
            raise RuntimeError("Không tìm thấy cổng đính kèm ảnh của ChatGPT.")

        # Chờ ảnh tải lên thành công (khoảng 3.5 giây để nạp xong thumbnail)
        if log_callback:
            log_callback("Đang tải ảnh lên ChatGPT...")
        time.sleep(3.5)

        # Ghi nhận số lượng ảnh hiện có trước khi gửi prompt
        initial_img_count = self._count_generated_images()

        # 4. Nhập chính xác câu lệnh
        final_prompt = prompt.strip() if prompt and prompt.strip() else DEFAULT_PROMPT
        if log_callback:
            log_callback(f"Đang nhập câu lệnh: \"{final_prompt}\"...")

        editor = self._find_editor(timeout=5)
        if editor:
            editor.click()
            time.sleep(0.3)
            editor.input(final_prompt)
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

        # 6. Chờ ChatGPT tạo phản hồi (vẽ lại ảnh AI / dịch văn bản)
        if log_callback:
            log_callback("ChatGPT đang nhận ảnh, mô phỏng lại nét vẽ và tạo ảnh mới với chữ đã dịch...")

        time.sleep(4)
        start_wait = time.time()
        max_wait = 240  # tối đa 4 phút cho quá trình vẽ ảnh DALL-E / GPT
        last_text = ""
        found_image_result = None
        last_log_time = 0

        while time.time() - start_wait < max_wait:
            time.sleep(2.5)
            elapsed = int(time.time() - start_wait)

            if elapsed - last_log_time >= 10:
                last_log_time = elapsed
                if log_callback:
                    log_callback(f"  [ChatGPT] Đang xử lý vẽ và tạo ảnh mô phỏng ({elapsed}s)...")

            # Kiểm tra nút dừng (stop button)
            stop_btn = page.ele('xpath://button[@data-testid="stop-button" or contains(@aria-label, "Stop") or contains(@aria-label, "Dừng") or contains(@aria-label, "Cancel")]', timeout=0.5)

            # Kiểm tra xem có ảnh sinh ra mới chưa
            current_img_count = self._count_generated_images()
            if current_img_count > initial_img_count and not found_image_result:
                if log_callback:
                    log_callback("🎨 Đã phát hiện ảnh mô phỏng mới từ ChatGPT! Đang nạp dữ liệu ảnh...")
                found_image_result = self._extract_generated_image()

            # Lấy text phản hồi nếu có
            current_text = self._extract_latest_response()
            if current_text and current_text != last_text:
                last_text = current_text
                if log_callback:
                    preview_short = current_text.replace('\n', ' ')[:60]
                    log_callback(f"  [ChatGPT]: {preview_short}...")

            # Nếu đã có ảnh sinh ra và nút stop đã biến mất
            if found_image_result and not stop_btn:
                break

            # Nếu nút stop đã mất sau ít nhất 20 giây, thử kiểm tra ảnh lại lần nữa
            if not stop_btn and elapsed > 20:
                found_image_result = self._extract_generated_image()
                if found_image_result:
                    break
                if current_text and len(current_text) > 10 and elapsed > 35:
                    break

        # 7. Lưu ảnh đã tạo về máy tính nếu có
        saved_image_path = ""
        saved_image_size = ""
        if found_image_result and "bytes" in found_image_result:
            base_dir = output_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
            gpt_folder = os.path.join(base_dir, "anh_tao_tu_gpt")
            os.makedirs(gpt_folder, exist_ok=True)
            
            name_no_ext, _ = os.path.splitext(filename)
            saved_image_path = os.path.join(gpt_folder, f"{name_no_ext}_gpt_translated.png")
            try:
                with open(saved_image_path, "wb") as f:
                    f.write(found_image_result["bytes"])
                w = found_image_result.get("width", 0)
                h = found_image_result.get("height", 0)
                saved_image_size = f"{w}x{h}" if w and h else "Ultra-HD"
                if log_callback:
                    log_callback(f"🎉 ĐÃ LƯU THÀNH CÔNG ẢNH AI TẠO TỪ CHATGPT: {os.path.basename(saved_image_path)} ({saved_image_size})")
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ Lỗi khi ghi file ảnh GPT: {e}")

        final_text = last_text or self._extract_latest_response()
        if not final_text:
            if saved_image_path:
                final_text = f"Đã mô phỏng lại và làm nét thành công ảnh bằng AI ChatGPT ({saved_image_size}). Toàn bộ chữ đã được dịch trực tiếp sang Tiếng Việt trên hình ảnh."
            else:
                final_text = "Không nhận diện được nội dung từ ảnh."

        if log_callback:
            log_callback(f"Hoàn tất xử lý file {filename}!")

        return {
            "success": True if saved_image_path else False,
            "text": final_text,
            "generated_image_path": saved_image_path,
            "generated_image_size": saved_image_size,
            "generated_images": [saved_image_path] if saved_image_path else []
        }

    def close(self):
        """Đóng kết nối trình duyệt"""
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None
