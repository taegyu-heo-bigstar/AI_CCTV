# AI CCTV 메인 PyQt 창을 정의하는 파일입니다.
# 화면 구성, 사용자 조작, VideoWorker 신호 연결을 담당합니다.
# PyTorch는 server_run.py에서 PyQt보다 먼저 초기화하고 영상 작업자는 지연 import합니다.

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .settings_window import SettingsWindow
from .event_presenter import EventPresenter


os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", r"C:\qt_plugins")
os.environ.setdefault("QT_PLUGIN_PATH", r"C:\qt_plugins")


class CCTVMainWindow(QMainWindow):
    """AI CCTV 클라이언트의 메인 제어 창입니다.

    인자:
        없음.
    반환값:
        CCTVMainWindow 인스턴스를 반환합니다.
    """

    def __init__(self):
        """메인 창 상태와 UI를 초기화합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        super().__init__()
        self.setWindowTitle("Intelligent CCTV Control Center")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(
            "background-color: #0f172a; color: #f8fafc; font-family: Arial;"
        )

        self.worker = None
        self.appear_count = 0
        self.disappear_count = 0
        self.video_source = 0
        self.use_vlm = False
        self.storage_root_path = ""
        self.ai_cctv_path = ""
        self.original_segment_seconds = 10
        self.event_presenter = EventPresenter()

        self.init_ui()

    def init_ui(self):
        """메인 화면의 전체 레이아웃을 구성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        main_layout.addLayout(self._create_header_layout())

        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)
        main_layout.addLayout(body_layout)

        body_layout.addWidget(self._create_left_panel())
        body_layout.addWidget(self._create_center_panel(), stretch=1)
        body_layout.addWidget(self._create_right_panel())

    def _create_header_layout(self):
        """상단 제목과 제어 버튼 레이아웃을 생성합니다.

        인자:
            없음.
        반환값:
            QHBoxLayout 객체를 반환합니다.
        """

        header_layout = QHBoxLayout()
        title_label = QLabel("Intelligent CCTV Control Center")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.btn_start = self._create_button("START", "#166534")
        self.btn_start.clicked.connect(self.start_video)

        self.btn_stop = self._create_button("STOP", "#7f1d1d")
        self.btn_stop.clicked.connect(self.stop_video)

        self.btn_setting = self._create_button("Settings", "#334155")
        self.btn_setting.clicked.connect(self.open_settings)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)
        header_layout.addWidget(self.btn_setting)
        self._set_run_button_state(is_running=False)
        return header_layout

    def _create_button(self, text, background_color):
        """표준 스타일의 버튼을 생성합니다.

        인자:
            text: 버튼에 표시할 문자열입니다.
            background_color: 버튼 배경 색상 코드입니다.
        반환값:
            QPushButton 객체를 반환합니다.
        """

        button = QPushButton(text)
        button.setStyleSheet(
            f"background-color: {background_color}; color: white; "
            "padding: 8px 20px; border-radius: 5px; font-weight: bold;"
        )
        return button

    def _set_run_button_state(self, is_running):
        """영상 실행 상태에 맞춰 START와 STOP 버튼을 하이라이팅합니다.

        인자:
            is_running: 영상 작업자가 실행 중인지 여부입니다.
        반환값:
            없음.
        """

        self.btn_start.setStyleSheet(
            self._build_run_button_style("#166534", is_running)
        )
        self.btn_stop.setStyleSheet(
            self._build_run_button_style("#7f1d1d", not is_running)
        )

    def _build_run_button_style(self, background_color, is_active):
        """실행 상태 버튼의 활성/비활성 스타일을 생성합니다.

        인자:
            background_color: 버튼의 기본 배경 색상 코드입니다.
            is_active: 현재 상태와 일치해 강조할지 여부입니다.
        반환값:
            QPushButton에 적용할 스타일시트 문자열을 반환합니다.
        """

        if is_active:
            return (
                f"background-color: {background_color}; color: white; "
                "padding: 8px 20px; border-radius: 5px; font-weight: bold; "
                "border: 2px solid #facc15;"
            )

        return (
            "background-color: #334155; color: #cbd5e1; "
            "padding: 8px 20px; border-radius: 5px; font-weight: bold; "
            "border: 1px solid #475569;"
        )

    def _create_left_panel(self):
        """카메라 입력 상태 패널을 생성합니다.

        인자:
            없음.
        반환값:
            QFrame 객체를 반환합니다.
        """

        panel = QFrame()
        panel.setFixedWidth(300)
        panel.setStyleSheet("background-color: #1e293b; border-radius: 10px;")

        layout = QVBoxLayout(panel)
        label = QLabel("Camera\nRTSP / LAN / USB input status")
        label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(label)

        self.cam_status = QLabel("CAM-01 - READY")
        self._set_camera_status_style("#3b82f6", "#facc15")
        layout.addWidget(self.cam_status)
        layout.addStretch()
        return panel

    def _create_center_panel(self):
        """실시간 영상과 지표 패널을 생성합니다.

        인자:
            없음.
        반환값:
            QFrame 객체를 반환합니다.
        """

        panel = QFrame()
        panel.setStyleSheet("background-color: #1e293b; border-radius: 10px;")
        layout = QVBoxLayout(panel)

        title = QLabel("CAM-01 live analysis")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.video_label = QLabel("LIVE VIDEO SURFACE")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "background-color: #0f172a; border-radius: 5px; "
            "font-size: 24px; color: #334155; font-weight: bold;"
        )
        self.video_label.setMinimumSize(800, 450)
        layout.addWidget(self.video_label, stretch=1)

        metrics_layout = QHBoxLayout()
        self.metric_current = self.create_metric_box("0", "Current")
        self.metric_total = self.create_metric_box("0", "Tracked")
        self.metric_appear = self.create_metric_box("0", "Appear")
        self.metric_disappear = self.create_metric_box("0", "Disappear")

        for metric in [
            self.metric_current,
            self.metric_total,
            self.metric_appear,
            self.metric_disappear,
        ]:
            metrics_layout.addWidget(metric["box"])

        layout.addLayout(metrics_layout)
        return panel

    def _create_right_panel(self):
        """이벤트 타임라인과 저장 경로 패널을 생성합니다.

        인자:
            없음.
        반환값:
            QFrame 객체를 반환합니다.
        """

        panel = QFrame()
        panel.setFixedWidth(350)
        panel.setStyleSheet("background-color: #1e293b; border-radius: 10px;")

        layout = QVBoxLayout(panel)
        label = QLabel("Event timeline\nAppear / Move / Disappear / VLM")
        label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        scroll_widget = QWidget()
        self.event_list = QVBoxLayout(scroll_widget)
        self.event_list.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        layout.addStretch()

        self.storage_label = QLabel(self._build_storage_label())
        self.storage_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.storage_label)
        return panel

    def create_metric_box(self, value, label):
        """지표 숫자와 라벨을 담는 UI 박스를 생성합니다.

        인자:
            value: 초기 지표 값 문자열입니다.
            label: 지표 이름 문자열입니다.
        반환값:
            박스와 내부 라벨들을 담은 딕셔너리를 반환합니다.
        """

        box = QFrame()
        box.setStyleSheet("background-color: #0f172a; border-radius: 5px;")
        layout = QVBoxLayout(box)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        text_label = QLabel(label)
        text_label.setStyleSheet("color: #94a3b8;")

        layout.addWidget(value_label)
        layout.addWidget(text_label)
        return {"box": box, "value": value_label, "label": text_label}

    def start_video(self):
        """영상 처리 작업자를 시작하고 신호를 연결합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.worker is not None:
            return

        try:
            from ..analysis.video_worker import VideoWorker

            worker = VideoWorker(
                source=self.video_source,
                use_vlm=self.use_vlm,
                ai_cctv_path=self.ai_cctv_path,
                original_segment_seconds=self.original_segment_seconds,
            )
        except Exception as exc:
            self._handle_video_start_failure(exc)
            return

        self.worker = worker
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.metrics_ready.connect(self.update_metrics)
        self.worker.event_ready.connect(self.add_event)
        self.worker.start()

        self.cam_status.setText("CAM-01 - LIVE")
        self._set_camera_status_style("#22c55e", "#22c55e")
        self._set_run_button_state(is_running=True)

    def stop_video(self):
        """영상 처리 작업자를 중지하고 카메라 상태를 갱신합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.worker is not None:
            self.worker.stop()
            self.worker = None

        self.cam_status.setText("CAM-01 - STOPPED")
        self._set_camera_status_style("#ef4444", "#ef4444")
        self._set_run_button_state(is_running=False)

    def open_settings(self):
        """설정 창을 열고 적용된 값을 메인 창 상태에 반영합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        dialog = SettingsWindow(
            self,
            video_source=self.video_source,
            use_vlm=self.use_vlm,
            storage_root_path=self.storage_root_path,
            ai_cctv_path=self.ai_cctv_path,
            original_segment_seconds=self.original_segment_seconds,
        )

        if dialog.exec_():
            self.video_source = dialog.selected_source
            self.use_vlm = dialog.use_vlm
            self.storage_root_path = dialog.storage_root_path
            self.ai_cctv_path = dialog.ai_cctv_path
            self.original_segment_seconds = dialog.original_segment_seconds

            self.cam_status.setText(f"CAM-01 - INPUT SET: {self.video_source}")
            self.storage_label.setText(self._build_storage_label())

    def update_frame(self, frame):
        """OpenCV 프레임을 PyQt 이미지로 변환해 화면에 표시합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
        반환값:
            없음.
        """

        import cv2

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        qt_img = QImage(
            rgb_frame.data,
            width,
            height,
            channels * width,
            QImage.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def update_metrics(self, data):
        """영상 처리 지표를 화면에 반영합니다.

        인자:
            data: current_objects와 tracked_total 값을 담은 딕셔너리입니다.
        반환값:
            없음.
        """

        self.metric_current["value"].setText(str(data.get("current_objects", 0)))
        self.metric_total["value"].setText(str(data.get("tracked_total", 0)))

    def add_event(self, event):
        """이벤트 타임라인에 새 이벤트 항목을 추가합니다.

        인자:
            event: 이벤트 유형, 인물 ID, 시간 등을 담은 딕셔너리입니다.
        반환값:
            없음.
        """

        display = self.event_presenter.build_display(event)
        if display.event_type == "appear":
            self.appear_count += 1
            self.metric_appear["value"].setText(str(self.appear_count))
        elif display.event_type == "disappear":
            self.disappear_count += 1
            self.metric_disappear["value"].setText(str(self.disappear_count))

        event_box = QFrame()
        event_box.setStyleSheet("background-color: #0f172a; border-radius: 5px;")
        layout = QVBoxLayout(event_box)

        time_label = QLabel(self.event_presenter.get_time_text(event))
        time_label.setStyleSheet(f"color: {display.color};")
        desc_label = QLabel(display.description)
        desc_label.setStyleSheet("font-size: 15px; font-weight: bold;")

        layout.addWidget(time_label)
        layout.addWidget(desc_label)
        self.event_list.insertWidget(0, event_box)
        self._trim_event_list()

    def closeEvent(self, event):
        """창 닫힘 이벤트에서 작업자를 정리합니다.

        인자:
            event: PyQt 닫힘 이벤트 객체입니다.
        반환값:
            없음.
        """

        self.stop_video()
        event.accept()

    def _set_camera_status_style(self, border_color, text_color):
        """카메라 상태 라벨의 색상을 설정합니다.

        인자:
            border_color: 라벨 테두리 색상 코드입니다.
            text_color: 라벨 텍스트 색상 코드입니다.
        반환값:
            없음.
        """

        self.cam_status.setStyleSheet(
            "background-color: #0f172a; "
            f"border: 1px solid {border_color}; "
            "border-radius: 5px; padding: 15px; "
            f"color: {text_color};"
        )

    def _handle_video_start_failure(self, error):
        """영상 처리 작업자 시작 실패를 화면 상태와 이벤트로 표시합니다.

        인자:
            error: 영상 시작 중 발생한 예외 객체입니다.
        반환값:
            없음.
        """

        message = f"영상 시작 실패: {error}"
        print(message)
        self.worker = None
        self.cam_status.setText("CAM-01 - ERROR")
        self._set_camera_status_style("#ef4444", "#ef4444")
        self._set_run_button_state(is_running=False)
        self.add_event({
            "type": "error",
            "message": message,
        })

    def _build_storage_label(self):
        """저장 경로 패널에 표시할 문자열을 생성합니다.

        인자:
            없음.
        반환값:
            저장 경로 안내 문자열을 반환합니다.
        """

        if self.ai_cctv_path:
            return (
                "Storage path\n"
                f"{self.ai_cctv_path}\n\n"
                "Subfolders\n"
                "original_records\n"
                "event_clips"
            )
        return (
            "Storage path\n"
            "No storage path selected.\n\n"
            "Select a location in Settings > Storage."
        )

    def _trim_event_list(self, max_events=30):
        """이벤트 타임라인의 최대 표시 개수를 제한합니다.

        인자:
            max_events: 화면에 남길 최대 이벤트 수입니다.
        반환값:
            없음.
        """

        if self.event_list.count() <= max_events:
            return

        old_item = self.event_list.takeAt(max_events)
        if old_item and old_item.widget():
            old_item.widget().deleteLater()


def main():
    """AI CCTV PyQt 애플리케이션을 실행합니다.

    인자:
        없음.
    반환값:
        정상적으로는 반환하지 않고 Qt 이벤트 루프 종료 코드를 사용합니다.
    """

    app = QApplication(sys.argv)
    window = CCTVMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
