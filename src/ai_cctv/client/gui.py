import os
import sys
from datetime import datetime

import cv2
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
from .video_worker import VideoWorker


os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", r"C:\qt_plugins")
os.environ.setdefault("QT_PLUGIN_PATH", r"C:\qt_plugins")


class CCTVMainWindow(QMainWindow):
    """PyQt control center for the AI CCTV client."""

    def __init__(self):
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
        self.use_vlm = True
        self.storage_root_path = ""
        self.ai_cctv_path = ""
        self.original_segment_seconds = 10

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Intelligent CCTV Control Center")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.btn_start = QPushButton("START")
        self.btn_start.setStyleSheet(
            "background-color: #166534; color: white; padding: 8px 20px; "
            "border-radius: 5px; font-weight: bold;"
        )
        self.btn_start.clicked.connect(self.start_video)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet(
            "background-color: #7f1d1d; color: white; padding: 8px 20px; "
            "border-radius: 5px; font-weight: bold;"
        )
        self.btn_stop.clicked.connect(self.stop_video)

        self.btn_setting = QPushButton("Settings")
        self.btn_setting.setStyleSheet(
            "background-color: #334155; color: white; padding: 8px 20px; "
            "border-radius: 5px; font-weight: bold;"
        )
        self.btn_setting.clicked.connect(self.open_settings)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)
        header_layout.addWidget(self.btn_setting)
        main_layout.addLayout(header_layout)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)
        main_layout.addLayout(body_layout)

        body_layout.addWidget(self._create_left_panel())
        body_layout.addWidget(self._create_center_panel(), stretch=1)
        body_layout.addWidget(self._create_right_panel())

    def _create_left_panel(self):
        panel = QFrame()
        panel.setFixedWidth(300)
        panel.setStyleSheet("background-color: #1e293b; border-radius: 10px;")

        layout = QVBoxLayout(panel)
        label = QLabel("Camera\nRTSP / LAN / USB input status")
        label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(label)

        self.cam_status = QLabel("CAM-01 - READY")
        self.cam_status.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #3b82f6; "
            "border-radius: 5px; padding: 15px; color: #facc15;"
        )
        layout.addWidget(self.cam_status)
        layout.addStretch()
        return panel

    def _create_center_panel(self):
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

        self.storage_label = QLabel(
            "Storage path\n"
            "No storage path selected.\n\n"
            "Select a location in Settings > Storage."
        )
        self.storage_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.storage_label)
        return panel

    def create_metric_box(self, value, label):
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
        if self.worker is not None:
            return

        self.worker = VideoWorker(
            source=self.video_source,
            use_vlm=self.use_vlm,
            ai_cctv_path=self.ai_cctv_path,
            original_segment_seconds=self.original_segment_seconds,
        )
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.metrics_ready.connect(self.update_metrics)
        self.worker.event_ready.connect(self.add_event)
        self.worker.start()

        self.cam_status.setText("CAM-01 - LIVE")
        self.cam_status.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #22c55e; "
            "border-radius: 5px; padding: 15px; color: #22c55e;"
        )

    def stop_video(self):
        if self.worker is not None:
            self.worker.stop()
            self.worker = None

        self.cam_status.setText("CAM-01 - STOPPED")
        self.cam_status.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #ef4444; "
            "border-radius: 5px; padding: 15px; color: #ef4444;"
        )

    def open_settings(self):
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
            if self.ai_cctv_path:
                self.storage_label.setText(
                    "Storage path\n"
                    f"{self.ai_cctv_path}\n\n"
                    "Subfolders\n"
                    "original_records\n"
                    "event_clips"
                )
            else:
                self.storage_label.setText(
                    "Storage path\n"
                    "No storage path selected.\n\n"
                    "Select a location in Settings > Storage."
                )

    def update_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def update_metrics(self, data):
        self.metric_current["value"].setText(str(data.get("current_objects", 0)))
        self.metric_total["value"].setText(str(data.get("tracked_total", 0)))

    def add_event(self, event):
        event_type = event.get("type", "unknown")
        person_id = event.get("person_id", "-")
        time_text = event.get("time", datetime.now().strftime("%H:%M:%S"))

        if event_type == "appear":
            self.appear_count += 1
            self.metric_appear["value"].setText(str(self.appear_count))
            desc = f"ID {person_id} appeared"
            color = "#22c55e"
        elif event_type == "disappear":
            self.disappear_count += 1
            self.metric_disappear["value"].setText(str(self.disappear_count))
            desc = f"ID {person_id} disappeared"
            color = "#f97316"
        elif event_type == "error":
            desc = event.get("message", "Error")
            color = "#ef4444"
        else:
            desc = f"ID {person_id} {event_type}"
            color = "#38bdf8"

        event_box = QFrame()
        event_box.setStyleSheet("background-color: #0f172a; border-radius: 5px;")
        layout = QVBoxLayout(event_box)

        time_label = QLabel(time_text)
        time_label.setStyleSheet(f"color: {color};")
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("font-size: 15px; font-weight: bold;")

        layout.addWidget(time_label)
        layout.addWidget(desc_label)
        self.event_list.insertWidget(0, event_box)

        if self.event_list.count() > 30:
            old_item = self.event_list.takeAt(30)
            if old_item and old_item.widget():
                old_item.widget().deleteLater()

    def closeEvent(self, event):
        self.stop_video()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = CCTVMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
