from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QAudioDecoder, QAudioFormat


class WaveformGenerator(QObject):
    waveform_ready = Signal(list)
    TARGET_POINTS = 1200

    def __init__(self):
        super().__init__()

        self.decoder = QAudioDecoder()
        self.samples = []

        self.decoder.bufferReady.connect(
            self.process_buffer
        )

        self.decoder.finished.connect(
            self.decoding_finished
        )

    def generate(self, file_path):
        self.samples.clear()

        self.decoder.stop()
        self.decoder.setSource(QUrl.fromLocalFile(file_path))
        self.decoder.start()

    def process_buffer(self):
        while self.decoder.bufferAvailable():
            buffer = self.decoder.read()

            if not buffer.isValid():
                continue

            audio_format = buffer.format()
            sample_format = audio_format.sampleFormat()
            channel_count = audio_format.channelCount()

            data = buffer.constData()
            buffer_samples = []

            if sample_format == QAudioFormat.SampleFormat.Int16:
                samples = memoryview(data).cast("h")

                for sample in samples:
                    buffer_samples.append(sample / 32768.0)

            elif sample_format == QAudioFormat.SampleFormat.Int32:
                samples = memoryview(data).cast("i")

                for sample in samples:
                    buffer_samples.append(sample / 2147483648.0)

            elif sample_format == QAudioFormat.SampleFormat.Float:
                samples = memoryview(data).cast("f")

                for sample in samples:
                    buffer_samples.append(sample)

            elif sample_format == QAudioFormat.SampleFormat.UInt8:
                samples = memoryview(data).cast("B")

                for sample in samples:
                    buffer_samples.append(
                        (sample - 128) / 128.0
                    )

            mono_samples = self.convert_to_mono(
                buffer_samples,
                channel_count
            )

            self.samples.extend(mono_samples)

    def convert_to_mono(self, samples, channel_count):
        if channel_count <= 1:
            return samples

        mono_samples = []

        for i in range(0, len(samples), channel_count):
            frame = samples[i:i + channel_count]

            if frame:
                mono_samples.append(
                    sum(frame) / len(frame)
                )

        return mono_samples

    def downsample(self, samples):
        if len(samples) <= self.TARGET_POINTS:
            return samples

        points_per_bucket = len(samples) / self.TARGET_POINTS

        waveform = []

        for i in range(self.TARGET_POINTS):
            start = int(i * points_per_bucket)
            end = int((i + 1) * points_per_bucket)

            bucket = samples[start:end]

            if not bucket:
                continue

            minimum = min(bucket)
            maximum = max(bucket)

            waveform.append((minimum, maximum))

        return waveform

    def decoding_finished(self):
        waveform = self.downsample(self.samples)

        self.waveform_ready.emit(waveform)

    def release_source(self):
        self.decoder.stop()
        self.decoder.setSource(QUrl())
        self.samples.clear()