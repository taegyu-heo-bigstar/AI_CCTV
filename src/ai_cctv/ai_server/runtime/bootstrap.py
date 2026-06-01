# AI server의 GUI 기반 점검 창을 띄우기 전 최소 의존성을 확인하는 파일입니다.
# PyQt5가 없으면 표준 라이브러리 tkinter로 설치 여부를 먼저 묻습니다.
# 사용자가 O를 누른 경우에만 PyQt5를 설치하고, X를 누르면 실행을 종료합니다.

import importlib
import importlib.util
import subprocess
import sys


def ensure_pyqt5_available(finder=None, ask_user=None, installer=None, stream=None):
    """PyQt5가 있는지 확인하고 없으면 설치 여부를 물은 뒤 필요한 조치를 수행합니다.

    인자:
        finder: PyQt5 설치 여부를 반환하는 검사 함수입니다.
        ask_user: 설치 여부를 사용자에게 묻는 함수입니다.
        installer: PyQt5 설치를 수행하는 함수입니다.
        stream: 오류 메시지를 출력할 스트림입니다.
    반환값:
        PyQt5가 준비되면 None을 반환합니다.
    """

    resolved_finder = finder or _is_pyqt5_available
    if resolved_finder():
        return

    resolved_ask_user = ask_user or _ask_install_pyqt5_with_tkinter
    if not resolved_ask_user():
        _print_bootstrap_error("PyQt5가 없어 AI server를 시작할 수 없습니다.", stream)
        raise SystemExit(1)

    resolved_installer = installer or _install_pyqt5
    try:
        resolved_installer()
    except RuntimeError as error:
        _show_bootstrap_error(str(error))
        _print_bootstrap_error(str(error), stream)
        raise SystemExit(1) from error

    importlib.invalidate_caches()
    if not resolved_finder():
        message = "PyQt5 설치 후에도 패키지를 찾을 수 없습니다."
        _show_bootstrap_error(message)
        _print_bootstrap_error(message, stream)
        raise SystemExit(1)


def _is_pyqt5_available():
    """현재 Python 환경에서 PyQt5 import 경로를 찾을 수 있는지 확인합니다.

    인자:
        없음.
    반환값:
        PyQt5를 찾으면 True, 아니면 False를 반환합니다.
    """

    return importlib.util.find_spec("PyQt5") is not None


def _ask_install_pyqt5_with_tkinter():
    """tkinter 창으로 PyQt5 자동 설치 여부를 사용자에게 묻습니다.

    인자:
        없음.
    반환값:
        사용자가 O를 누르면 True, X를 누르면 False를 반환합니다.
    """

    try:
        import tkinter as tk
    except Exception:
        return False

    selected = {"install": False}
    window = tk.Tk()
    window.title("AI server 실행 환경 점검")
    window.geometry("520x220")
    window.resizable(False, False)
    window.attributes("-topmost", True)

    label = tk.Label(
        window,
        text=(
            "AI server GUI 실행에 필요한 PyQt5가 없습니다.\n"
            "O를 누르면 자동 설치하고, X를 누르면 설치하지 않고 종료합니다."
        ),
        justify="left",
        wraplength=460,
        padx=20,
        pady=24,
    )
    label.pack(fill="x")

    button_frame = tk.Frame(window)
    button_frame.pack(fill="x", padx=20, pady=8)

    def choose_install():
        """사용자의 자동 설치 선택을 기록하고 창을 닫습니다.

        인자:
            없음.
        반환값:
            없음.
        """

        selected["install"] = True
        window.destroy()

    def choose_cancel():
        """사용자의 설치 거부 선택을 기록하고 창을 닫습니다.

        인자:
            없음.
        반환값:
            없음.
        """

        selected["install"] = False
        window.destroy()

    tk.Button(button_frame, text="X - 설치하지 않음", command=choose_cancel).pack(
        side="right",
        padx=6,
    )
    tk.Button(button_frame, text="O - 자동 설치", command=choose_install).pack(
        side="right",
        padx=6,
    )
    window.protocol("WM_DELETE_WINDOW", choose_cancel)
    window.mainloop()
    return selected["install"]


def _install_pyqt5():
    """현재 Python 실행 파일을 사용해 PyQt5를 pip로 설치합니다.

    인자:
        없음.
    반환값:
        설치가 성공하면 None을 반환합니다.
    """

    command = [sys.executable, "-m", "pip", "install", "PyQt5"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "PyQt5 자동 설치에 실패했습니다.\n"
            f"{completed.stderr or completed.stdout}"
        )


def _show_bootstrap_error(message):
    """bootstrap 단계의 오류를 가능한 경우 tkinter 메시지 창으로 표시합니다.

    인자:
        message: 사용자에게 표시할 오류 메시지입니다.
    반환값:
        없음.
    """

    try:
        from tkinter import messagebox
    except Exception:
        return
    messagebox.showerror("AI server 실행 환경 점검", message)


def _print_bootstrap_error(message, stream=None):
    """bootstrap 단계의 오류를 지정된 스트림 또는 표준 오류에 출력합니다.

    인자:
        message: 출력할 오류 메시지입니다.
        stream: 메시지를 출력할 스트림입니다.
    반환값:
        없음.
    """

    print(message, file=stream or sys.stderr)
