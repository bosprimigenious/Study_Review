"""Materials routes."""

from __future__ import annotations

from fastapi import APIRouter

from ..core.storage import course_dir, load_course_files

router = APIRouter(prefix="/courses", tags=["materials"])


@router.get("/{course_id}/materials")
def list_materials(course_id: str) -> dict:
    course_dir(course_id)
    data = load_course_files(course_id)
    files = []
    for item in data.get("files", []):
        path = str(item.get("path", ""))
        name = path.split("/")[-1] if path else item.get("id", "")
        ext = name.rsplit(".", 1)[-1] if "." in name else ""
        files.append(
            {
                "id": item.get("id", name),
                "path": path,
                "name": name,
                "material_type": item.get("material_type", "other"),
                "ext": ext,
                "status": item.get("status", "indexed"),
                "tags": item.get("tags", []) or [],
            }
        )
    return {"course_id": course_id, "files": files}
