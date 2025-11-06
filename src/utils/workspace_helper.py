"""워크스페이스 검증 유틸리티"""

import re
from pathlib import Path


def validate_workspace_name(workspace_name: str) -> bool:
    """
    워크스페이스 이름 검증 (경로 탐색 방어)

    Args:
        workspace_name: 검증할 워크스페이스 이름

    Returns:
        bool: 유효하면 True, 아니면 False

    Examples:
        >>> validate_workspace_name("my_workspace")
        True
        >>> validate_workspace_name("../../../etc/passwd")
        False
        >>> validate_workspace_name("workspace/../other")
        False
    """
    if not workspace_name:
        return False

    # 위험한 문자 검사: .., /, \, null byte
    if '..' in workspace_name or workspace_name.startswith('.'):
        return False

    if any(char in workspace_name for char in ['/', '\\', '\0']):
        return False

    # 길이 제한 (50자)
    if len(workspace_name) > 50:
        return False

    return True


def safe_path_join(base: Path, workspace_name: str) -> Path:
    """
    안전한 경로 조합 (경로 이탈 확인)

    Args:
        base: 기본 경로
        workspace_name: 워크스페이스 이름

    Returns:
        Path: 안전하게 조합된 경로

    Raises:
        ValueError: 유효하지 않은 워크스페이스 이름 또는 경로 이탈 시

    Examples:
        >>> base = Path("/workspaces")
        >>> safe_path_join(base, "my_workspace")
        PosixPath('/workspaces/my_workspace')
        >>> safe_path_join(base, "../etc")  # doctest: +SKIP
        Traceback (most recent call last):
        ValueError: 유효하지 않은 워크스페이스 이름
    """
    # 1. 워크스페이스 이름 검증
    if not validate_workspace_name(workspace_name):
        raise ValueError(f"유효하지 않은 워크스페이스 이름: {workspace_name}")

    # 2. 경로 조합
    workspace_folder = (base / workspace_name).resolve()
    base_resolved = base.resolve()

    # 3. 경로 이탈 확인 (심볼릭 링크 공격 방어)
    if not str(workspace_folder).startswith(str(base_resolved)):
        raise ValueError(f"유효하지 않은 경로 (경로 이탈 감지): {workspace_folder}")

    return workspace_folder
