from bot.helper.mirror_utils.download_status import DownloadStatus
from bot.helper.telegram_helper import message_utils
from bot.helper.ext_utils import bot_utils
from bot import DOWNLOAD_STATUS_UPDATE_INTERVAL
from .status_message import StatusMessage
import threading
import time


class ProgressUpdater:
    def __init__(self):
        # Key: StatusMessage.uid
        # Value: object of DownloadStatus
        self.downloads = {}

        # Key: StatusMessage.uid
        # Value: Object of StatusMessage
        # Stores messages to update
        self.messages = {}

        self.downloads_lock = threading.RLock()
        self.messages_lock = threading.RLock()
        self._thread = None

    def add_tracker(self, mirror: DownloadStatus, trackerMessage: StatusMessage):
        """
        :param mirror: The mirror request whose progress have to be tracked. Object of DownloadStatus
        :param trackerMessage: The message which have to be edited when a progress is detected. Object of StatusMessage
        :return It does not returns anything
        """
        with self.downloads_lock:
            self.downloads[trackerMessage.uid] = mirror
        with self.messages_lock:
            self.messages_lock = trackerMessage
        # If no thread is alive, create one and start updating
        if self._thread is None:
            self._thread = threading.Thread(target=self._update_progress())
            self._thread.start()

    def del_tracker(self, uid):
        with self.downloads_lock:
            del self.downloads[uid]
        with self.messages_lock:
            del self.messages[uid]

    def _edit_all_message(self, msg):
        for message in self.messages.values():
            message_utils.editMessage(msg, message.context, message.message)

    def _clear_mirrors(self):
        """
        This function deletes all the cancelled or finished mirrors from self.downloads
        """
        for key, download in self.downloads.items():
            if download.status() == bot_utils.MirrorStatus.STATUS_CANCELLED:
                del self.downloads[key]
            elif download.status == bot_utils.MirrorStatus.STATUS_FAILED:
                del self.downloads[key]

    def _check_mirror_finished(self):
        """
        Checks if any of the mirror is finished. Replies with the link if it has
        """
        for (key, download) in self.downloads.items():
            if download.link is not None:
                message_utils.sendMessage(download.link, self.messages[key].context, self.messages[key].update)
                self.del_tracker(key)

    def _update_progress(self):
        """It updates the messages in self.messages, with the progress of the mirror from self.downloads"""
        # Keep on running the loop until break is called
        while True:
            if len(self.downloads) == 0:
                with self.messages_lock:
                    for i in list(self.messages.values()):
                        message_utils.deleteMessage(i.context, i.message)
                break
            with self.downloads_lock:
                msg = bot_utils.get_readable_message(list(self.downloads.values()))
            self._clear_mirrors()
            self._check_mirror_finished()
            self._edit_all_message(msg)
            time.sleep(DOWNLOAD_STATUS_UPDATE_INTERVAL)