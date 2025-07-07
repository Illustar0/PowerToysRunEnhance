import uuid

from PySide6.QtCore import QTimer, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from loguru import logger

from src.core.interfaces import IQApplication

SERVER_NAME = str(uuid.uuid5(uuid.NAMESPACE_DNS, "WindowsSearchUtility"))


class WSUApplication(IQApplication):
    messageReceived = Signal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self._server_name = SERVER_NAME
        self._socket = QLocalSocket()

        # 尝试连接到服务
        self._socket.connectToServer(self._server_name)

        if self._socket.waitForConnected(500):
            self._socket.write("show".encode("utf-8"))
            self._socket.flush()
            logger.error("Another instance of the application is already running.")
            self.is_running = True
            self.quit()
        else:
            self.is_running = False
            self._server = QLocalServer()
            # 确保即使应用崩溃，服务也能被正确移除
            self._server.removeServer(self._server_name)
            self._server.listen(self._server_name)
            self._server.newConnection.connect(self._on_new_connection)

    def _on_new_connection(self):
        client_socket = self._server.nextPendingConnection()
        if client_socket:
            # 使用 QTimer 延迟读取，确保数据已完全到达
            QTimer.singleShot(100, lambda: self._read_message(client_socket))

    def _read_message(self, socket):
        if socket.bytesAvailable() > 0:
            message = socket.readAll().data().decode("utf-8")
            logger.info(f"Received message: {message}")
            self.messageReceived.emit(message)
        socket.close()
