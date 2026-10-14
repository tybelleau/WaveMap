from pathlib import Path

from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QObject, QUrl, QTimer, Signal

class AudioPlayer(QObject):
    def __init__(self):
        super().__init__()

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()

        self.player.setAudioOutput(self.audio_output)

    def play_file(self, file_path):
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(file_path)))
        self.player.play()

    def release_source(self):
        self.player.stop()
        self.player.setSource(QUrl())

    def toggle_playback(self):
        state = self.player.playbackState()

        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()

        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()

        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.player.setPosition(0)
            self.player.play()

    def set_looping(self, enabled):
        if enabled:
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
        else:
            self.player.setLoops(QMediaPlayer.Loops.Once)

    def seek(self, position):
        self.player.setPosition(position)


class DurationReader(QObject):
    duration_ready = Signal(str, int)
    progress_changed = Signal(int, int)

    def __init__(self):
        super().__init__()

        self.player = QMediaPlayer()
        self.files = []
        self.index = 0
        self.file_path = None

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.timed_out)

        self.player.durationChanged.connect(self.duration_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)

    def read_files(self, file_paths):
        self.timer.stop()
        self.files = list(file_paths)
        self.index = 0
        self.file_path = None
        self.progress_changed.emit(0, len(self.files))
        self.read_next()

    def read_next(self):
        if self.index >= len(self.files):
            self.timer.stop()
            self.file_path = None
            self.player.setSource(QUrl())
            return

        self.file_path = str(self.files[self.index])
        self.index += 1
        self.player.setSource(QUrl.fromLocalFile(self.file_path))
        self.timer.start()

    def duration_changed(self, duration):
        if duration <= 0 or self.file_path is None:
            return

        source = self.player.source().toLocalFile()

        if Path(source) != Path(self.file_path):
            return

        self.finish_current(duration)

    def media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.finish_current(0)

    def timed_out(self):
        self.finish_current(0)

    def finish_current(self, duration):
        if self.file_path is None:
            return

        self.timer.stop()
        path = self.file_path
        self.file_path = None
        self.duration_ready.emit(path, duration)
        self.progress_changed.emit(self.index, len(self.files))
        QTimer.singleShot(0, self.read_next)