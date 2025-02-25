import qrcode
import logging
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import (
    GappedSquareModuleDrawer,
)
from qrcode.image.styles.colormasks import (
    RadialGradiantColorMask,
)
from pathlib import Path
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)


async def generate_qrcode(
    data: str,
    error_correction: int = qrcode.constants.ERROR_CORRECT_H,
    module_drawer=GappedSquareModuleDrawer(),
    color_mask=RadialGradiantColorMask(
        back_color=(255, 255, 255),
        center_color=(190, 20, 200),
        edge_color=(150, 0, 25),
    ),
    embedded_image_path: Optional[str] = str(
        Path(__file__).parent.parent / "services" / "ok.png"
    ),
) -> BytesIO:
    """
    Generate a styled QR code with optional customization.

    Args:
        data (str): Data to encode in the QR code
        error_correction (int, optional): QR code error correction level. Defaults to HIGH.
        module_drawer (ModuleDrawer, optional): Style of QR code modules. Defaults to GappedSquareModuleDrawer.
        color_mask (ColorMask, optional): Color gradient for QR code. Defaults to RadialGradiantColorMask.
        embedded_image_path (str, optional): Path to embedded image. Defaults to 'ok.png'.

    Returns:
        BytesIO: QR code image as a byte stream
    """
    try:
        r = qrcode.QRCode(error_correction=error_correction)
        r.add_data(data)

        img = r.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=color_mask,
            embeded_image_path=embedded_image_path,
        )

        # Save image to a BytesIO object
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        logger.info(f"QR code generated successfully for data: {data[:20]}...")
        return img_byte_arr

    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise
