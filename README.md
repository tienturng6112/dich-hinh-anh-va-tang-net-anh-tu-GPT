# ỨNG DỤNG TỰ ĐỘNG DỊCH ẢNH VÀ LÀM NÉT QUA CHATGPT (AI IMAGE TRANSLATOR & ENHANCER)

Ứng dụng chuyên nghiệp giúp bạn:
1. **Mô phỏng lại, Làm nét & Dịch chữ trực tiếp lên hình ảnh qua AI ChatGPT**: Tự động tải ảnh lên ChatGPT, gửi câu lệnh yêu cầu vẽ lại ảnh sắc nét và dịch toàn bộ chữ trên ảnh sang tiếng Việt (hoặc ngôn ngữ tùy chọn), sau đó tự động tải ảnh tuyệt đẹp sinh ra từ ChatGPT lưu về máy tính.
2. **Làm nét cục bộ & Siêu phân giải (Super-Resolution 2x / 4x)**: Sử dụng các thuật toán đồ họa chuyên sâu (Lanczos, Unsharp Masking, CLAHE) giúp tăng cường chi tiết cho ảnh.
3. **Lưu phiên đăng nhập vĩnh viễn**: Profile Chrome được lưu trữ riêng biệt, bạn chỉ cần đăng nhập tài khoản ChatGPT 1 lần duy nhất, các lần sau ứng dụng sẽ tự động nhận diện tài khoản mà không cần đăng nhập lại.
4. **Xuất báo cáo tổng hợp ra 1 file kết quả**: Hỗ trợ xuất file báo cáo **Excel (.xlsx)**, **Báo cáo trực quan HTML (.html)** và **Tài liệu Word (.docx)** chứa toàn bộ đối chiếu ảnh gốc, ảnh AI sinh ra và nội dung dịch chi tiết.

---

## 🚀 HƯỚNG DẪN KHỞI CHẠY NHANH

### Cách 1: Chạy bằng file Run (Khuyên dùng)
- Click đúp vào file `run.bat` trong thư mục này.

### Cách 2: Chạy bằng lệnh dòng lệnh (Terminal / PowerShell)
```bash
python main.py
```

---

## 📖 HƯỚNG DẪN SỬ DỤNG TỪNG BƯỚC

### Bước 1: Mở Chrome và Đăng nhập ChatGPT
1. Trên giao diện ứng dụng, bấm nút **🌐 Mở Chrome Đăng Nhập GPT**.
2. Một cửa sổ Google Chrome sẽ xuất hiện và truy cập vào `https://chatgpt.com/`.
3. Bạn tiến hành đăng nhập tài khoản ChatGPT của mình.
4. Sau khi đăng nhập thành công, bạn quay lại ứng dụng và bấm nút **🔍 Kiểm Tra Đăng Nhập**. Khi thông báo hiển thị màu xanh lá: `Trạng thái: Đã đăng nhập ChatGPT thành công! ✅`, bạn đã sẵn sàng!
> 💡 *Lưu ý: Bạn chỉ cần thực hiện bước này trong lần đầu sử dụng. Những lần sau mở ứng dụng, Chrome sẽ tự động ghi nhớ tài khoản.*

### Bước 2: Nạp hình ảnh cần xử lý
- Bấm **📁 Chọn File Ảnh...** để chọn một hoặc nhiều ảnh cùng lúc (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`).
- Hoặc bấm **📂 Chọn Thư Mục...** để quét toàn bộ ảnh trong một thư mục bất kỳ.
- Bấm vào từng ảnh trong bảng danh sách bên trái để xem trước ảnh gốc ở khung bên phải.

### Bước 3: Cài đặt chế độ & Câu lệnh Prompt
- **Chế độ xử lý**:
  - `✨ Mô phỏng & Làm nét & Dịch trực tiếp lên ảnh qua GPT (Khuyên dùng)`: Tự động gửi lệnh tạo ảnh mới với chữ đã dịch tiếng Việt trên ảnh.
  - `📝 Chỉ nhận diện & Dịch văn bản trên ảnh (OCR Translation)`: Chỉ trích xuất chữ thành dạng text.
- **Ngôn ngữ dịch**: Mặc định là `Tiếng Việt`, có thể chọn `English`, `Tiếng Nhật`, `Tiếng Hàn`, `Tiếng Trung`, v.v.
- **Câu lệnh Prompt gửi ChatGPT**:
  - Mặc định: `mô phỏng lại hình ảnh và làm nét hình ảnh, dịch text trên hình sang tiếng việt`
  - Bạn có thể chỉnh sửa tự do câu lệnh này để thêm yêu cầu mong muốn (ví dụ: giữ nguyên phong cách, font chữ nghệ thuật, v.v.).

### Bước 4: Bắt đầu tiến trình
- Bấm nút to nổi bật **🚀 BẮT ĐẦU DỊCH & MÔ PHỎNG LÀM NÉT QUA GPT**.
- Ứng dụng sẽ tự động thực hiện:
  1. Tải ảnh lên ChatGPT.
  2. Gửi câu lệnh mô phỏng và dịch chữ.
  3. Chờ ChatGPT vẽ và hoàn thành ảnh mới.
  4. Tự động tải ảnh AI chất lượng cao về thư mục `output/anh_tao_tu_gpt/`.
  5. Hiển thị đối chiếu ảnh gốc và ảnh GPT tạo trực tiếp trên giao diện tab **So Sánh Trước & Sau**.

### Bước 5: Xem và mở file kết quả
- **✨ Xem Ảnh GPT (Kích Thước Gốc)**: Bấm trực tiếp trên giao diện để mở ảnh kết quả bằng trình xem ảnh mặc định của máy tính.
- **📊 Mở File Excel Kết Quả**: Xem bảng dữ liệu Excel tổng hợp.
- **🌐 Mở Báo Cáo HTML Trực Quan**: Xem trang giao diện đẹp mắt trên trình duyệt với hình ảnh so sánh cạnh nhau.
- **🎨 Thư Mục Ảnh GPT**: Mở trực tiếp thư mục chứa toàn bộ ảnh tuyệt đẹp do GPT tạo ra.

---

## 📂 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
├── core/
│   ├── chatgpt_bot.py       # Module tự động hóa Chrome ChatGPT bằng DrissionPage
│   ├── enhancer.py          # Module làm nét cục bộ (OpenCV & Pillow)
│   ├── exporter.py          # Module xuất báo cáo Excel, HTML, Word
│   └── __init__.py
├── gui/
│   ├── main_window.py       # Giao diện đồ họa PySide6 hiện đại
│   ├── styles.py            # Giao diện QSS phong cách phẳng hiện đại
│   └── __init__.py
├── chrome_profile/          # Thư mục lưu trữ cookies & phiên đăng nhập ChatGPT
├── output/
│   ├── anh_tao_tu_gpt/      # Thư mục chứa các ảnh AI đã mô phỏng, làm nét và dịch
│   ├── anh_da_lam_net/      # Thư mục chứa ảnh làm nét cục bộ
│   └── [Báo cáo Excel, HTML, Word]
├── main.py                  # File thực thi chính của ứng dụng
├── run.bat                  # File nhấp đúp chạy nhanh trên Windows
├── requirements.txt         # Danh sách thư viện phụ thuộc
└── README.md                # Tài liệu hướng dẫn sử dụng
```
