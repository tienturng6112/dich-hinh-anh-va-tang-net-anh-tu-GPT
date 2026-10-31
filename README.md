# ỨNG DỤNG TỰ ĐỘNG DỊCH ẢNH VÀ LÀM NÉT QUA CHATGPT (AI IMAGE TRANSLATOR & ENHANCER)

Ứng dụng chuyên nghiệp giúp bạn:
1. **Làm nét & Nâng cấp độ phân giải hình ảnh (Super-Resolution 2x / 4x)**: Sử dụng các thuật toán đồ họa và xử lý ảnh chuyên sâu (Lanczos, Unsharp Masking, CLAHE, Bilateral Filter) giúp khôi phục chi tiết mờ, tăng độ sắc cạnh và làm nổi bật văn bản trong ảnh.
2. **Tự động hóa Chrome tương tác với ChatGPT**: Tự động mở trình duyệt, đính kèm từng ảnh lên ChatGPT, gửi câu lệnh dịch thuật ngữ cảnh và phân tích hình ảnh theo thời gian thực.
3. **Lưu phiên đăng nhập vĩnh viễn**: Profile Chrome được lưu trữ riêng biệt, bạn chỉ cần đăng nhập tài khoản ChatGPT (Plus hoặc Free) 1 lần duy nhất, các lần sau ứng dụng sẽ tự động nhận diện tài khoản mà không cần đăng nhập lại.
4. **Xuất báo cáo tổng hợp ra 1 file kết quả**: Hỗ trợ xuất file báo cáo **Excel (.xlsx)**, **Báo cáo trực quan HTML (.html)** và **Tài liệu Word (.docx)** chứa toàn bộ đối chiếu ảnh trước/sau và nội dung dịch chi tiết.

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
3. Bạn tiến hành đăng nhập tài khoản ChatGPT của mình (bằng Google, Email, Apple, v.v.).
4. Sau khi đăng nhập thành công, bạn quay lại ứng dụng và bấm nút **🔍 Kiểm Tra Đăng Nhập**. Khi thông báo hiển thị màu xanh lá: `Trạng thái: Đã đăng nhập ChatGPT thành công! ✅`, bạn đã sẵn sàng!
> 💡 *Lưu ý: Bạn chỉ cần thực hiện bước này trong lần đầu sử dụng. Những lần sau mở ứng dụng, Chrome sẽ tự động ghi nhớ tài khoản.*

### Bước 2: Nạp hình ảnh cần xử lý
- Bấm **📁 Chọn File Ảnh...** để chọn một hoặc nhiều ảnh cùng lúc (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`).
- Hoặc bấm **📂 Chọn Thư Mục...** để quét toàn bộ ảnh trong một thư mục bất kỳ.
- Bạn cũng có thể bấm vào từng ảnh trong bảng danh sách bên trái để xem trước ảnh gốc ở khung bên phải.

### Bước 3: Cài đặt chế độ dịch & làm nét
- **Ngôn ngữ dịch**: Mặc định là `Tiếng Việt`, bạn có thể chọn sang `English`, `Tiếng Nhật`, `Tiếng Hàn`, `Tiếng Trung`, v.v.
- **Chế độ làm nét**:
  - `Siêu nét 2x (Cân bằng & Sắc sảo)`: Tăng gấp đôi độ phân giải, giữ nguyên nét tự nhiên.
  - `Siêu nét 4x (Ultra HD)`: Nâng cấp cực đại độ phân giải cho các ảnh nhỏ hoặc mờ nhiều.
  - `Tối ưu tương phản & văn bản`: Tăng độ tương phản viền chữ, phù hợp với truyện tranh, tài liệu scan, bìa sách.
- **Định dạng file xuất kết quả**: Tích chọn `Excel (.xlsx)`, `HTML (.html)` và `Word (.docx)`.

### Bước 4: Bắt đầu tiến trình
- Bấm nút to nổi bật **🚀 BẮT ĐẦU DỊCH & LÀM NÉT HÀNG LOẠT**.
- Ứng dụng sẽ tự động thực hiện tuần tự:
  1. Nâng cấp và làm nét hình ảnh (lưu vào thư mục `output/anh_da_lam_net/`).
  2. Mở kết nối Chrome ChatGPT, đính kèm ảnh và gửi yêu cầu dịch toàn bộ chữ sang ngôn ngữ đích.
  3. Lấy nội dung bản dịch từ GPT hiển thị trực tiếp lên tab **Bản Dịch & Phân Tích (GPT)**.
  4. Hiển thị đối chiếu ảnh gốc và ảnh đã làm nét trên tab **So Sánh Trước & Sau**.
  5. Cập nhật thanh tiến trình % theo thời gian thực.

### Bước 5: Xem và mở file kết quả
Khi tiến trình hoàn thành, ứng dụng sẽ tự động xuất báo cáo tổng hợp. Bạn chỉ cần bấm:
- **📊 Mở File Excel Kết Quả**: Xem bảng dữ liệu Excel gồm tên file, kích thước trước/sau, nội dung dịch đầy đủ và đường dẫn ảnh.
- **🌐 Mở Báo Cáo HTML Trực Quan**: Xem trang giao diện đẹp mắt trên trình duyệt với hình ảnh so sánh cạnh nhau và bản dịch.
- **📂 Mở Thư Mục Kết Quả**: Mở thư mục chứa toàn bộ ảnh đã làm nét và các file báo cáo.

---

## 📂 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
├── core/
│   ├── chatgpt_bot.py       # Module tự động hóa Chrome ChatGPT bằng DrissionPage
│   ├── enhancer.py          # Module làm nét & siêu phân giải ảnh (OpenCV & Pillow)
│   ├── exporter.py          # Module xuất báo cáo Excel, HTML, Word
│   └── __init__.py
├── gui/
│   ├── main_window.py       # Giao diện đồ họa PySide6 hiện đại
│   ├── styles.py            # Giao diện QSS phong cách phẳng hiện đại
│   └── __init__.py
├── chrome_profile/          # Thư mục lưu trữ cookies & phiên đăng nhập ChatGPT
├── output/                  # Thư mục chứa ảnh đã làm nét và các file báo cáo xuất ra
├── main.py                  # File thực thi chính của ứng dụng
├── run.bat                  # File nhấp đúp chạy nhanh trên Windows
└── README.md                # Tài liệu hướng dẫn sử dụng
```

