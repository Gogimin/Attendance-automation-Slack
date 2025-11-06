"""에러 처리 유틸리티"""

import logging
import traceback
from functools import wraps
from flask import jsonify, current_app

logger = logging.getLogger(__name__)


def safe_error_response(func):
    """
    에러 처리 래퍼 데코레이터 (스택 트레이스 노출 방지)

    프로덕션 환경에서는 스택 트레이스를 숨기고 일반적인 에러 메시지만 반환합니다.
    개발 환경에서는 디버깅을 위해 상세한 에러 정보를 포함합니다.

    Args:
        func: 래핑할 Flask 라우트 함수

    Returns:
        래핑된 함수

    Examples:
        >>> @app.route('/api/test')
        >>> @safe_error_response
        >>> def test_endpoint():
        >>>     raise Exception("Test error")
        >>>     return jsonify({'success': True})
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 로그에는 상세 정보 기록
            logger.exception(f"API error in {func.__name__}: {str(e)}")

            # 프로덕션: 일반 메시지만 (보안)
            if not current_app.debug:
                return jsonify({
                    'success': False,
                    'error': '요청 처리 중 오류가 발생했습니다. 관리자에게 문의하세요.'
                }), 500

            # 개발 모드: 상세 정보 (디버깅)
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500

    return wrapper


class APIError(Exception):
    """
    API 에러 베이스 클래스

    Attributes:
        code: 에러 코드 (예: INVALID_INPUT, RESOURCE_NOT_FOUND)
        message: 사용자에게 표시할 메시지
        status_code: HTTP 상태 코드
        details: 추가 상세 정보
    """
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


def register_error_handlers(app):
    """
    Flask 앱에 에러 핸들러 등록

    Args:
        app: Flask 앱 인스턴스
    """
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """APIError 핸들러"""
        return jsonify({
            'success': False,
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            }
        }), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        """404 Not Found 핸들러"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': '요청한 리소스를 찾을 수 없습니다.'
            }
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        """500 Internal Server Error 핸들러"""
        logger.exception("Internal server error")

        if not app.debug:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': '서버 오류가 발생했습니다.'
                }
            }), 500
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': str(error),
                    'traceback': traceback.format_exc()
                }
            }), 500
