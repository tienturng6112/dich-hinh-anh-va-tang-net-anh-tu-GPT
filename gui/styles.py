"""
Tập hợp stylesheet QSS hiện đại cho giao diện ứng dụng PySide6.
"""

MODERN_STYLE = """
/* Toàn bộ ứng dụng */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    font-size: 13px;
    color: #1e293b;
    background-color: #f8fafc;
}

/* Khung nhóm */
QGroupBox {
    font-weight: 600;
    font-size: 13px;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #2563eb;
}

/* Các loại nút bấm */
QPushButton {
    background-color: #f1f5f9;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e2e8f0;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #cbd5e1;
}

QPushButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* Nút chính nổi bật (Primary Button) */
QPushButton#primaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 8px;
}

QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
}

QPushButton#primaryBtn:pressed {
    background-color: #1e40af;
}

QPushButton#primaryBtn:disabled {
    background-color: #94a3b8;
}

/* Nút mở Chrome */
QPushButton#chromeBtn {
    background-color: #0f766e;
    color: #ffffff;
    border: none;
    font-weight: 600;
    padding: 9px 18px;
    border-radius: 6px;
}

QPushButton#chromeBtn:hover {
    background-color: #115e59;
}

/* Nút mở file/thư mục kết quả */
QPushButton#successBtn {
    background-color: #059669;
    color: #ffffff;
    border: none;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
}

QPushButton#successBtn:hover {
    background-color: #047857;
}

/* Nút Dừng */
QPushButton#dangerBtn {
    background-color: #ef4444;
    color: #ffffff;
    border: none;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
}

QPushButton#dangerBtn:hover {
    background-color: #dc2626;
}

/* Bảng hiển thị danh sách ảnh */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    selection-background-color: #eff6ff;
    selection-color: #1e40af;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    font-weight: 600;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
}

/* Ô nhập liệu và Combobox */
QLineEdit, QComboBox, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #bfdbfe;
    selection-color: #1e3a8a;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1.5px solid #2563eb;
}

/* Hộp chọn thả xuống (ComboBox) */
QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #eff6ff;
    selection-color: #1e40af;
}

/* Thanh tiến trình */
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: #1e293b;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #10b981);
    border-radius: 6px;
}

/* Nhật ký / Log Terminal */
QTextEdit#logBox {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 8px;
}

/* Checkbox */
QCheckBox {
    spacing: 8px;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #cbd5e1;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

/* Thanh cuộn */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

