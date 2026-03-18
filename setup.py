from setuptools import setup, find_packages

setup(
    name="whisper-transcriber",
    version="1.1.0",
    description="Cross-platform GUI for video transcription using OpenAI Whisper",
    author="WhisperTranscriber",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "openai-whisper>=20250625",
        "PyQt6>=6.10.0",
        "torch>=2.10.0",
    ],
    entry_points={
        "console_scripts": [
            "whisper-transcriber=src.main:main",
        ],
    },
)
