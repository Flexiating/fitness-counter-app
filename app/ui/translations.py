"""Vietnamese labels and display-only translations for the interface."""

EXERCISE_NAMES = {
    "Push Up": "Chống đẩy",
    "Crunch": "Gập bụng",
}

STATE_NAMES = {
    "INITIALIZING": "Đang khởi tạo",
    "NO PERSON": "Chưa phát hiện người",
    "WAITING": "Đang chờ",
    "UP": "LÊN",
    "DOWN": "XUỐNG",
    "READY": "SẴN SÀNG",
    "RUNNING": "ĐANG TẬP",
    "PAUSED": "ĐÃ TẠM DỪNG",
    "FINISHED": "ĐÃ HOÀN THÀNH",
}

JOINT_NAMES = {
    "Left elbow": "Khuỷu tay trái",
    "Right elbow": "Khuỷu tay phải",
    "Left shoulder": "Vai trái",
    "Right shoulder": "Vai phải",
    "Left hip": "Hông trái",
    "Right hip": "Hông phải",
    "Left knee": "Gối trái",
    "Right knee": "Gối phải",
}

STATUS_TEXT = {
    "Opening camera": "Đang mở camera",
    "Loading pose detector": "Đang tải bộ nhận diện tư thế",
    "Ready": "Sẵn sàng",
    "No person detected": "Chưa phát hiện người",
    "Camera frame unavailable. Check the camera connection.": "Không nhận được hình ảnh từ camera. Hãy kiểm tra kết nối camera.",
    "Camera unavailable. Check the connection and camera permission.": "Không thể sử dụng camera. Hãy kiểm tra kết nối và quyền truy cập camera.",
    "Pose model failed to load. Restart the app or reinstall the dependencies.": "Không tải được mô hình tư thế. Hãy khởi động lại ứng dụng hoặc cài lại thư viện.",
    "Camera processing stopped unexpectedly. Press Start Camera to retry.": "Xử lý camera đã dừng ngoài dự kiến. Hãy nhấn Bật camera để thử lại.",
    "Exercise module failed": "Không tải được mô-đun bài tập",
    "Details": "Chi tiết",
    "Move into camera view": "Hãy di chuyển vào khung hình camera",
    "Move farther from the camera": "Hãy lùi xa camera hơn",
    "Posture: GOOD": "Tư thế: TỐT",
    "Posture: BAD": "Tư thế: CHƯA ĐÚNG",
    "Movement between thresholds": "Chuyển động chưa đủ biên độ",
    "Body not visible": "Không nhìn thấy rõ cơ thể",
    "Only one arm detected or body not visible": "Chỉ phát hiện một tay hoặc không thấy rõ cơ thể",
    "Hips too high or too low": "Hông quá cao hoặc quá thấp",
    "Not in plank position (standing or walking)": "Chưa ở tư thế plank (đang đứng hoặc đi lại)",
    "Body not visible or tracking lost": "Không thấy rõ cơ thể hoặc mất theo dõi",
    "Standing, sitting, walking, or body rotated": "Đang đứng, ngồi, đi lại hoặc cơ thể xoay quá nhiều",
    "Partial crunch ignored": "Bỏ qua lần gập bụng chưa đủ biên độ",
    "Rep rejected: too fast": "Lần lặp bị bỏ qua: quá nhanh",
    "OK": "Ổn",
}


def translate_exercise(name: str) -> str:
    return EXERCISE_NAMES.get(name, name)


def translate_state(state: str) -> str:
    return STATE_NAMES.get(state, state)


def translate_status(status: str) -> str:
    translated = status
    for source, target in STATUS_TEXT.items():
        translated = translated.replace(source, target)
    return translated


def translate_joint(name: str) -> str:
    return JOINT_NAMES.get(name, name)


def translate_debug(text: str) -> str:
    """Translate display text without changing the exercise counters' data."""
    replacements = {
        "Push-up debug": "Gỡ lỗi chống đẩy",
        "state": "trạng thái",
        "last transition": "chuyển trạng thái gần nhất",
        "thresholds": "ngưỡng",
        "down": "xuống",
        "up": "lên",
        "hip tolerance": "dung sai hông",
        "rejected": "bị từ chối",
        "none": "không có",
        "Joint angles": "Góc khớp",
        "no pose detected": "chưa phát hiện tư thế",
    }
    translated = translate_status(text)
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    for source, target in JOINT_NAMES.items():
        translated = translated.replace(source, target)
    for source, target in STATE_NAMES.items():
        translated = translated.replace(source, target)
    return translated
