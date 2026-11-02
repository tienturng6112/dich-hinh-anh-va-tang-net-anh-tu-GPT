"""
Module xuất báo cáo kết quả dịch và làm nét ảnh.
Hỗ trợ xuất ra:
1. File Excel (.xlsx) với định dạng đẹp mắt, có đường dẫn ảnh gốc, ảnh GPT sinh ra và nội dung dịch.
2. File HTML tương tác (.html) xem trực quan so sánh Ảnh Gốc vs Ảnh GPT Mô Phỏng & Dịch.
3. File Word (.docx) chứa bảng biểu và ảnh nhúng trực tiếp.
"""

from typing import Optional
import os
import html
from datetime import datetime
from typing import List, Dict, Any

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class ResultExporter:
    @staticmethod
    def export_all(
        results: List[Dict[str, Any]], 
        output_dir: str, 
        base_name: str = "ket_qua_dich_va_lam_net",
        export_options: Optional[Dict[str, bool]] = None
    ) -> Dict[str, str]:
        """
        Chỉ xuất báo cáo khi người dùng tích chọn.
        Nếu không tích chọn tùy chọn nào, tuyệt đối không tạo bất kỳ file báo cáo nào.
        """
        if not export_options:
            export_options = {}

        do_excel = export_options.get("excel", False)
        do_html = export_options.get("html", False)
        do_docx = export_options.get("docx", False)

        # Nếu người dùng bỏ tích toàn bộ thì không tạo file nào
        if not (do_excel or do_html or do_docx):
            return {}

        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = {}

        # 1. Xuất Excel
        if do_excel:
            excel_path = os.path.join(output_dir, f"{base_name}_{timestamp}.xlsx")
            try:
                ResultExporter.export_to_excel(results, excel_path)
                files["excel"] = excel_path
            except Exception as e:
                print(f"Lỗi khi xuất Excel: {e}")

        # 2. Xuất HTML
        if do_html:
            html_path = os.path.join(output_dir, f"{base_name}_{timestamp}.html")
            try:
                ResultExporter.export_to_html(results, html_path)
                files["html"] = html_path
            except Exception as e:
                print(f"Lỗi khi xuất HTML: {e}")

        # 3. Xuất Word
        if do_docx and HAS_DOCX:
            docx_path = os.path.join(output_dir, f"{base_name}_{timestamp}.docx")
            try:
                ResultExporter.export_to_docx(results, docx_path)
                files["docx"] = docx_path
            except Exception as e:
                print(f"Lỗi khi xuất Word: {e}")

        return files

    @staticmethod
    def export_to_excel(results: List[Dict[str, Any]], file_path: str) -> str:
        """Xuất danh sách kết quả ra file Excel chuẩn định dạng thẩm mỹ"""
        if not HAS_OPENPYXL:
            raise ImportError("Thư viện openpyxl chưa được cài đặt.")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Kết quả Dịch & Làm nét"

        # Định dạng màu sắc và font
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        bold_font = Font(name="Segoe UI", size=10, bold=True)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="top", wrap_text=True)

        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # Tiêu đề bảng
        headers = [
            "STT", 
            "Tên File Gốc", 
            "Kích Thước Gốc", 
            "Ảnh GPT Sinh Ra (Size)", 
            "Đường Dẫn Ảnh GPT Đã Dịch", 
            "Đường Dẫn Làm Nét Cục Bộ", 
            "Nội Dung Dịch / Ghi Chú (GPT)", 
            "Trạng Thái",
            "Thời Gian"
        ]

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = thin_border
        ws.row_dimensions[1].height = 28

        # Dữ liệu từng hàng
        for row_idx, res in enumerate(results, start=2):
            status = "Thành công" if res.get("success", False) else "Lỗi"
            status_color = "059669" if status == "Thành công" else "DC2626"

            gpt_img = res.get("gpt_image_path", "") or res.get("generated_image_path", "")
            gpt_size = res.get("gpt_image_size", "") or res.get("generated_image_size", "-")

            cells_data = [
                (row_idx - 1, center_align, regular_font),
                (res.get("original_filename", ""), left_align, bold_font),
                (res.get("original_size", "-"), center_align, regular_font),
                (gpt_size if gpt_size else "-", center_align, regular_font),
                (gpt_img if gpt_img else "-", left_align, regular_font),
                (res.get("enhanced_path", "-"), left_align, regular_font),
                (res.get("gpt_translation", "Không có nội dung"), left_align, regular_font),
                (status, center_align, Font(name="Segoe UI", size=10, bold=True, color=status_color)),
                (res.get("timestamp", datetime.now().strftime("%H:%M:%S")), center_align, regular_font)
            ]

            for col_idx, (val, align, font_style) in enumerate(cells_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.alignment = align
                cell.font = font_style
                cell.border = thin_border

            # Tự động chỉnh độ cao hàng cho văn bản dài
            text_len = len(str(res.get("gpt_translation", "")))
            ws.row_dimensions[row_idx].height = min(200, max(35, int(text_len / 4)))

        # Tự động căn chỉnh độ rộng cột
        col_widths = {
            1: 8,   # STT
            2: 25,  # Tên file
            3: 16,  # Kích thước gốc
            4: 18,  # Kích thước GPT
            5: 35,  # Đường dẫn ảnh GPT
            6: 30,  # Đường dẫn làm nét
            7: 55,  # Nội dung dịch
            8: 15,  # Trạng thái
            9: 15   # Thời gian
        }
        for col_idx, width in col_widths.items():
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        wb.save(file_path)
        return file_path

    @staticmethod
    def export_to_html(results: List[Dict[str, Any]], file_path: str) -> str:
        """Xuất báo cáo HTML hiện đại xem trực quan ảnh trước/sau và bản dịch"""
        total = len(results)
        success_count = sum(1 for r in results if r.get("success", False))

        cards_html = []
        for idx, res in enumerate(results, start=1):
            orig_name = html.escape(res.get("original_filename", f"Ảnh #{idx}"))
            orig_path = res.get("original_path", "").replace("\\", "/")
            gpt_img_path = (res.get("gpt_image_path", "") or res.get("generated_image_path", "")).replace("\\", "/")
            enh_path = res.get("enhanced_path", "").replace("\\", "/")
            orig_size = res.get("original_size", "-")
            gpt_size = res.get("gpt_image_size", "") or res.get("generated_image_size", "")
            enh_size = res.get("enhanced_size", "-")
            translation = html.escape(res.get("gpt_translation", "Chưa có nội dung dịch")).replace("\n", "<br>")
            status_badge = '<span class="badge badge-success">Thành công</span>' if res.get("success", False) else '<span class="badge badge-danger">Lỗi</span>'

            # Hiển thị ảnh kết quả chính (ưu tiên ảnh do GPT vẽ & dịch)
            main_result_html = ""
            if gpt_img_path and os.path.exists(gpt_img_path):
                main_result_html = f"""
                <div class="image-box highlight-box">
                    <div class="image-label image-label-gpt">✨ Ảnh ChatGPT Mô Phỏng & Dịch Trực Tiếp ({gpt_size or 'HD'})</div>
                    <img src="file:///{gpt_img_path}" alt="Ảnh GPT tạo" loading="lazy">
                    <div style="margin-top: 8px;">
                        <a href="file:///{gpt_img_path}" target="_blank" class="btn-link">🔍 Mở ảnh GPT kích thước gốc</a>
                    </div>
                </div>
                """
            elif enh_path and os.path.exists(enh_path):
                main_result_html = f"""
                <div class="image-box">
                    <div class="image-label image-label-enhanced">Ảnh Đã Làm Nét ({enh_size})</div>
                    <img src="file:///{enh_path}" alt="Ảnh đã làm nét" loading="lazy">
                    <div style="margin-top: 8px;">
                        <a href="file:///{enh_path}" target="_blank" class="btn-link">Mở ảnh nét đầy đủ</a>
                    </div>
                </div>
                """

            card = f"""
            <div class="result-card">
                <div class="card-header">
                    <div class="card-title">#{idx}. {orig_name}</div>
                    {status_badge}
                </div>
                <div class="card-body">
                    <div class="images-container">
                        <div class="image-box">
                            <div class="image-label">Ảnh Gốc ({orig_size})</div>
                            <img src="file:///{orig_path}" alt="Ảnh gốc" loading="lazy" onerror="this.src='';this.alt='Không tìm thấy ảnh gốc';">
                        </div>
                        {main_result_html}
                    </div>
                    <div class="translation-section">
                        <div class="translation-title">Nội Dung / Bản Dịch Từ ChatGPT:</div>
                        <div class="translation-box">{translation}</div>
                    </div>
                </div>
            </div>
            """
            cards_html.append(card)

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo Cáo Kết Quả Dịch & Làm Nét Ảnh - AI ChatGPT</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --success: #10b981;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text-main); line-height: 1.6; padding: 24px; }}
        .header {{ max-width: 1200px; margin: 0 auto 32px auto; background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 32px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(37,99,235,0.2); }}
        .header h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; font-size: 15px; }}
        .stats-bar {{ display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }}
        .stat-item {{ background: rgba(255,255,255,0.15); backdrop-filter: blur(8px); padding: 12px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; }}
        .container {{ max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }}
        .result-card {{ background: var(--card-bg); border-radius: 14px; border: 1px solid var(--border); box-shadow: 0 4px 12px rgba(0,0,0,0.04); overflow: hidden; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: #f1f5f9; border-bottom: 1px solid var(--border); }}
        .card-title {{ font-size: 16px; font-weight: 600; color: #1e293b; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .card-body {{ padding: 24px; }}
        .images-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
        @media (max-width: 768px) {{ .images-container {{ grid-template-columns: 1fr; }} }}
        .image-box {{ background: #f8fafc; border: 1px dashed var(--border); border-radius: 10px; padding: 12px; text-align: center; }}
        .highlight-box {{ border: 2px solid #3b82f6; background: #eff6ff; }}
        .image-label {{ font-size: 13px; font-weight: 600; margin-bottom: 10px; color: var(--text-muted); }}
        .image-label-enhanced {{ color: var(--primary); }}
        .image-label-gpt {{ color: #1d4ed8; font-size: 14px; font-weight: 700; }}
        .image-box img {{ max-width: 100%; max-height: 480px; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .btn-link {{ display: inline-block; font-size: 13px; color: var(--primary); text-decoration: none; font-weight: 600; }}
        .btn-link:hover {{ text-decoration: underline; }}
        .translation-section {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; }}
        .translation-title {{ font-weight: 600; font-size: 14px; margin-bottom: 10px; color: #334155; }}
        .translation-box {{ font-size: 14px; line-height: 1.7; color: #1e293b; background: white; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; word-break: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Báo Cáo Tổng Hợp: Mô Phỏng, Dịch & Làm Nét Ảnh (ChatGPT AI)</h1>
        <p>Tự động hóa Chrome tạo ảnh nét & dịch chữ trực tiếp lên ảnh qua AI ChatGPT</p>
        <div class="stats-bar">
            <div class="stat-item">Tổng số ảnh: {total}</div>
            <div class="stat-item">Thành công: {success_count}</div>
            <div class="stat-item">Thời gian xuất: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
        </div>
    </div>
    <div class="container">
        {"".join(cards_html)}
    </div>
</body>
</html>
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return file_path

    @staticmethod
    def export_to_docx(results: List[Dict[str, Any]], file_path: str) -> str:
        """Xuất báo cáo tài liệu Word (.docx) chứa đối chiếu ảnh và bản dịch"""
        if not HAS_DOCX:
            raise ImportError("Thư viện python-docx chưa được cài đặt.")

        doc = Document()

        # Tiêu đề tài liệu
        p_title = doc.add_paragraph()
        run_title = p_title.add_run("BÁO CÁO KẾT QUẢ DỊCH & LÀM NÉT HÌNH ẢNH (AI CHATGPT)")
        run_title.font.name = "Segoe UI"
        run_title.font.size = Pt(18)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(30, 58, 138)
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p_sub = doc.add_paragraph()
        run_sub = p_sub.add_run(f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Tổng số ảnh: {len(results)}")
        run_sub.font.name = "Segoe UI"
        run_sub.font.size = Pt(10)
        run_sub.font.italic = True
        run_sub.font.color.rgb = RGBColor(100, 116, 139)
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()

        # Từng mục ảnh
        for idx, res in enumerate(results, start=1):
            p_item = doc.add_paragraph()
            r_item = p_item.add_run(f"Ảnh #{idx}: {res.get('original_filename', '')}")
            r_item.font.name = "Segoe UI"
            r_item.font.size = Pt(13)
            r_item.font.bold = True
            r_item.font.color.rgb = RGBColor(37, 99, 235)

            # Bảng so sánh 2 cột ảnh
            table = doc.add_table(rows=1, cols=2)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            row_cells = table.rows[0].cells

            orig_path = res.get("original_path", "")
            gpt_img_path = res.get("gpt_image_path", "") or res.get("generated_image_path", "")
            enh_path = res.get("enhanced_path", "")
            result_img = gpt_img_path if (gpt_img_path and os.path.exists(gpt_img_path)) else enh_path

            # Cột 1: Ảnh gốc
            p_c1 = row_cells[0].paragraphs[0]
            p_c1.add_run(f"Ảnh Gốc ({res.get('original_size', '-')})\n").bold = True
            if os.path.exists(orig_path):
                try:
                    row_cells[0].paragraphs[0].add_run().add_picture(orig_path, width=Inches(3.0))
                except Exception:
                    row_cells[0].paragraphs[0].add_run("(Lỗi hiển thị ảnh gốc)")

            # Cột 2: Ảnh kết quả
            p_c2 = row_cells[1].paragraphs[0]
            label_c2 = "Ảnh GPT Đã Dịch & Mô Phỏng" if gpt_img_path else "Ảnh Đã Làm Nét"
            p_c2.add_run(f"{label_c2}\n").bold = True
            if os.path.exists(result_img):
                try:
                    row_cells[1].paragraphs[0].add_run().add_picture(result_img, width=Inches(3.0))
                except Exception:
                    row_cells[1].paragraphs[0].add_run("(Lỗi hiển thị ảnh kết quả)")

            # Bản dịch text
            p_trans = doc.add_paragraph()
            p_trans.add_run("Bản dịch / Phản hồi từ ChatGPT:\n").bold = True
            p_trans.add_run(res.get("gpt_translation", "Không có nội dung dịch."))
            doc.add_paragraph()

        doc.save(file_path)
        return file_path
