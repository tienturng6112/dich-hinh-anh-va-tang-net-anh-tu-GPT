"""
Giao diện người dùng chính (Main Window) PySide6.
Đúng theo yêu cầu tinh gọn:
- Bật Chrome ChatGPT lưu phiên đăng nhập riêng biệt.
- Tải NGUYÊN HÌNH ẢNH GỐC lên ChatGPT (không can thiệp bộ lọc làm méo ảnh).
- Gửi kèm câu lệnh: "mô phổng lại hình ảnh và làm nét hình ảnh, dịch text trên hình sang tiếng việt".
- Tự động phát hiện khi ảnh mới sinh ra và tải về máy.
- Hiển thị đối chiếu Ảnh Gốc vs Ảnh GPT Tạo Mới.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QProgressBar, QTextEdit, QCheckBox, QGroupBox, QSplitter,
    QMessageBox, QHeaderView, QAbstractItemView, QTabWidget, QLineEdit
)
from PySide6.QtGui import QPixmap, QColor

from core.chatgpt_bot import ChatGPTAutomation, DEFAULT_PROMPT
from core.exporter import ResultExporter
from gui.styles import MODERN_STYLE
from PIL import Image


class BatchProcessingWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int, int)  # current, total
    item_finished_signal = Signal(int, dict)  # index, result_dict
    all_finished_signal = Signal(list, dict)  # all_results, exported_files
    error_signal = Signal(str)

    def __init__(
        self,
        image_paths: List[str],
        prompt: str,
        export_options: Dict[str, bool],
        output_dir: str
    ):
        super().__init__()
        self.image_paths = image_paths
        self.prompt = prompt
        self.export_options = export_options
        self.output_dir = output_dir
        self.is_running = True
        self.bot = ChatGPTAutomation()

    def stop(self):
        self.is_running = False

    def run(self):
        total = len(self.image_paths)
        if total == 0:
            self.error_signal.emit("Không có hình ảnh nào trong danh sách để xử lý.")
            return

        gpt_folder = os.path.join(self.output_dir, "anh_tao_tu_gpt")
        os.makedirs(gpt_folder, exist_ok=True)

        all_results = []
        self.log_signal.emit(f"🚀 Bắt đầu gửi {total} ảnh lên ChatGPT để mô phỏng lại và làm nét...")

        for idx, img_path in enumerate(self.image_paths):
            if not self.is_running:
                self.log_signal.emit("⚠️ Tiến trình đã bị dừng bởi người dùng.")
                break

            filename = os.path.basename(img_path)
            self.log_signal.emit(f"\n==========================================")
            self.log_signal.emit(f"[{idx + 1}/{total}] Đang xử lý ảnh: {filename}")
            self.progress_signal.emit(idx, total)

            # Lấy kích thước gốc
            orig_size_str = "-"
            try:
                with Image.open(img_path) as im:
                    orig_size_str = f"{im.width}x{im.height}"
            except Exception:
                pass

            # Tải nguyên hình ảnh gốc lên ChatGPT và gửi prompt
            gpt_text = ""
            gpt_img_path = ""
            gpt_img_size = ""
            success = False
            try:
                self.log_signal.emit(f"🌐 Đang gửi NGUYÊN ẢNH GỐC lên ChatGPT với câu lệnh:")
                self.log_signal.emit(f"   \"{self.prompt}\"")
                gpt_res = self.bot.process_single_image(
                    image_path=img_path,
                    prompt=self.prompt,
                    output_dir=self.output_dir,
                    log_callback=lambda msg: self.log_signal.emit(f"  {msg}")
                )
                gpt_text = gpt_res.get("text", "")
                gpt_img_path = gpt_res.get("generated_image_path", "")
                gpt_img_size = gpt_res.get("generated_image_size", "")
                success = gpt_res.get("success", False)
                if gpt_img_path and os.path.exists(gpt_img_path):
                    self.log_signal.emit(f"🎉 Hoàn thành: Đã lưu ảnh AI mới tại {gpt_img_path}")
            except Exception as e:
                gpt_text = f"Lỗi ChatGPT: {str(e)}"
                self.log_signal.emit(f"❌ Lỗi: {str(e)}")

            result_item = {
                "original_filename": filename,
                "original_path": img_path,
                "original_size": orig_size_str,
                "gpt_image_path": gpt_img_path,
                "gpt_image_size": gpt_img_size,
                "enhanced_path": "",
                "enhanced_size": "-",
                "gpt_translation": gpt_text,
                "success": success,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            all_results.append(result_item)
            self.item_finished_signal.emit(idx, result_item)

        self.progress_signal.emit(total, total)

        # Xuất báo cáo tổng hợp nếu người dùng có tích chọn
        exported_files = {}
        if any(self.export_options.values()):
            self.log_signal.emit("\n==========================================")
            self.log_signal.emit("📊 Đang xuất báo cáo tổng hợp kết quả...")
            try:
                exported_files = ResultExporter.export_all(
                    all_results, 
                    self.output_dir, 
                    export_options=self.export_options
                )
                for k, fpath in exported_files.items():
                    self.log_signal.emit(f"📄 Đã tạo file {k.upper()}: {fpath}")
            except Exception as e:
                self.error_signal.emit(f"Lỗi xuất báo cáo: {str(e)}")

        self.all_finished_signal.emit(all_results, exported_files)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Image Translator & Enhancer - ChatGPT Automation")
        self.resize(1280, 850)
        self.setStyleSheet(MODERN_STYLE)

        self.bot = ChatGPTAutomation()
        self.worker: Optional[BatchProcessingWorker] = None
        self.image_list: List[str] = []
        self.results_data: List[Dict[str, Any]] = []
        self.exported_files: Dict[str, str] = {}
        
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(workspace_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        self.current_preview_orig = ""
        self.current_preview_gpt = ""

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header Banner
        header = QWidget()
        header.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #2563eb); border-radius: 8px; padding: 10px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 10, 14, 10)
        
        title_box = QVBoxLayout()
        title_lbl = QLabel("AI Image Translator & Enhancer (ChatGPT Automation)")
        title_lbl.setStyleSheet("color: white; font-size: 19px; font-weight: bold; background: transparent;")
        sub_lbl = QLabel("Tự động gửi nguyên ảnh gốc lên ChatGPT, mô phỏng lại nét vẽ, làm nét & dịch chữ trực tiếp lên ảnh")
        sub_lbl.setStyleSheet("color: #e2e8f0; font-size: 12px; background: transparent;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        main_layout.addWidget(header)

        # 2. Body Splitter
        splitter = QSplitter(Qt.Horizontal)

        # --- LEFT PANEL ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(10)

        # Group 1: Chrome & ChatGPT Login
        grp_login = QGroupBox("Bước 1: Kết nối Chrome & Đăng nhập ChatGPT")
        g1_layout = QVBoxLayout(grp_login)
        
        lbl_info = QLabel("Chỉ cần đăng nhập tài khoản ChatGPT 1 lần duy nhất trên trình duyệt. Lần sau tự động nhận diện.")
        lbl_info.setStyleSheet("color: #64748b; font-size: 11px;")
        lbl_info.setWordWrap(True)
        g1_layout.addWidget(lbl_info)

        btn_row_login = QHBoxLayout()
        self.btn_open_chrome = QPushButton("🌐 Mở Chrome Đăng Nhập GPT")
        self.btn_open_chrome.setObjectName("chromeBtn")
        self.btn_open_chrome.clicked.connect(self.handle_open_chrome)
        btn_row_login.addWidget(self.btn_open_chrome)

        self.btn_check_login = QPushButton("🔍 Kiểm Tra Đăng Nhập")
        self.btn_check_login.clicked.connect(self.handle_check_login)
        btn_row_login.addWidget(self.btn_check_login)
        g1_layout.addLayout(btn_row_login)

        self.lbl_login_status = QLabel("Trạng thái: Chưa kiểm tra")
        self.lbl_login_status.setStyleSheet("font-weight: 600; color: #475569;")
        g1_layout.addWidget(self.lbl_login_status)
        left_layout.addWidget(grp_login)

        # Group 2: Image Selection
        grp_images = QGroupBox("Bước 2: Danh sách hình ảnh đầu vào (Nguyên ảnh gốc)")
        g2_layout = QVBoxLayout(grp_images)

        btn_row_img = QHBoxLayout()
        self.btn_add_files = QPushButton("📁 Chọn File Ảnh...")
        self.btn_add_files.clicked.connect(self.handle_add_files)
        btn_row_img.addWidget(self.btn_add_files)

        self.btn_add_dir = QPushButton("📂 Chọn Thư Mục...")
        self.btn_add_dir.clicked.connect(self.handle_add_dir)
        btn_row_img.addWidget(self.btn_add_dir)

        self.btn_clear_list = QPushButton("🗑️ Xóa Danh Sách")
        self.btn_clear_list.clicked.connect(self.handle_clear_list)
        btn_row_img.addWidget(self.btn_clear_list)
        g2_layout.addLayout(btn_row_img)

        # Table
        self.table_images = QTableWidget()
        self.table_images.setColumnCount(5)
        self.table_images.setHorizontalHeaderLabels(["STT", "Tên File", "Kích Thước", "Ảnh GPT Sinh Ra", "Trạng Thái"])
        self.table_images.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_images.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_images.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_images.cellClicked.connect(self.handle_table_row_clicked)
        g2_layout.addWidget(self.table_images)
        left_layout.addWidget(grp_images)

        # Group 3: Prompt Setting
        grp_settings = QGroupBox("Bước 3: Câu lệnh Prompt gửi ChatGPT")
        g3_layout = QVBoxLayout(grp_settings)

        prompt_box = QVBoxLayout()
        row_p_head = QHBoxLayout()
        row_p_head.addWidget(QLabel("Câu lệnh gửi kèm ảnh:"))
        self.btn_reset_prompt = QPushButton("🔄 Đặt lại mặc định")
        self.btn_reset_prompt.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        self.btn_reset_prompt.clicked.connect(self.reset_prompt_to_default)
        row_p_head.addStretch()
        row_p_head.addWidget(self.btn_reset_prompt)
        prompt_box.addLayout(row_p_head)

        self.txt_prompt = QLineEdit()
        self.txt_prompt.setText(DEFAULT_PROMPT)
        prompt_box.addWidget(self.txt_prompt)
        g3_layout.addLayout(prompt_box)

        # Xuất file báo cáo
        row_export = QHBoxLayout()
        row_export.addWidget(QLabel("Xuất báo cáo (tùy chọn):"))
        self.chk_excel = QCheckBox("Excel (.xlsx)")
        self.chk_excel.setChecked(False)
        self.chk_html = QCheckBox("HTML (.html)")
        self.chk_html.setChecked(False)
        self.chk_word = QCheckBox("Word (.docx)")
        self.chk_word.setChecked(False)
        row_export.addWidget(self.chk_excel)
        row_export.addWidget(self.chk_html)
        row_export.addWidget(self.chk_word)
        g3_layout.addLayout(row_export)

        left_layout.addWidget(grp_settings)
        splitter.addWidget(left_widget)

        # --- RIGHT PANEL ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        # Control Action Buttons
        act_row = QHBoxLayout()
        self.btn_start = QPushButton("🚀 BẮT ĐẦU TẢI ẢNH LÊN GPT & MÔ PHỎNG LÀM NÉT")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.clicked.connect(self.handle_start_processing)
        act_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏹️ Dừng")
        self.btn_stop.setObjectName("dangerBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.handle_stop_processing)
        act_row.addWidget(self.btn_stop)
        right_layout.addLayout(act_row)

        # Progress
        prog_box = QVBoxLayout()
        self.lbl_progress = QLabel("Tiến trình: 0 / 0 ảnh đã hoàn thành (0%)")
        self.lbl_progress.setStyleSheet("font-weight: 600; color: #1e40af;")
        self.prog_bar = QProgressBar()
        self.prog_bar.setValue(0)
        prog_box.addWidget(self.lbl_progress)
        prog_box.addWidget(self.prog_bar)
        right_layout.addLayout(prog_box)

        # Tabs: Preview & Logs
        self.tabs = QTabWidget()

        # Tab 1: So sánh hình ảnh
        tab_images = QWidget()
        ti_layout = QHBoxLayout(tab_images)
        ti_layout.setSpacing(14)
        
        # Cột ảnh gốc
        box_orig = QVBoxLayout()
        self.lbl_orig_info = QLabel("Ảnh Gốc")
        self.lbl_orig_info.setStyleSheet("font-weight: 600; color: #475569; font-size: 13px;")
        self.lbl_orig_img = QLabel("Chưa chọn ảnh")
        self.lbl_orig_img.setAlignment(Qt.AlignCenter)
        self.lbl_orig_img.setStyleSheet("background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 8px;")
        box_orig.addWidget(self.lbl_orig_info)
        box_orig.addWidget(self.lbl_orig_img, 1)

        self.btn_view_orig = QPushButton("🔍 Mở Xem Ảnh Gốc (Kích Thước Thật)")
        self.btn_view_orig.setEnabled(False)
        self.btn_view_orig.clicked.connect(lambda: self.open_image_external(self.current_preview_orig))
        box_orig.addWidget(self.btn_view_orig)
        ti_layout.addLayout(box_orig)

        # Cột ảnh GPT Mô Phỏng & Dịch
        box_gpt = QVBoxLayout()
        self.lbl_gpt_info = QLabel("✨ Ảnh ChatGPT Mô Phỏng & Dịch Trực Tiếp")
        self.lbl_gpt_info.setStyleSheet("font-weight: 700; color: #2563eb; font-size: 13px;")
        self.lbl_gpt_img = QLabel("Chưa có kết quả từ ChatGPT")
        self.lbl_gpt_img.setAlignment(Qt.AlignCenter)
        self.lbl_gpt_img.setStyleSheet("background: #eff6ff; border: 2px solid #93c5fd; border-radius: 8px;")
        box_gpt.addWidget(self.lbl_gpt_info)
        box_gpt.addWidget(self.lbl_gpt_img, 1)

        self.btn_view_gpt = QPushButton("✨ Mở Xem Ảnh GPT Tạo (Kích Thước Gốc)")
        self.btn_view_gpt.setObjectName("successBtn")
        self.btn_view_gpt.setEnabled(False)
        self.btn_view_gpt.clicked.connect(lambda: self.open_image_external(self.current_preview_gpt))
        box_gpt.addWidget(self.btn_view_gpt)
        ti_layout.addLayout(box_gpt)

        self.tabs.addTab(tab_images, "🖼️ So Sánh: Ảnh Gốc vs Ảnh GPT Tạo Mới")

        # Tab 2: Nội dung từ ChatGPT
        tab_trans = QWidget()
        tt_layout = QVBoxLayout(tab_trans)
        self.txt_translation = QTextEdit()
        self.txt_translation.setReadOnly(True)
        self.txt_translation.setPlaceholderText("Nội dung phản hồi hoặc mô tả từ ChatGPT sẽ hiển thị tại đây...")
        tt_layout.addWidget(self.txt_translation)
        self.tabs.addTab(tab_trans, "📝 Ghi Chú & Nội Dung Từ GPT")

        # Tab 3: Nhật ký tiến trình
        tab_log = QWidget()
        tl_layout = QVBoxLayout(tab_log)
        self.txt_log = QTextEdit()
        self.txt_log.setObjectName("logBox")
        self.txt_log.setReadOnly(True)
        tl_layout.addWidget(self.txt_log)
        self.tabs.addTab(tab_log, "📜 Nhật Ký Tiến Trình")

        right_layout.addWidget(self.tabs, 1)

        # Bottom Bar: Nút mở file kết quả
        bottom_row = QHBoxLayout()
        self.btn_open_excel = QPushButton("📊 Mở File Excel Kết Quả")
        self.btn_open_excel.setObjectName("successBtn")
        self.btn_open_excel.setEnabled(False)
        self.btn_open_excel.clicked.connect(lambda: self.open_file_external("excel"))
        bottom_row.addWidget(self.btn_open_excel)

        self.btn_open_html = QPushButton("🌐 Mở Báo Cáo HTML Trực Quan")
        self.btn_open_html.setObjectName("successBtn")
        self.btn_open_html.setEnabled(False)
        self.btn_open_html.clicked.connect(lambda: self.open_file_external("html"))
        bottom_row.addWidget(self.btn_open_html)

        self.btn_open_gpt_folder = QPushButton("🎨 Mở Thư Mục Ảnh GPT")
        self.btn_open_gpt_folder.clicked.connect(self.open_gpt_folder)
        bottom_row.addWidget(self.btn_open_gpt_folder)

        self.btn_open_folder = QPushButton("📂 Toàn Bộ Thư Mục Output")
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        bottom_row.addWidget(self.btn_open_folder)

        right_layout.addLayout(bottom_row)
        splitter.addWidget(right_widget)

        splitter.setSizes([480, 800])
        main_layout.addWidget(splitter)

        # Tự động kiểm tra trạng thái đăng nhập
        self.handle_check_login()

    def log(self, text: str):
        self.txt_log.append(text)
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def reset_prompt_to_default(self):
        self.txt_prompt.setText(DEFAULT_PROMPT)

    def handle_open_chrome(self):
        self.log("Đang mở trình duyệt Google Chrome...")
        self.lbl_login_status.setText("Trạng thái: Đang mở Chrome...")
        success = self.bot.open_for_login(callback=self.log)
        if success:
            self.lbl_login_status.setText("Trạng thái: Chrome đã mở! Hãy đăng nhập trên trình duyệt.")
            QMessageBox.information(
                self, 
                "Chrome ChatGPT Đã Mở", 
                "Trình duyệt Chrome đã được khởi động với profile riêng biệt.\n\n"
                "1. Bạn hãy đăng nhập tài khoản ChatGPT của mình trên trình duyệt.\n"
                "2. Sau khi đăng nhập xong, bạn quay lại đây và bấm 'Kiểm Tra Đăng Nhập' để bắt đầu!\n\n"
                "Phiên đăng nhập này sẽ được lưu giữ vĩnh viễn cho các lần sau."
            )
        else:
            self.lbl_login_status.setText("Trạng thái: Lỗi khởi động Chrome.")
            QMessageBox.warning(self, "Lỗi", "Không thể khởi động Chrome. Vui lòng kiểm tra lại Google Chrome đã được cài đặt chưa.")

    def handle_check_login(self):
        self.log("Đang kiểm tra trạng thái đăng nhập ChatGPT...")
        is_logged, info = self.bot.check_login_status()
        if is_logged:
            user_text = f"Đã đăng nhập: {info} ✅" if info != "Đã sẵn sàng" else "Đã đăng nhập ChatGPT thành công! ✅"
            self.lbl_login_status.setText(f"Trạng thái: {user_text}")
            self.lbl_login_status.setStyleSheet("font-weight: 600; color: #10b981;")
            self.log(f"✅ Xác nhận: {user_text}")
        else:
            self.lbl_login_status.setText(f"Trạng thái: {info}")
            self.lbl_login_status.setStyleSheet("font-weight: 600; color: #ef4444;")
            self.log(f"⚠️ {info}")

    def handle_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn file hình ảnh gốc",
            "",
            "Hình ảnh (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;Tất cả (*.*)"
        )
        if files:
            self.add_images_to_list(files)

    def handle_add_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa hình ảnh gốc")
        if folder:
            valid_exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')
            files = []
            for root, _, filenames in os.walk(folder):
                for f in filenames:
                    if f.lower().endswith(valid_exts):
                        files.append(os.path.join(root, f))
            if files:
                self.add_images_to_list(files)
            else:
                QMessageBox.information(self, "Thông báo", "Không tìm thấy file hình ảnh nào trong thư mục đã chọn.")

    def add_images_to_list(self, files: List[str]):
        added_count = 0
        for f in files:
            if f not in self.image_list and os.path.exists(f):
                self.image_list.append(f)
                added_count += 1

        self.update_table()
        self.lbl_progress.setText(f"Tiến trình: 0 / {len(self.image_list)} ảnh đã hoàn thành (0%)")
        self.log(f"Đã nạp thêm {added_count} ảnh vào danh sách chờ. Tổng số: {len(self.image_list)}")

    def handle_clear_list(self):
        self.image_list.clear()
        self.results_data.clear()
        self.table_images.setRowCount(0)
        self.lbl_progress.setText("Tiến trình: 0 / 0 ảnh đã hoàn thành (0%)")
        self.prog_bar.setValue(0)
        self.lbl_orig_img.setText("Chưa chọn ảnh")
        self.lbl_gpt_img.setText("Chưa có kết quả từ ChatGPT")
        self.btn_view_orig.setEnabled(False)
        self.btn_view_gpt.setEnabled(False)
        self.txt_translation.clear()
        self.log("Đã xóa danh sách ảnh.")

    def update_table(self):
        self.table_images.setRowCount(len(self.image_list))
        for row, path in enumerate(self.image_list):
            filename = os.path.basename(path)
            
            size_str = "-"
            try:
                with Image.open(path) as im:
                    size_str = f"{im.width}x{im.height}"
            except Exception:
                pass

            item_stt = QTableWidgetItem(str(row + 1))
            item_stt.setTextAlignment(Qt.AlignCenter)
            item_name = QTableWidgetItem(filename)
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignCenter)
            item_gpt = QTableWidgetItem("-")
            item_gpt.setTextAlignment(Qt.AlignCenter)
            item_status = QTableWidgetItem("Chờ xử lý ⏳")
            item_status.setTextAlignment(Qt.AlignCenter)

            self.table_images.setItem(row, 0, item_stt)
            self.table_images.setItem(row, 1, item_name)
            self.table_images.setItem(row, 2, item_size)
            self.table_images.setItem(row, 3, item_gpt)
            self.table_images.setItem(row, 4, item_status)

    def handle_table_row_clicked(self, row: int, col: int):
        if 0 <= row < len(self.image_list):
            orig_path = self.image_list[row]
            self.current_preview_orig = orig_path
            self.display_image_preview(self.lbl_orig_img, orig_path)
            self.lbl_orig_info.setText(f"Ảnh Gốc: {os.path.basename(orig_path)}")
            self.btn_view_orig.setEnabled(True)

            found = False
            for r in self.results_data:
                if r.get("original_path") == orig_path:
                    gpt_path = r.get("gpt_image_path", "")
                    if gpt_path and os.path.exists(gpt_path):
                        self.current_preview_gpt = gpt_path
                        self.display_image_preview(self.lbl_gpt_img, gpt_path)
                        self.lbl_gpt_info.setText(f"✨ Ảnh GPT Mô Phỏng & Dịch ({r.get('gpt_image_size', '')})")
                        self.btn_view_gpt.setEnabled(True)
                    else:
                        self.lbl_gpt_img.setText("Chưa có ảnh kết quả từ GPT")
                        self.btn_view_gpt.setEnabled(False)

                    self.txt_translation.setText(r.get("gpt_translation", ""))
                    found = True
                    break

            if not found:
                self.lbl_gpt_img.setText("Chưa xử lý với ChatGPT")
                self.btn_view_gpt.setEnabled(False)
                self.txt_translation.setText("Chưa có dữ liệu từ ChatGPT.")

    def display_image_preview(self, label: QLabel, path: str):
        if os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                scaled = pix.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled)
                return
        label.setText("Không tìm thấy file ảnh")

    def handle_start_processing(self):
        if not self.image_list:
            QMessageBox.warning(self, "Chưa chọn ảnh", "Vui lòng chọn ít nhất 1 hình ảnh trước khi bắt đầu!")
            return

        prompt = self.txt_prompt.text().strip()
        if not prompt:
            prompt = DEFAULT_PROMPT

        export_opts = {
            "excel": self.chk_excel.isChecked(),
            "html": self.chk_html.isChecked(),
            "docx": self.chk_word.isChecked()
        }

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.tabs.setCurrentIndex(2)  # Xem tab Log

        self.worker = BatchProcessingWorker(
            image_paths=self.image_list,
            prompt=prompt,
            export_options=export_opts,
            output_dir=self.output_dir
        )
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.item_finished_signal.connect(self.on_item_finished)
        self.worker.all_finished_signal.connect(self.on_all_finished)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()

    def handle_stop_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log("🛑 Đang gửi yêu cầu dừng tiến trình...")
            self.btn_stop.setEnabled(False)

    def on_progress(self, current: int, total: int):
        if total > 0:
            pct = int((current / total) * 100)
            self.prog_bar.setValue(pct)
            self.lbl_progress.setText(f"Tiến trình: {current} / {total} ảnh đã hoàn thành ({pct}%)")

    def on_item_finished(self, row_idx: int, result: Dict[str, Any]):
        self.results_data.append(result)
        
        # Cập nhật bảng
        if row_idx < self.table_images.rowCount():
            gpt_img = result.get("gpt_image_path", "")
            if gpt_img and os.path.exists(gpt_img):
                item_gpt = QTableWidgetItem("Đã tạo 🎨")
                item_gpt.setForeground(QColor("#2563eb"))
            else:
                item_gpt = QTableWidgetItem("-")
            item_gpt.setTextAlignment(Qt.AlignCenter)
            self.table_images.setItem(row_idx, 3, item_gpt)

            status_text = "Hoàn thành ✅" if result.get("success", False) else "Lỗi ❌"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setForeground(QColor("#10b981" if result.get("success", False) else "#ef4444"))
            self.table_images.setItem(row_idx, 4, item_status)

        # Hiển thị ảnh và nội dung
        orig_path = result.get("original_path", "")
        self.current_preview_orig = orig_path
        self.display_image_preview(self.lbl_orig_img, orig_path)
        self.lbl_orig_info.setText(f"Ảnh Gốc ({result.get('original_size', '')})")
        self.btn_view_orig.setEnabled(True)

        gpt_path = result.get("gpt_image_path", "")
        if gpt_path and os.path.exists(gpt_path):
            self.current_preview_gpt = gpt_path
            self.display_image_preview(self.lbl_gpt_img, gpt_path)
            self.lbl_gpt_info.setText(f"✨ Ảnh GPT Mô Phỏng & Dịch ({result.get('gpt_image_size', '')})")
            self.btn_view_gpt.setEnabled(True)
        else:
            self.lbl_gpt_img.setText("Không tạo được ảnh mới từ GPT")
            self.btn_view_gpt.setEnabled(False)

        self.txt_translation.setText(result.get("gpt_translation", ""))

    def on_all_finished(self, all_results: List[Dict[str, Any]], exported_files: Dict[str, str]):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.exported_files = exported_files

        if "excel" in exported_files:
            self.btn_open_excel.setEnabled(True)
        if "html" in exported_files:
            self.btn_open_html.setEnabled(True)

        self.log("\n==========================================")
        self.log("🎉 TẤT CẢ TIẾN TRÌNH ĐÃ HOÀN TẤT THÀNH CÔNG!")
        self.tabs.setCurrentIndex(0)  # Chuyển về xem ảnh đối chiếu

        msg = f"Đã hoàn thành xử lý cho {len(all_results)} hình ảnh!\n\nẢnh AI mới đã được lưu trong thư mục 'output/anh_tao_tu_gpt/'."
        if exported_files:
            msg += "\n\nCác file báo cáo đã tạo:"
            for k, p in exported_files.items():
                msg += f"\n- {k.upper()}: {os.path.basename(p)}"
        
        QMessageBox.information(self, "Thành Công", msg)

    def on_worker_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log(f"❌ LỖI: {err_msg}")
        QMessageBox.critical(self, "Lỗi Quá Trình", err_msg)

    def open_image_external(self, image_path: str):
        if image_path and os.path.exists(image_path):
            try:
                os.startfile(image_path)
            except Exception as e:
                self.log(f"Không thể mở ảnh: {e}")
        else:
            QMessageBox.warning(self, "Thông báo", "File hình ảnh không tồn tại.")

    def open_file_external(self, file_key: str):
        path = self.exported_files.get(file_key, "")
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                self.log(f"Không thể mở file: {e}")
        else:
            QMessageBox.warning(self, "Thông báo", "File báo cáo chưa được tạo.")

    def open_gpt_folder(self):
        gpt_folder = os.path.join(self.output_dir, "anh_tao_tu_gpt")
        os.makedirs(gpt_folder, exist_ok=True)
        os.startfile(gpt_folder)

    def open_output_folder(self):
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)
        else:
            QMessageBox.warning(self, "Thông báo", "Thư mục output chưa tồn tại.")
