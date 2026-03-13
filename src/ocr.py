import base64
import logging
from io import BytesIO

from PIL import Image
import pytesseract

from src.config import Config

logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = Config.get_tesseract_cmd()


def extract_text_from_base64(base64_string):
    """Base64 인코딩된 이미지를 OCR로 판독하여 텍스트를 반환한다."""
    if not base64_string:
        return ""

    try:
        pure_data = base64_string.split(",")[1] if "," in base64_string else base64_string
        image_bytes = base64.b64decode(pure_data)
        img = Image.open(BytesIO(image_bytes))

        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)

        return pytesseract.image_to_string(img, lang="eng").strip()
    except Exception as e:
        logger.warning("OCR 이미지 판독 실패: %s", e)
        return ""
