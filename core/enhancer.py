"""
Module xử lý làm nét và nâng cấp độ phân giải hình ảnh cao cấp (Ultra-HD Super-Resolution).
Hỗ trợ cả OpenCV chuyên sâu và Pillow:
- Khử nhiễu nén JPEG trước khi phóng lớn để tránh vỡ hạt
- Phóng lớn siêu phân giải 4x (Lanczos 4)
- Cân bằng tương phản thích nghi cục bộ CLAHE trong không gian màu LAB
- Tăng cường chi tiết vi mô (Computational Detail Enhance)
- Bộ lọc sắc cạnh đa tầng (Multi-scale Unsharp Masking + High-Pass Edge Kernel)
"""

import os
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class ImageEnhancer:
    def __init__(self):
        pass

    @staticmethod
    def enhance_pil(img: Image.Image, scale: float = 4.0, sharpness_factor: float = 2.5, contrast_factor: float = 1.2) -> Image.Image:
        """Làm nét ảnh bằng Pillow nâng cao (Lanczos upscale + UnsharpMask + Sharpness & Contrast Boost)"""
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        upscaled = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

        # Áp dụng Unsharp Mask đa tầng
        unsharped = upscaled.filter(ImageFilter.UnsharpMask(radius=3, percent=180, threshold=2))
        
        # Tăng cường độ nét chi tiết
        enhancer_sharp = ImageEnhance.Sharpness(unsharped)
        sharpened = enhancer_sharp.enhance(sharpness_factor)

        # Tăng nhẹ tương phản
        enhancer_contrast = ImageEnhance.Contrast(sharpened)
        enhanced = enhancer_contrast.enhance(contrast_factor)

        return enhanced

    @staticmethod
    def enhance_opencv(img: Image.Image, scale: float = 4.0, mode: str = "ultra") -> Image.Image:
        """
        Làm nét ảnh chuyên sâu Ultra-HD bằng OpenCV:
        1. Khử nhiễu nén JPEG
        2. Lanczos4 upscale 4x
        3. CLAHE cân bằng sáng & viền chữ
        4. DetailEnhance tăng cường chi tiết mắt, tóc, nếp gấp
        5. Unsharp masking + Edge kernel làm sắc cạnh
        """
        if not HAS_OPENCV:
            return ImageEnhancer.enhance_pil(img, scale=scale)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        np_img = np.array(img)
        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]

        # 1. Khử nhiễu nén JPEG nhẹ trước khi phóng lớn
        denoised = cv2.bilateralFilter(bgr, d=5, sigmaColor=25, sigmaSpace=25)

        # 2. Phóng lớn siêu phân giải (Lanczos4)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        upscaled = cv2.resize(denoised, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        # 3. Cân bằng tương phản thích nghi cục bộ CLAHE trong không gian màu LAB
        lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
        l, a, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b_channel))
        contrast_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # 4. Tăng cường chi tiết ảnh (Detail Enhance)
        detailed = cv2.detailEnhance(contrast_bgr, sigma_s=10, sigma_r=0.15)

        # 5. Unsharp Masking ma trận làm nét
        gaussian = cv2.GaussianBlur(detailed, (0, 0), 2.0)
        unsharp = cv2.addWeighted(detailed, 1.7, gaussian, -0.7, 0)

        # 6. Kernel làm nổi viền nét chi tiết (Text & Edge Enhancement)
        if mode == "text":
            edge_kernel = np.array([
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0]
            ], dtype=np.float32)
        else:
            edge_kernel = np.array([
                [0, -0.4, 0],
                [-0.4, 2.6, -0.4],
                [0, -0.4, 0]
            ], dtype=np.float32)

        sharpened = cv2.filter2D(unsharp, -1, edge_kernel)

        rgb_out = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_out)

    @classmethod
    def process_image(cls, input_path: str, output_path: str, scale: float = 4.0, mode: str = "ultra") -> str:
        """
        Hàm chính nhận file ảnh đầu vào, làm nét và lưu vào file đầu ra.
        Trả về đường dẫn file ảnh đã làm nét.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Không tìm thấy file ảnh: {input_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with Image.open(input_path) as img:
            if HAS_OPENCV:
                enhanced_img = cls.enhance_opencv(img, scale=scale, mode=mode)
            else:
                enhanced_img = cls.enhance_pil(img, scale=scale)

            # Lưu ảnh chất lượng tối đa
            ext = os.path.splitext(output_path)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                enhanced_img.save(output_path, 'JPEG', quality=98, subsampling=0)
            else:
                enhanced_img.save(output_path, 'PNG', optimize=True)

        return output_path
