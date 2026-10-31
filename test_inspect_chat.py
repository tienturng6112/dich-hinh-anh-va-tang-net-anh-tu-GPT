import sys
import os
import base64
sys.stdout.reconfigure(encoding='utf-8')
from DrissionPage import ChromiumOptions, ChromiumPage

co = ChromiumOptions()
co.set_local_port(9555)
page = ChromiumPage(co)

print("Page URL:", page.url)

# Test finding generated image
js_find_img = """
const imgs = Array.from(document.querySelectorAll('img')).filter(i => {
    return (i.alt && i.alt.includes('Generated')) || 
           (i.src && i.src.startsWith('blob:')) ||
           (i.closest && i.closest('div[data-testid*="image"], button')) ||
           (i.parentElement && i.parentElement.querySelector('button'));
});

if (imgs.length === 0) return null;

// Lấy ảnh generated cuối cùng
const targetImg = imgs[imgs.length - 1];

return {
    alt: targetImg.alt || '',
    src: targetImg.src || '',
    width: targetImg.naturalWidth || targetImg.width,
    height: targetImg.naturalHeight || targetImg.height
};
"""

img_info = page.run_js(js_find_img)
print("Found img info:", img_info)

# Thử chuyển blob url sang base64 qua canvas hoặc fetch
js_blob_to_base64 = """
return (async () => {
    const imgs = Array.from(document.querySelectorAll('img')).filter(i => 
        (i.alt && i.alt.includes('Generated')) || (i.src && i.src.startsWith('blob:') && i.alt !== 'User attachment')
    );
    if (imgs.length === 0) return null;
    const img = imgs[imgs.length - 1];
    
    // Thử vẽ qua canvas trước vì tức thời và không bị CORS blob
    try {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const dataUrl = canvas.toDataURL('image/png');
        if (dataUrl && dataUrl.length > 500) {
            return dataUrl;
        }
    } catch (e) {
        console.error('Canvas error:', e);
    }

    try {
        const response = await fetch(img.src);
        const blob = await response.blob();
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
    } catch (e) {
        return null;
    }
})();
"""

b64_data = page.run_js(js_blob_to_base64)
if b64_data:
    print("Base64 fetched length:", len(b64_data))
    header, encoded = b64_data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    with open("test_output_generated.png", "wb") as f:
        f.write(img_bytes)
    print("Saved test_output_generated.png successfully! Size:", len(img_bytes), "bytes")
else:
    print("Could not fetch base64")
