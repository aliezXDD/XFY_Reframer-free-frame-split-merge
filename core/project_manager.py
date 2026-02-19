import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


@dataclass
class ProjectInfo:
    name: str
    root_dir: Path
    created_at: str
    original_dir: Path
    frames_dir: Path
    timestamps_dir: Path
    modified_dir: Path
    output_dir: Path
    original_video: Optional[Path] = None

    @property
    def display_name(self) -> str:
        return self.name


class ProjectManager:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root)
        self.projects_root = self.workspace_root / "projects"
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def create_project_from_video(self, video_path: str) -> ProjectInfo:
        source_video = Path(video_path)
        if not source_video.exists():
            raise FileNotFoundError(f"Video file does not exist: {video_path}")

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_stem = self._safe_name(source_video.stem)
        project_name = f"{safe_stem}_{stamp}"
        project_root = self.projects_root / project_name

        project = self._build_project(project_root, created_at=stamp)
        self._ensure_structure(project)

        target_video = project.original_dir / source_video.name
        shutil.copy2(source_video, target_video)
        project.original_video = target_video

        self._write_metadata(project, source_video.name)
        return project

    def list_projects(self) -> List[ProjectInfo]:
        projects: List[ProjectInfo] = []
        if not self.projects_root.exists():
            return projects

        for project_dir in self.projects_root.iterdir():
            if not project_dir.is_dir():
                continue
            try:
                projects.append(self.load_project(project_dir))
            except Exception:
                continue

        projects.sort(key=lambda item: item.root_dir.stat().st_mtime, reverse=True)
        return projects

    def delete_project(self, project_dir: Path) -> None:
        target = Path(project_dir).resolve()
        root = self.projects_root.resolve()
        if root not in target.parents:
            raise ValueError("Project path is outside projects directory.")
        if target.exists() and target.is_dir():
            shutil.rmtree(target)

    def load_project(self, project_dir: Path) -> ProjectInfo:
        project_dir = Path(project_dir)
        metadata_path = project_dir / "project.json"
        created_at = ""
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as file:
                metadata = json.load(file)
            created_at = metadata.get("created_at", "")
        if not created_at:
            created_at = datetime.fromtimestamp(project_dir.stat().st_mtime).strftime("%Y%m%d_%H%M%S")

        project = self._build_project(project_dir, created_at=created_at)
        self._ensure_structure(project)
        project.original_video = self._find_first_video(project.original_dir)
        return project

    def get_project_state(self, project: ProjectInfo) -> Dict[str, object]:
        timing_files = self.list_timing_files(project)
        output_files = self.list_output_files(project)
        modified_images = self.list_images(project.modified_dir)
        frame_images = self.list_images(project.frames_dir)

        state = {
            "has_video": project.original_video is not None and project.original_video.exists(),
            "frame_count": len(frame_images),
            "modified_count": len(modified_images),
            "timing_files": timing_files,
            "selected_timing": timing_files[0] if timing_files else None,
            "output_files": output_files,
            "latest_output": output_files[0] if output_files else None,
        }
        return state

    def list_timing_files(self, project: ProjectInfo) -> List[Path]:
        if not project.timestamps_dir.exists():
            return []
        files = sorted(project.timestamps_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return files

    def list_output_files(self, project: ProjectInfo) -> List[Path]:
        if not project.output_dir.exists():
            return []
        files = sorted(project.output_dir.glob("*.mp4"), key=lambda path: path.stat().st_mtime, reverse=True)
        return files

    def read_timing_info(self, timing_path: Path) -> Dict[str, object]:
        path = Path(timing_path)
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        scenes = data.get("scenes", [])
        duration_frames = sum(int(scene.get("duration_frames", 1)) for scene in scenes)
        return {
            "fps": float(data.get("fps") or 24.0),
            "scene_count": len(scenes),
            "duration_frames": duration_frames,
        }

    def replace_modified_images(self, project: ProjectInfo, source_paths: List[str]) -> int:
        self.clear_images(project.modified_dir)
        copied = 0
        for image_path in self._resolve_image_sources(source_paths):
            target = project.modified_dir / image_path.name
            shutil.copy2(image_path, target)
            copied += 1
        return copied

    def clear_images(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                item.unlink()

    def list_images(self, directory: Path) -> List[Path]:
        if not directory.exists():
            return []
        return sorted(
            [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
        )

    def _build_project(self, project_root: Path, created_at: str) -> ProjectInfo:
        return ProjectInfo(
            name=project_root.name,
            root_dir=project_root,
            created_at=created_at,
            original_dir=project_root / "original",
            frames_dir=project_root / "frames",
            timestamps_dir=project_root / "timestamps",
            modified_dir=project_root / "modified",
            output_dir=project_root / "output",
        )

    def _ensure_structure(self, project: ProjectInfo) -> None:
        project.root_dir.mkdir(parents=True, exist_ok=True)
        project.original_dir.mkdir(parents=True, exist_ok=True)
        project.frames_dir.mkdir(parents=True, exist_ok=True)
        project.timestamps_dir.mkdir(parents=True, exist_ok=True)
        project.modified_dir.mkdir(parents=True, exist_ok=True)
        project.output_dir.mkdir(parents=True, exist_ok=True)

    def _write_metadata(self, project: ProjectInfo, source_name: str) -> None:
        metadata = {
            "name": project.name,
            "created_at": project.created_at,
            "source_video_name": source_name,
        }
        metadata_path = project.root_dir / "project.json"
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2, ensure_ascii=False)

    def _resolve_image_sources(self, source_paths: List[str]) -> List[Path]:
        files: List[Path] = []
        for raw_path in source_paths:
            source = Path(raw_path)
            if source.is_dir():
                files.extend(self.list_images(source))
            elif source.is_file() and source.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(source)
        files.sort()
        return files

    def _find_first_video(self, directory: Path) -> Optional[Path]:
        if not directory.exists():
            return None
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                return path
        return None

    def _safe_name(self, raw_name: str) -> str:
        cleaned = "".join(ch if (ch.isalnum() or ch in {"_", "-"}) else "_" for ch in raw_name)
        cleaned = cleaned.strip("_")
        return cleaned or "project"
