
import os
import re
import jwt
from datetime import datetime, timedelta, timezone
from errors import ApiError
from users import find_public


def get_secret():
    secret = os.getenv("JWT_SECRET", "")

    # 64자리 16진수 형식 검사
    if not re.fullmatch(r"[0-9a-fA-F]{64}", secret):
        raise RuntimeError("JWT_SECRET은 64자리 16진수여야 합니다.")

    # 제공 예시 키는 실제 키로 사용할 수 없음
    if secret.lower() in {
        "0123456789abcdef" * 4,
        "0" * 64,
        "f" * 64,
    }:
        raise RuntimeError("예시 JWT_SECRET은 사용할 수 없습니다.")

    return bytes.fromhex(secret)


def issue_token(user):
    secret = get_secret()

    ttl = int(os.getenv("TOKEN_TTL", "90"))
    if ttl <= 0:
        raise RuntimeError("TOKEN_TTL은 양수여야 합니다.")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user["id"]),
        "exp": now + timedelta(seconds=ttl),
        "iss": os.getenv("JWT_ISSUER", "webservice-class"),
        "aud": os.getenv("JWT_AUDIENCE", "board-api"),
    }

    return jwt.encode(payload, secret, algorithm="HS256")



def current_user_id(request):
    authorization = request.headers.get("Authorization")

    # 1. 토큰이 없거나 Bearer 형식이 잘못된 경우
    if not authorization:
        raise ApiError(401, "TOKEN_REQUIRED", "로그인이 필요합니다.")

    parts = authorization.split()

    if len(parts) != 2 or parts[0] != "Bearer":
        raise ApiError(401, "TOKEN_REQUIRED", "Bearer 토큰이 필요합니다.")

    token = parts[1]

    # 2. JWT 서명, 알고리즘, 만료, 클레임 검증
    try:
        payload = jwt.decode(
            token,
            get_secret(),
            algorithms=["HS256"],
            issuer=os.getenv("JWT_ISSUER", "webservice-class"),
            audience=os.getenv("JWT_AUDIENCE", "board-api"),
            options={
                "require": ["sub", "exp", "iss", "aud"]
            },
        )

    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRED", "토큰이 만료되었습니다.")

    except jwt.InvalidTokenError:
        raise ApiError(401, "INVALID_TOKEN", "유효하지 않은 토큰입니다.")

    # 3. sub가 올바른 사용자 ID인지 확인
    sub = payload.get("sub")

    if (
        not isinstance(sub, str)
        or not re.fullmatch(r"[1-9][0-9]*", sub)
    ):
        raise ApiError(401, "INVALID_TOKEN", "사용자 ID가 올바르지 않습니다.")

    user_id = int(sub)

    # 4. 실제 계정 존재 확인
    user = find_public(user_id)

    if not user:
        raise ApiError(401, "INVALID_TOKEN", "존재하지 않는 사용자입니다.")

    return user_id




def assert_owner(user_id, author_id):
    if user_id != author_id:
        raise ApiError(
            403,
            "FORBIDDEN",
            "본인이 작성한 게시글만 수정하거나 삭제할 수 있습니다."
        )
