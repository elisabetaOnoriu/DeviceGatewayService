import logging

class LoggerProvider:
    """Handles logging configuration for the application"""
    
    @staticmethod
    def configure() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
        )