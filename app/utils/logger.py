"""
로그 유틸리티
loguru를 사용한 중앙화된 로깅 설정
"""
import sys
from pathlib import Path
from loguru import logger


class LoggerSetup:
    """로그 설정 유틸리티 클래스"""

    _initialized = False

    @classmethod
    def setup(
        cls,
        log_dir: str = "logs",
        log_file: str = "app.log",
        rotation: str = "10 MB",
        retention: str = "7 days",
        level: str = "INFO",
        console_level: str = "DEBUG",
        json_format: bool = False
    ):
        """
        로그 설정 초기화

        Args:
            log_dir: 로그 디렉토리 경로
            log_file: 로그 파일명
            rotation: 로그 파일 회전 크기 (예: "10 MB", "100 KB", "1 day")
            retention: 로그 보관 기간 (예: "7 days", "1 week", "30 days")
            level: 파일 로그 레벨
            console_level: 콘솔 로그 레벨
            json_format: JSON 포맷 사용 여부
        """
        if cls._initialized:
            return logger

        # 기본 핸들러 제거
        logger.remove()

        # 콘솔 로그 추가 (컬러풀)
        logger.add(
            sys.stderr,
            level=console_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )

        # 로그 디렉토리 생성
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 파일 로그 추가
        if json_format:
            # JSON 포맷 (구조화된 로그)
            logger.add(
                log_path / log_file,
                level=level,
                rotation=rotation,
                retention=retention,
                serialize=True,  # JSON 직렬화
                enqueue=True,    # 비동기 로깅
                backtrace=True,  # 예외 추적
                diagnose=True    # 상세 진단
            )
        else:
            # 일반 텍스트 포맷
            logger.add(
                log_path / log_file,
                level=level,
                rotation=rotation,
                retention=retention,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                enqueue=True,
                backtrace=True,
                diagnose=True
            )

        # 에러 전용 로그 파일
        logger.add(
            log_path / "error.log",
            level="ERROR",
            rotation=rotation,
            retention=retention,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )

        cls._initialized = True
        logger.info(f"로거 초기화 완료: {log_dir}/{log_file}")
        return logger

    @classmethod
    def get_logger(cls):
        """
        로거 인스턴스 반환
        초기화되지 않았다면 기본 설정으로 초기화
        """
        if not cls._initialized:
            cls.setup()
        return logger


# 간편한 사용을 위한 함수
def get_logger():
    """로거 가져오기"""
    return LoggerSetup.get_logger()


# 데코레이터: 함수 실행 시간 로깅
def log_execution_time(func):
    """함수 실행 시간을 로깅하는 데코레이터"""
    from functools import wraps
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"🚀 {func.__name__} 시작")

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"✅ {func.__name__} 완료 ({elapsed:.2f}초)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ {func.__name__} 실패 ({elapsed:.2f}초): {e}")
            raise

    return wrapper


# 데코레이터: 예외 자동 로깅
def log_exception(func):
    """예외를 자동으로 로깅하는 데코레이터"""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"예외 발생 in {func.__name__}: {e}")
            raise

    return wrapper

