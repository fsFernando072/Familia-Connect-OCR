from paddleocr import PaddleOCR

# ==========================================
# OCR
# ==========================================

ocr = PaddleOCR(
    lang="pt",
    use_angle_cls=True,
    det_db_box_thresh=0.3,
    det_db_unclip_ratio=1.6,
    rec_algorithm="CRNN",
    use_space_char=True,
    show_log=False
)