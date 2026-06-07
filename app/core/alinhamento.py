import cv2
import numpy as np

# ==========================================
# TEMPLATE (CARREGADO UMA VEZ)
# ==========================================

TEMPLATE_PATH = "app/templates/template-vazio.png"
template = cv2.imread(TEMPLATE_PATH)

if template is None:
    raise RuntimeError("Template não encontrado no container")

# ==========================================
# ALINHAMENTO ORB
# ==========================================

def alinhar_formulario(img):
    g1 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(4000)
    kp1, d1 = orb.detectAndCompute(g1, None)
    kp2, d2 = orb.detectAndCompute(g2, None)

    if d1 is None or d2 is None:
        return img

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = sorted(bf.match(d1, d2), key=lambda x: x.distance)[:200]

    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

    H, _ = cv2.findHomography(pts1, pts2, cv2.RANSAC)

    if H is None:
        return img

    h, w = template.shape[:2]
    return cv2.warpPerspective(img, H, (w, h))