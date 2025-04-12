from PySide6.QtCore import QTranslator, Signal, QObject
from PySide6.QtWidgets import QApplication
from loguru import logger


LANGUAGE_MAP = {
    "zh_CN": "简体中文",
    "en_US": "English",
    "ja_JP": "日本語",
}

REVERSE_LANGUAGE_MAP = {v: k for k, v in LANGUAGE_MAP.items()}


class TranslatorManager(QObject):
    _instance = None
    language_changed = Signal(object)

    def __init__(self):
        super().__init__()
        if TranslatorManager._instance is not None:
            raise RuntimeError("Please use instance() method")
        self._translator = QTranslator()
        self._current_language = None
        self._app = QApplication.instance()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def switch_translator(self, language: str):
        if "_" in language:
            language_code = language
        else:
            language_code = REVERSE_LANGUAGE_MAP[language]
        if language_code == self._current_language:
            return True
        logger.debug(f"尝试切换到 {language_code}")
        self._app.removeTranslator(self._translator)

        if self._translator.load(f"{language_code}.qm", directory="i18n"):
            self._app.installTranslator(self._translator)
            self._current_language = language_code
            # self.language_changed.emit()
            return True
        else:
            return False

    def get_current_language(self):
        return self._current_language
