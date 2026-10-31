"""
Giao diện người dùng chính (GUI) phát triển bằng PySide6.
Đầy đủ các tính năng:
- Mở Chrome đăng nhập ChatGPT với profile độc lập
- Chọn danh sách ảnh hoặc kéo thả trực tiếp
- Tự động làm nét và gửi lên ChatGPT để dịch
- Xem trước ảnh gốc vs ảnh nét và nội dung dịch theo thời gian thực
- Xuất báo cáo tổng hợp ra file Excel, HTML, Word và mở nhanh
"""

import os
import sys
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QCheckBox, QTextEdit, QProgressBar,
    QGroupBox, QSplitter, QMessageBox, QTabWidget, QAbstractItemView
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor

from core.chatgpt_bot import ChatGPTAutomation, find_chrome_path
from core.enhancer import ImageEnhancer
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
        target_lang: str,
        enhance_mode: str,
        scale: float,
        export_options: Dict[str, bool],
        output_dir: str
    ):
        super().__init__()
        self.image_paths = image_paths
        self.target_lang = target_lang
        self.enhance_mode = enhance_mode
        self.scale = scale
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

        enhanced_folder = os.path.join(self.output_dir, "anh_da_lam_net")
        os.makedirs(enhanced_folder, exist_ok=True)

        all_results = []
        self.log_signal.emit(f"🚀 Bắt đầu tiến trình xử lý hàng loạt cho {total} hình ảnh...")

        for idx, img_path in enumerate(self.image_paths):
            if not self.is_running:
                self.log_signal.emit("⚠️ Tiến trình đã bị người dùng tạm dừng.")
                break

            filename = os.path.basename(img_path)
            self.log_signal.emit(f"\n==========================================")
            self.log_signal.emit(f"[{idx + 1}/{total}] Đang xử lý file: {filename}")
            self.progress_signal.emit(idx, total)

            # Lấy thông tin kích thước gốc
            orig_size_str = "-"
            try:
                with Image.open(img_path) as im:
                    orig_size_str = f"{im.width}x{im.height}"
            except Exception:
                pass

            # Bước 1: Làm nét và tăng độ phân giải ảnh
            name_no_ext, ext = os.path.splitext(filename)
            enhanced_filename = f"{name_no_ext}_sharp_{int(self.scale)}x{ext}"
            enhanced_path = os.path.join(enhanced_folder, enhanced_filename)

            enh_size_str = "-"
            try:
                self.log_signal.emit(f"⚙️ Đang áp dụng bộ lọc làm nét & siêu phân giải {int(self.scale)}x...")
                ImageEnhancer.process_image(
                    input_path=img_path,
                    output_path=enhanced_path,
                    scale=self.scale,
                    mode=self.enhance_mode
                )
                with Image.open(enhanced_path) as im:
                    enh_size_str = f"{im.width}x{im.height}"
                self.log_signal.emit(f"✅ Đã làm nét thành công! Kích thước mới: {enh_size_str}")
            except Exception as e:
                self.log_signal.emit(f"⚠️ Lỗi khi làm nét ảnh: {e}. Sẽ dùng ảnh gốc để gửi lên GPT.")
                enhanced_path = img_path

            # Bước 2: Tải lên ChatGPT để dịch
            gpt_text = ""
            success = False
            try:
                self.log_signal.emit(f"🌐 Đang mở Chrome ChatGPT và gửi yêu cầu dịch thuật...")
                gpt_res = self.bot.process_single_image(
                    image_path=img_path,
                    target_lang=self.target_lang,
                    log_callback=lambda msg: self.log_signal.emit(f"  [ChatGPT] {msg}")
                )
                gpt_text = gpt_res.get("text", "")
                success = True
                self.log_signal.emit(f"🎉 Hoàn thành dịch cho ảnh: {filename}")
            except Exception as e:
                gpt_text = f"Lỗi ChatGPT: {str(e)}"
                self.log_signal.emit(f"❌ Lỗi khi gửi sang ChatGPT: {str(e)}")

            result_item = {
                "original_filename": filename,
                "original_path": img_path,
                "original_size": orig_size_str,
                "enhanced_path": enhanced_path,
                "enhanced_size": enh_size_str,
                "gpt_translation": gpt_text,
                "success": success,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            all_results.append(result_item)
            self.item_finished_signal.emit(idx, result_item)

        self.progress_signal.emit(total, total)

        # Bước 3: Xuất báo cáo tổng hợp
        self.log_signal.emit("\n==========================================")
        self.log_signal.emit("📊 Đang tổng hợp kết quả và xuất file báo cáo...")
        try:
            exported_files = ResultExporter.export_all(all_results, self.output_dir)
            for k, fpath in exported_files.items():
                self.log_signal.emit(f"📄 Đã tạo file {k.upper()}: {fpath}")
            self.all_finished_signal.emit(all_results, exported_files)
        except Exception as e:
            self.error_signal.emit(f"Lỗi khi xuất file báo cáo: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Image Translator & Enhancer - ChatGPT Automation")
        self.resize(1200, 800)
        self.setStyleSheet(MODERN_STYLE)

        self.bot = ChatGPTAutomation()
        self.worker: Optional[BatchProcessingWorker] = None
        self.image_list: List[str] = []
        self.results_data: List[Dict[str, Any]] = []
        self.exported_files: Dict[str, str] = {}
        
        # Thư mục output mặc định
        workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(workspace_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

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
        h_layout.setContentsMargins(12, 8, 12, 8)
        
        title_box = QVBoxLayout()
        title_lbl = QLabel("AI Image Translator & Sharpener")
        title_lbl.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent;")
        sub_lbl = QLabel("Tự động hóa Chrome GPT dịch hình ảnh & Nâng cấp độ nét siêu phân giải (Super-Resolution)")
        sub_lbl.setStyleSheet("color: #e2e8f0; font-size: 12px; background: transparent;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        main_layout.addWidget(header)

        # 2. Body Splitter (Left config & table | Right progress & preview)
        splitter = QSplitter(Qt.Horizontal)

        # --- LEFT PANEL ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(10)

        # Group 1: Chrome & ChatGPT Login
        grp_login = QGroupBox("Bước 1: Kết nối Chrome & Đăng nhập ChatGPT")
        g1_layout = QVBoxLayout(grp_login)
        
        lbl_info = QLabel("Phiên đăng nhập được lưu vĩnh viễn trong Chrome Profile của ứng dụng.")
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

        self.lbl_login_status = QLabel("Trạng thái: Chưa mở trình duyệt")
        self.lbl_login_status.setStyleSheet("font-weight: 600; color: #475569;")
        g1_layout.addWidget(self.lbl_login_status)
        left_layout.addWidget(grp_login)

        # Group 2: Image Selection
        grp_images = QGroupBox("Bước 2: Danh sách hình ảnh đầu vào")
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
        self.table_images.setColumnCount(4)
        self.table_images.setHorizontalHeaderLabels(["STT", "Tên File", "Kích Thước", "Trạng Thái"])
        self.table_images.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_images.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_images.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_images.cellClicked.connect(self.handle_table_row_clicked)
        g2_layout.addWidget(self.table_images)
        left_layout.addWidget(grp_images)

        # Group 3: Settings
        grp_settings = QGroupBox("Bước 3: Cài đặt dịch thuật & Làm nét")
        g3_layout = QVBoxLayout(grp_settings)

        # Ngôn ngữ
        row_lang = QHBoxLayout()
        row_lang.addWidget(QLabel("Ngôn ngữ dịch:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Tiếng Việt", "English", "日本語 (Tiếng Nhật)", "한국어 (Tiếng Hàn)", "中文 (Tiếng Trung)", "Français (Tiếng Pháp)", "Deutsch (Tiếng Đức)"])
        row_lang.addWidget(self.combo_lang)
        g3_layout.addLayout(row_lang)

        # Làm nét
        row_enh = QHBoxLayout()
        row_enh.addWidget(QLabel("Chế độ làm nét:"))
        self.combo_enhance = QComboBox()
        self.combo_enhance.addItems([
            "Siêu nét 4x Ultra-HD (Khuyên dùng - Cực nét cho ảnh nhỏ/bìa)",
            "Siêu nét 2x (Cân bằng & Tự nhiên)",
            "Tối ưu tương phản & văn bản (Dành cho tài liệu/chữ)"
        ])
        row_enh.addWidget(self.combo_enhance)
        g3_layout.addLayout(row_enh)

        # Định dạng xuất file
        row_export = QHBoxLayout()
        row_export.addWidget(QLabel("Xuất file báo cáo:"))
        self.chk_excel = QCheckBox("Excel (.xlsx)")
        self.chk_excel.setChecked(True)
        self.chk_html = QCheckBox("HTML (.html)")
        self.chk_html.setChecked(True)
        self.chk_word = QCheckBox("Word (.docx)")
        self.chk_word.setChecked(True)
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
        self.btn_start = QPushButton("🚀 BẮT ĐẦU DỊCH & LÀM NÉT HÀNG LOẠT")
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

        # Tab 1: So sánh hình ảnh (Ảnh gốc vs Ảnh làm nét)
        tab_images = QWidget()
        ti_layout = QHBoxLayout(tab_images)
        
        # Cột ảnh gốc
        box_orig = QVBoxLayout()
        self.lbl_orig_info = QLabel("Ảnh Gốc")
        self.lbl_orig_info.setStyleSheet("font-weight: 600; color: #475569;")
        self.lbl_orig_img = QLabel("Chưa chọn ảnh")
        self.lbl_orig_img.setAlignment(Qt.AlignCenter)
        self.lbl_orig_img.setStyleSheet("background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 6px;")
        box_orig.addWidget(self.lbl_orig_info)
        box_orig.addWidget(self.lbl_orig_img, 1)
        ti_layout.addLayout(box_orig)

        # Cột ảnh làm nét
        box_enh = QVBoxLayout()
        self.lbl_enh_info = QLabel("Ảnh Đã Làm Nét")
        self.lbl_enh_info.setStyleSheet("font-weight: 600; color: #2563eb;")
        self.lbl_enh_img = QLabel("Chưa có kết quả làm nét")
        self.lbl_enh_img.setAlignment(Qt.AlignCenter)
        self.lbl_enh_img.setStyleSheet("background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 6px;")
        box_enh.addWidget(self.lbl_enh_info)
        box_enh.addWidget(self.lbl_enh_img, 1)
        ti_layout.addLayout(box_enh)

        self.tabs.addTab(tab_images, "🖼️ So Sánh Trước & Sau")

        # Tab 2: Nội dung dịch từ ChatGPT
        tab_trans = QWidget()
        tt_layout = QVBoxLayout(tab_trans)
        self.txt_translation = QTextEdit()
        self.txt_translation.setReadOnly(True)
        self.txt_translation.setPlaceholderText("Nội dung dịch thuật và giải thích từ ChatGPT sẽ hiển thị tại đây sau khi hoàn thành...")
        tt_layout.addWidget(self.txt_translation)
        self.tabs.addTab(tab_trans, "📝 Bản Dịch Tiếng Việt (GPT)")

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

        self.btn_open_folder = QPushButton("📂 Mở Thư Mục Kết Quả")
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        bottom_row.addWidget(self.btn_open_folder)

        right_layout.addLayout(bottom_row)
        splitter.addWidget(right_widget)

        splitter.setSizes([450, 750])
        main_layout.addWidget(splitter)

    # --- SỰ KIỆN NÚT VÀ LOGIC ---
    def log(self, text: str):
        self.txt_log.append(text)
        # Tự động cuộn xuống dưới
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_open_chrome(self):
        """Mở cửa sổ Chrome để đăng nhập ChatGPT"""
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
                "2. Sau khi đăng nhập xong, bạn có thể quay lại đây và bấm 'Bắt đầu dịch & làm nét' bất cứ lúc nào!\n"
                "Phiên đăng nhập này sẽ được lưu giữ vĩnh viễn."
            )
        else:
            self.lbl_login_status.setText("Trạng thái: Lỗi khởi động Chrome.")
            QMessageBox.warning(self, "Lỗi", "Không thể khởi động Chrome. Vui lòng kiểm tra lại Google Chrome đã được cài đặt chưa.")

    def handle_check_login(self):
        """Kiểm tra xem người dùng đã đăng nhập ChatGPT hay chưa"""
        self.log("Đang kiểm tra trạng thái đăng nhập ChatGPT...")
        is_logged, info = self.bot.check_login_status()
        if is_logged:
            user_text = f"Đã đăng nhập: {info} ✅" if info != "Đã sẵn sàng" else "Đã đăng nhập ChatGPT thành công! ✅"
            self.lbl_login_status.setText(f"Trạng thái: {user_text}")
            self.lbl_login_status.setStyleSheet("font-weight: 600; color: #10b981;")
            self.log(f"✅ Xác nhận: {user_text}")
            QMessageBox.information(self, "Trạng thái", f"Tuyệt vời! {user_text}\nChatGPT đã sẵn sàng xử lý hình ảnh.")
        else:
            self.lbl_login_status.setText(f"Trạng thái: {info}")
            self.lbl_login_status.setStyleSheet("font-weight: 600; color: #ef4444;")
            self.log(f"⚠️ {info}")
            QMessageBox.warning(self, "Chưa đăng nhập", f"Thông báo: {info}\nHãy bấm 'Mở Chrome Đăng Nhập GPT' và đăng nhập trên trình duyệt trước.")

    def handle_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn file hình ảnh",
            "",
            "Hình ảnh (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;Tất cả (*.*)"
        )
        if files:
            self.add_images_to_list(files)

    def handle_add_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa hình ảnh")
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
        self.lbl_enh_img.setText("Chưa có kết quả làm nét")
        self.txt_translation.clear()
        self.log("Đã xóa danh sách ảnh.")

    def update_table(self):
        self.table_images.setRowCount(len(self.image_list))
        for row, path in enumerate(self.image_list):
            filename = os.path.basename(path)
            
            # Kích thước
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
            item_status = QTableWidgetItem("Chờ xử lý ⏳")
            item_status.setTextAlignment(Qt.AlignCenter)

            self.table_images.setItem(row, 0, item_stt)
            self.table_images.setItem(row, 1, item_name)
            self.table_images.setItem(row, 2, item_size)
            self.table_images.setItem(row, 3, item_status)

    def handle_table_row_clicked(self, row: int, col: int):
        if 0 <= row < len(self.image_list):
            orig_path = self.image_list[row]
            self.display_image_preview(self.lbl_orig_img, orig_path)
            self.lbl_orig_info.setText(f"Ảnh Gốc: {os.path.basename(orig_path)}")

            # Kiểm tra xem ảnh này đã có kết quả trong results_data chưa
            found = False
            for r in self.results_data:
                if r.get("original_path") == orig_path:
                    enh_path = r.get("enhanced_path", "")
                    if os.path.exists(enh_path):
                        self.display_image_preview(self.lbl_enh_img, enh_path)
                        self.lbl_enh_info.setText(f"Ảnh Đã Làm Nét ({r.get('enhanced_size', '')})")
                    self.txt_translation.setText(r.get("gpt_translation", ""))
                    found = True
                    break

            if not found:
                self.lbl_enh_img.setText("Chưa xử lý làm nét")
                self.txt_translation.setText("Chưa có dữ liệu dịch từ ChatGPT.")

    def display_image_preview(self, label: QLabel, path: str):
        if os.path.exists(path):
            pix = QPixmap(path)
            scaled = pix.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
        else:
            label.setText("Không tìm thấy file ảnh")

    def handle_start_processing(self):
        if not self.image_list:
            QMessageBox.warning(self, "Chưa chọn ảnh", "Vui lòng chọn ít nhất 1 hình ảnh trước khi bắt đầu!")
            return

        # Lấy tham số ngôn ngữ chuẩn xác
        raw_lang = self.combo_lang.currentText()
        if "(" in raw_lang:
            target_lang = raw_lang.split("(")[0].strip()
        else:
            target_lang = raw_lang.strip()
        enh_idx = self.combo_enhance.currentIndex()
        if enh_idx == 0:
            scale = 4.0
            mode = "ultra"
        elif enh_idx == 1:
            scale = 2.0
            mode = "balanced"
        else:
            scale = 4.0
            mode = "text"

        export_opts = {
            "excel": self.chk_excel.isChecked(),
            "html": self.chk_html.isChecked(),
            "docx": self.chk_word.isChecked()
        }

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.tabs.setCurrentIndex(2)  # chuyển sang xem tab Log

        self.worker = BatchProcessingWorker(
            image_paths=self.image_list,
            target_lang=target_lang,
            enhance_mode=mode,
            scale=scale,
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
        
        # Cập nhật trạng thái dòng trong bảng
        if row_idx < self.table_images.rowCount():
            status_text = "Hoàn thành ✅" if result.get("success", False) else "Lỗi ❌"
            item = QTableWidgetItem(status_text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("#10b981" if result.get("success", False) else "#ef4444"))
            self.table_images.setItem(row_idx, 3, item)

        # Hiển thị ảnh và bản dịch lên giao diện
        self.display_image_preview(self.lbl_orig_img, result.get("original_path", ""))
        self.lbl_orig_info.setText(f"Ảnh Gốc ({result.get('original_size', '')})")

        self.display_image_preview(self.lbl_enh_img, result.get("enhanced_path", ""))
        self.lbl_enh_info.setText(f"Ảnh Đã Làm Nét ({result.get('enhanced_size', '')})")

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
        self.tabs.setCurrentIndex(0)  # Chuyển về xem ảnh so sánh

        msg = f"Đã hoàn thành dịch và làm nét {len(all_results)} hình ảnh!\n\nCác file kết quả đã tạo:"
        for k, p in exported_files.items():
            msg += f"\n- {k.upper()}: {os.path.basename(p)}"
        
        QMessageBox.information(self, "Thành Công", msg)

    def on_worker_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log(f"❌ LỖI: {err_msg}")
        QMessageBox.critical(self, "Lỗi Quá Trình", err_msg)

    def open_file_external(self, file_key: str):
        path = self.exported_files.get(file_key, "")
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                self.log(f"Không thể mở file: {e}")
        else:
            QMessageBox.warning(self, "Thông báo", "File báo cáo chưa được tạo.")

    def open_output_folder(self):
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)
        else:
            QMessageBox.warning(self, "Thông báo", "Thư mục output chưa tồn tại.")

