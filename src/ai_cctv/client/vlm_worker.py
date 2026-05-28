# vlm_worker.py 파일입니다.
# AI CCTV 프로젝트의 client 영역에서 사용하는 소스 코드입니다.
# 이 파일의 클래스와 함수 책임은 각 국문 docstring에 정리되어 있습니다.

# vlm_worker.py ?????.
# AI CCTV ????? client ???? ???? ?? ?????.
# ? ??? ???? ?? ??? ? ?? docstring? ???? ????.

# vlm_worker.py

import threading
import queue
import torch
import gc

from .vlm_person_analyzer_qwen_test import PersonAnalyzer
from .chat_bot import chat_bot as chatbot

class VLMWorker:
    """VLMWorker 클래스의 주요 책임을 수행합니다.
    
    인자:
        생성자 인자는 __init__ 문서를 따릅니다.
    반환값:
        VLMWorker 인스턴스를 반환합니다.
    """
    def __init__(self, state_manager):
        """__init__ 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.state_manager = state_manager
        self.task_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.analyzer = None

    def start(self):
        """start 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if self.thread is not None and self.thread.is_alive():
            print("VLM Worker 이미 실행 중")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def add_task(self, person_id, crop_path):
        """add_task 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if not self.running:
            return

        self.task_queue.put((person_id, crop_path))

    def _run(self):
        """_run 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        try:
            print("VLM 모델 로딩 중...")
            self.analyzer = PersonAnalyzer()
            print("VLM 모델 로딩 완료")
        except Exception as e:
            print(f"VLM 모델 로딩 실패: {e}")
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
                chatbot.send_msg(result)
                
            except Exception as e:
                print(f"ID {person_id} VLM 분석 실패: {e}")

            finally:
                self.task_queue.task_done()

        self.cleanup()

    def stop(self):
        """stop 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.running = False

        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=10)

        self.cleanup()

    def cleanup(self):
        """cleanup 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if self.analyzer is not None:
            try:
                del self.analyzer
            except Exception:
                pass

            self.analyzer = None

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
