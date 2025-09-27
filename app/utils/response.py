from typing import Any, Dict, Optional

def success_response(message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    return {"success": True, "message": message, "data": data}

def error_response(message: str, errors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return payload