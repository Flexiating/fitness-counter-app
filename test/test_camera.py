import cv2

from app.utils.logger import get_logger


log = get_logger(__name__)


def main() -> int:
    """Manual camera diagnostic; press Q to exit."""
    capture = cv2.VideoCapture(0)
    log.info("Manual camera opened: %s", capture.isOpened())
    try:
        while capture.isOpened():
            available, frame = capture.read()
            if not available:
                log.warning("Manual camera frame unavailable")
                break
            cv2.imshow("Camera", frame)
            if cv2.waitKey(1) == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
