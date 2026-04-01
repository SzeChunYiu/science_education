"""Tests for src/style_learner/data_collection/ modules.

All external dependencies (yt-dlp, ffmpeg, scenedetect) are mocked.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# playlist_fetcher tests
# ---------------------------------------------------------------------------


class TestFetchPlaylistMetadata:
    """Test fetch_playlist_metadata with mocked subprocess."""

    def test_fetch_playlist_metadata(self):
        """Mock subprocess.run for yt-dlp, verify parsed output."""
        from src.style_learner.data_collection.playlist_fetcher import (
            fetch_playlist_metadata,
        )

        fake_stdout = "\n".join(
            [
                json.dumps(
                    {
                        "id": "abc123",
                        "title": "Video One",
                        "duration": 300,
                        "view_count": 1000,
                    }
                ),
                json.dumps(
                    {
                        "id": "def456",
                        "title": "Video Two",
                        "duration": 420,
                        "view_count": 2000,
                    }
                ),
            ]
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_stdout
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            videos = fetch_playlist_metadata("https://youtube.com/playlist?list=PL123")

        assert len(videos) == 2
        assert videos[0]["video_id"] == "abc123"
        assert videos[0]["title"] == "Video One"
        assert videos[0]["duration"] == 300
        assert videos[1]["video_id"] == "def456"
        assert "youtube.com/watch?v=def456" in videos[1]["url"]

        # Verify yt-dlp was called with correct args
        call_args = mock_run.call_args[0][0]
        assert "yt-dlp" in call_args
        assert "--dump-json" in call_args
        assert "--flat-playlist" in call_args

    def test_fetch_playlist_metadata_empty_on_failure(self):
        """yt-dlp returning nonzero should produce empty list."""
        from src.style_learner.data_collection.playlist_fetcher import (
            fetch_playlist_metadata,
        )

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "some error"

        with patch("subprocess.run", return_value=mock_result):
            videos = fetch_playlist_metadata("https://youtube.com/playlist?list=BAD")

        assert videos == []

    def test_fetch_playlist_metadata_skips_entries_without_id(self):
        """Entries missing 'id' should be skipped."""
        from src.style_learner.data_collection.playlist_fetcher import (
            fetch_playlist_metadata,
        )

        fake_stdout = "\n".join(
            [
                json.dumps({"title": "No ID video"}),
                json.dumps({"id": "good1", "title": "Good"}),
            ]
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_stdout
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            videos = fetch_playlist_metadata("https://youtube.com/playlist?list=PL1")

        assert len(videos) == 1
        assert videos[0]["video_id"] == "good1"


class TestFetchAllPlaylists:
    """Test fetch_all_playlists deduplication logic."""

    def test_fetch_all_playlists_deduplicates(self, tmp_path):
        """Duplicate video_ids across playlists are removed."""
        from src.style_learner.data_collection.playlist_fetcher import (
            fetch_all_playlists,
        )

        playlists_file = tmp_path / "playlists.txt"
        playlists_file.write_text(
            "https://youtube.com/playlist?list=PL1\n"
            "https://youtube.com/playlist?list=PL2\n"
        )

        # Both playlists contain video "dup1"
        call_count = 0

        def fake_fetch(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [
                    {"video_id": "dup1", "title": "Dup", "duration": 100, "view_count": 10, "url": "u1"},
                    {"video_id": "unique1", "title": "U1", "duration": 200, "view_count": 20, "url": "u2"},
                ]
            else:
                return [
                    {"video_id": "dup1", "title": "Dup Again", "duration": 100, "view_count": 10, "url": "u3"},
                    {"video_id": "unique2", "title": "U2", "duration": 300, "view_count": 30, "url": "u4"},
                ]

        with patch(
            "src.style_learner.data_collection.playlist_fetcher.fetch_playlist_metadata",
            side_effect=fake_fetch,
        ), patch(
            "src.style_learner.data_collection.playlist_fetcher.DATA_DIR",
            tmp_path / "data",
        ):
            unique = fetch_all_playlists(playlists_file)

        assert len(unique) == 3
        ids = [v["video_id"] for v in unique]
        assert ids.count("dup1") == 1


# ---------------------------------------------------------------------------
# transcript_extractor tests
# ---------------------------------------------------------------------------


class TestParseVttToWords:
    """Test VTT parsing into word-level timestamps."""

    def test_parse_vtt_to_words(self, tmp_path):
        """Provide sample VTT text, verify word timestamps."""
        from src.style_learner.data_collection.transcript_extractor import (
            parse_vtt_to_words,
        )

        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world today

00:00:05.000 --> 00:00:07.000
We learn science
"""
        vtt_path = tmp_path / "subs.en.vtt"
        vtt_path.write_text(vtt_content)

        words = parse_vtt_to_words(vtt_path)

        assert len(words) == 6
        # First cue: "Hello world today" over 3 seconds, 3 words = 1s each
        assert words[0]["word"] == "Hello"
        assert words[0]["start"] == pytest.approx(1.0, abs=0.01)
        assert words[0]["end"] == pytest.approx(2.0, abs=0.01)
        assert words[1]["word"] == "world"
        assert words[2]["word"] == "today"

        # Second cue
        assert words[3]["word"] == "We"
        assert words[3]["start"] == pytest.approx(5.0, abs=0.01)

    def test_parse_vtt_missing_file(self, tmp_path):
        """Non-existent VTT path returns empty list."""
        from src.style_learner.data_collection.transcript_extractor import (
            parse_vtt_to_words,
        )

        result = parse_vtt_to_words(tmp_path / "does_not_exist.vtt")
        assert result == []

    def test_parse_vtt_strips_tags(self, tmp_path):
        """HTML-like tags in VTT cues are stripped."""
        from src.style_learner.data_collection.transcript_extractor import (
            parse_vtt_to_words,
        )

        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:02.000
