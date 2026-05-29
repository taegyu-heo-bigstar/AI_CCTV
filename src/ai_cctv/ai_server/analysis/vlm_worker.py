# AI CCTV VLM 분석 작업자 파일입니다.
# 전신 crop 이미지 분석 요청을 비동기 큐로 처리합니다.
# 모델 준비 성공/실패 상태를 외부 작업자가 확인할 수 있게 제공합니다.

import gc
import queue
import threading


class VLMWorker:
    """VLM 모델 로딩과 crop 이미지 분석 작업을 관리합니다.

    인자:
        state_manager: 인물별 VLM 완료 상태를 기록하는 상태 관리자입니다.
    반환값:
        VLMWorker 인스턴스를 반환합니다.
    """

    def __init__(self, state_manager):
        """VLM 작업 큐와 준비 상태 이벤트를 초기화합니다.

        인자:
            state_manager: 인물별 상태를 관리하는 객체입니다.
        반환값:
            없음.
        """

        self.state_manager = state_manager
        self.task_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.analyzer = None
        self.ready_event = threading.Event()
        self.failed_event = threading.Event()
        self.error_message = None

    def start(self):
        """VLM 모델 로딩과 분석 큐 처리를 위한 thread를 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.thread is not None and self.thread.is_alive():
            print("VLM Worker 이미 실행 중")
            return

        self.ready_event.clear()
        self.failed_event.clear()
        self.error_message = None
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def is_ready(self):
        """VLM 모델이 분석 가능한 상태인지 반환합니다.

        인자:
            없음.
        반환값:
            준비가 끝났으면 True, 아니면 False를 반환합니다.
        """

        return self.ready_event.is_set()

    def has_failed(self):
        """VLM 모델 로딩이 실패했는지 반환합니다.

        인자:
            없음.
        반환값:
            실패 상태이면 True, 아니면 False를 반환합니다.
        """

        return self.failed_event.is_set()

    def wait_until_ready(self, timeout=0.1):
        """지정 시간 동안 VLM 준비 완료를 기다립니다.

        인자:
            timeout: 준비 완료를 기다릴 최대 초 단위 시간입니다.
        반환값:
            제한 시간 안에 준비되면 True, 아니면 False를 반환합니다.
        """

        return self.ready_event.wait(timeout=timeout)

    def add_task(self, person_id, crop_path):
        """VLM 분석 큐에 인물 crop 이미지를 등록합니다.

        인자:
            person_id: 추적 인물 식별자입니다.
            crop_path: 분석할 crop 이미지 경로입니다.
        반환값:
            없음.
        """

        if not self.running or not self.is_ready():
            return

        self.task_queue.put((person_id, crop_path))

    def _run(self):
        """VLM 모델을 로딩하고 큐에 등록된 분석 작업을 반복 처리합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        try:
            print("VLM 모델 로딩 중...")
            from .vlm_person_analyzer import PersonAnalyzer

            self.analyzer = PersonAnalyzer()
            print("VLM 모델 로딩 완료")
            self.ready_event.set()
        except Exception as error:
            print(f"VLM 모델 로딩 실패: {error}")
            self.error_message = str(error)
            self.failed_event.set()
            self.running = False
            return

        while self.running:
            try:
                person_id, crop_path = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                print(f"ID {person_id} VLM 분석 시작: {crop_path}")
                result = self.analyzer.analyze(crop_path)
                self.state_manager.mark_vlm_done(person_id, result)

                print(f"ID {person_id} VLM 분석 결과:")
                print(result)
                from ..alerts.chat_bot import chat_bot as chatbot

                chatbot.send_msg(result)
            except Exception as error:
                print(f"ID {person_id} VLM 분석 실패: {error}")
            finally:
                self.task_queue.task_done()

        self.cleanup()

    def stop(self):
        """VLM 분석 thread를 중지하고 모델 자원을 정리합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.running = False

        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=10)

        self.cleanup()

    def cleanup(self):
        """VLM 분석기와 GPU 캐시 자원을 해제합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.analyzer is not None:
            try:
                del self.analyzer
            except Exception:
                pass

            self.analyzer = None

        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
