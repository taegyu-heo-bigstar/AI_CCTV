# AI server 실행 전 패키지와 모델 준비 상태를 표시하는 PyQt 대화상자입니다.
# 누락 항목이 있으면 사용자가 O 또는 X 버튼으로 자동 설치 여부를 결정합니다.
# O를 누르면 pip 설치와 모델 다운로드를 순차 수행하고 다시 점검합니다.
# X를 누르면 설치하지 않고 AI server 실행을 중단합니다.

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ..runtime import RuntimeEnvironmentChecker, RuntimeInstaller


class RuntimeReadinessDialog(QDialog):
    """AI server 실행에 필요한 패키지와 모델 누락 항목을 표시하고 설치 여부를 묻습니다.

    인자:
        report: 런타임 점검 결과입니다.
        checker: 설치 후 재검사에 사용할 RuntimeEnvironmentChecker 객체입니다.
        installer: 자동 설치를 수행할 RuntimeInstaller 객체입니다.
        parent: 부모 PyQt 위젯입니다.
    반환값:
        RuntimeReadinessDialog 인스턴스를 반환합니다.
    """

    def __init__(self, report, checker=None, installer=None, parent=None):
        """런타임 준비 상태 대화상자의 상태와 UI를 초기화합니다.

        인자:
            report: 런타임 점검 결과입니다.
            checker: 설치 후 재검사에 사용할 RuntimeEnvironmentChecker 객체입니다.
            installer: 자동 설치를 수행할 RuntimeInstaller 객체입니다.
            parent: 부모 PyQt 위젯입니다.
        반환값:
            없음.
        """

        super().__init__(parent)
        self.report = report
        self.checker = checker or RuntimeEnvironmentChecker()
        self.installer = installer or RuntimeInstaller()
        self.setWindowTitle("AI server 실행 환경 점검")
        self.setMinimumSize(760, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(
            "QDialog { background-color: #0f172a; color: #f8fafc; } "
            "QTextEdit { background-color: #111827; color: #e5e7eb; "
            "border: 1px solid #334155; border-radius: 4px; padding: 8px; } "
            "QLabel { color: #e5e7eb; }"
        )
        self._build_ui()

    def _build_ui(self):
        """대화상자의 안내문, 결과 영역, O/X 버튼을 구성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title_label = QLabel("필요한 패키지와 모델이 누락되었습니다")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        guide_label = QLabel(
            "O를 누르면 누락 항목을 자동으로 설치하거나 다운로드합니다. "
            "X를 누르면 설치하지 않고 AI server 실행을 종료합니다."
        )
        guide_label.setWordWrap(True)
        guide_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(guide_label)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setText(self._build_report_text())
        layout.addWidget(self.report_text, stretch=1)

        self.status_label = QLabel("선택 대기 중입니다.")
        self.status_label.setStyleSheet("color: #facc15; font-weight: bold;")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = self._create_button("X - 설치하지 않음", "#7f1d1d")
        self.cancel_button.clicked.connect(self.reject)
        self.install_button = self._create_button("O - 자동 설치", "#166534")
        self.install_button.clicked.connect(self.install_and_recheck)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.install_button)
        layout.addLayout(button_layout)

    def _create_button(self, text, background_color):
        """대화상자에서 사용할 버튼을 생성합니다.

        인자:
            text: 버튼에 표시할 문자열입니다.
            background_color: 버튼 배경 색상 코드입니다.
        반환값:
            QPushButton 객체를 반환합니다.
        """

        button = QPushButton(text)
        button.setStyleSheet(
            f"background-color: {background_color}; color: white; "
            "padding: 9px 20px; border-radius: 5px; font-weight: bold;"
        )
        return button

    def install_and_recheck(self):
        """누락 항목 자동 설치를 수행하고 다시 준비 상태를 검사합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.install_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("자동 설치를 진행하는 중입니다. 시간이 걸릴 수 있습니다.")
        QApplication.processEvents()

        try:
            logs = self.installer.install_missing(self.report.missing_required())
        except Exception as error:
            self.status_label.setText("자동 설치 실패")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            QMessageBox.critical(self, "자동 설치 실패", str(error))
            self.install_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            return

        self.report = self.checker.check()
        self.report_text.setText(self._build_report_text(logs))
        if self.report.is_ready():
            self.status_label.setText("실행 환경 준비가 완료되었습니다.")
            self.status_label.setStyleSheet("color: #22c55e; font-weight: bold;")
            QApplication.processEvents()
            self.accept()
            return

        self.status_label.setText("일부 항목이 여전히 누락되어 있습니다.")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        self.install_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def _build_report_text(self, logs=None):
        """점검 결과와 설치 로그를 표시용 문자열로 생성합니다.

        인자:
            logs: 자동 설치 결과 로그 목록입니다.
        반환값:
            표시용 문자열을 반환합니다.
        """

        lines = [self.report.to_text()]
        if logs:
            lines.append("")
            lines.append("[자동 설치 로그]")
            lines.extend(logs)
        return "\n".join(lines)


def ensure_runtime_readiness(parent=None, checker=None, installer=None):
    """AI server 런타임 요구사항을 검사하고 누락 시 설치 여부를 묻습니다.

    인자:
        parent: 부모 PyQt 위젯입니다.
        checker: 런타임 점검 객체입니다.
        installer: 자동 설치 객체입니다.
    반환값:
        실행 준비가 완료되면 True, 사용자가 설치하지 않으면 False를 반환합니다.
    """

    resolved_checker = checker or RuntimeEnvironmentChecker()
    report = resolved_checker.check()
    if report.is_ready():
        return True

    dialog = RuntimeReadinessDialog(
        report,
        checker=resolved_checker,
        installer=installer or RuntimeInstaller(),
        parent=parent,
    )
    return dialog.exec_() == QDialog.Accepted