<c.colorE5E5E5>Tagged</c> words
"""
        vtt_path = tmp_path / "subs.vtt"
        vtt_path.write_text(vtt_content)

        words = parse_vtt_to_words(vtt_path)
        assert len(words) == 2
        assert words[0]["word"] == "Tagged"
        assert words[1]["word"] == "words"


# ---------------------------------------------------------------------------
# frame_extractor tests
# ---------------------------------------------------------------------------


class TestExtractFrames:
    """Test frame extraction with mocked ffmpeg."""

    def test_extract_frames_calls_ffmpeg(self, tmp_path):
        """Mock subprocess.run, verify ffmpeg command structure."""
        from src.style_learner.data_collection.frame_extractor import extract_frames

        video_path = tmp_path / "video.mp4"
        video_path.touch()
        output_dir = tmp_path / "frames"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # No actual frames created since ffmpeg is mocked
            extract_frames(video_path, output_dir, fps=2)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "ffmpeg" == call_args[0]
        assert "-i" in call_args
        assert str(video_path) in call_args
        assert "fps=2" in call_args
        assert "-q:v" in call_args

    def test_extract_frames_returns_zero_on_failure(self, tmp_path):
        """Nonzero return code from ffmpeg should return 0 frames."""
        from src.style_learner.data_collection.frame_extractor import extract_frames

        video_path = tmp_path / "video.mp4"
        video_path.touch()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some ffmpeg error"

        with patch("subprocess.run", return_value=mock_result):
            count = extract_frames(video_path, tmp_path / "frames", fps=2)

        assert count == 0


# ---------------------------------------------------------------------------
# scene_detector tests
# ---------------------------------------------------------------------------


class TestDetectScenes:
    """Test scene detection with mocked scenedetect."""

    def test_detect_scenes_returns_list(self, tmp_path):
        """Mock scenedetect internals, verify output format."""
        from src.style_learner.data_collection.scene_detector import detect_scenes

        video_path = tmp_path / "video.mp4"
        video_path.touch()

        # Create mock scene timecodes
        mock_start1 = MagicMock()
        mock_start1.get_seconds.return_value = 0.0
        mock_end1 = MagicMock()
        mock_end1.get_seconds.return_value = 5.5

        mock_start2 = MagicMock()
        mock_start2.get_seconds.return_value = 5.5
        mock_end2 = MagicMock()
        mock_end2.get_seconds.return_value = 12.3

        mock_scene_list = [(mock_start1, mock_end1), (mock_start2, mock_end2)]

        mock_scene_manager = MagicMock()
        mock_scene_manager.get_scene_list.return_value = mock_scene_list

        mock_video = MagicMock()

        with patch(
            "src.style_learner.data_collection.scene_detector.open_video",
            create=True,
        ) as mock_open_video, patch(
            "src.style_learner.data_collection.scene_detector.SceneManager",
            create=True,
        ) as MockSceneManager, patch(
            "src.style_learner.data_collection.scene_detector.ContentDetector",
            create=True,
        ):
            # The module does lazy import, so we patch at the module level
            # Actually, detect_scenes imports inside the function. We need to
            # mock the scenedetect module itself.
            pass

        # Better approach: mock the entire scenedetect import chain
        mock_scenedetect = MagicMock()
        mock_scenedetect.open_video.return_value = mock_video
        mock_sm_instance = MagicMock()
        mock_sm_instance.get_scene_list.return_value = mock_scene_list
        mock_scenedetect.SceneManager.return_value = mock_sm_instance

        import sys

        with patch.dict(sys.modules, {
            "scenedetect": mock_scenedetect,
            "scenedetect.detectors": MagicMock(),
        }):
            # Re-call after patching modules
            from src.style_learner.data_collection import scene_detector

            # Patch the lazy imports that happen inside detect_scenes
            with patch.object(scene_detector, "__builtins__", scene_detector.__builtins__ if hasattr(scene_detector, "__builtins__") else __builtins__):
                # We need to mock at the import level inside the function
                mock_open_video_fn = MagicMock(return_value=mock_video)
                mock_content_detector = MagicMock()

                with patch.dict(sys.modules, {
                    "scenedetect": MagicMock(
                        open_video=mock_open_video_fn,
                        SceneManager=MagicMock(return_value=mock_sm_instance),
                    ),
                    "scenedetect.detectors": MagicMock(
                        ContentDetector=mock_content_detector,
                    ),
                }):
                    scenes = scene_detector.detect_scenes(video_path)

        assert isinstance(scenes, list)
        assert len(scenes) == 2
        assert scenes[0]["scene_id"] == 0
        assert scenes[0]["start_time"] == pytest.approx(0.0)
        assert scenes[0]["end_time"] == pytest.approx(5.5)
        assert scenes[0]["duration"] == pytest.approx(5.5)
        assert scenes[1]["scene_id"] == 1
        assert scenes[1]["start_time"] == pytest.approx(5.5)

    def test_detect_scenes_missing_video(self, tmp_path):
        """Non-existent video should return empty list."""
        from src.style_learner.data_collection.scene_detector import detect_scenes

        # Mock scenedetect so the import doesn't fail
        import sys
        with patch.dict(sys.modules, {
            "scenedetect": MagicMock(),
            "scenedetect.detectors": MagicMock(),
        }):
            scenes = detect_scenes(tmp_path / "nonexistent.mp4")

        assert scenes == []
