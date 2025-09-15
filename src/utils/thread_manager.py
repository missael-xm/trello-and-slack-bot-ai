# src/utils/thread_manager.py
import threading

class ThreadManager():
    """
    Maneja ejecución concurrente para que el webhook responda rápido
    mientras el procesamiento pesado ocurre en segundo plano.
    """
    def __init__(self) -> None:
        self.threads = []

    def add_thread(self, target, args=()):
        """Agrega una función para ejecutar en hilo"""
        thread = threading.Thread(target=target, args=args)
        self.threads.append(thread)

    def start_threads(self):
        """Inicia todos los hilos"""
        for thread in self.threads:
            thread.start()

    def wait_threads(self):
        """Espera que todos los hilos terminen (para testing)"""
        for thread in self.threads:
            thread.join()