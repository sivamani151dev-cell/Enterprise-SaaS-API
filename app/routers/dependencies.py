from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.membership import Membership, MemberRole
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
import jwt


def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedException()
        return user
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid token")


def require_org_role(*allowed_roles: MemberRole):
    def checker(
        org_slug: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        from app.models.organization import Organization
        org = db.query(Organization).filter(
            Organization.slug == org_slug
        ).first()
        if not org:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Organization")

        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.org_id == org.id
        ).first()

        if not membership or membership.role not in allowed_roles:
            raise ForbiddenException()

        return {"user": current_user, "org": org, "membership": membership}
    return checker