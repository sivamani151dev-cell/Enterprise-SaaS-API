import sendgrid
from sendgrid.helpers.mail import Mail
from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="send_welcome_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_welcome_email(self, user_email: str, user_name: str, org_name: str):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=user_email,
            subject=f"Welcome to {org_name}!",
            html_content=f"""
                <h1>Welcome, {user_name}!</h1>
                <p>Your organization <strong>{org_name}</strong> has been created successfully.</p>
                <p>You can now invite team members and start collaborating.</p>
            """
        )

        response = sg.send(message)
        logger.info(
            "Welcome email sent",
            extra={
                "user_email": user_email,
                "org_name": org_name,
                "status_code": response.status_code
            }
        )
        return {"status": "sent", "email": user_email}

    except Exception as exc:
        logger.error(
            "Failed to send welcome email",
            extra={"user_email": user_email, "error": str(exc)}
        )
        raise self.retry(exc=exc)


@celery_app.task(
    name="send_invitation_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_invitation_email(
    self,
    invitee_email: str,
    inviter_name: str,
    org_name: str,
    org_slug: str
):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=invitee_email,
            subject=f"You've been invited to join {org_name}",
            html_content=f"""
                <h1>You're invited!</h1>
                <p><strong>{inviter_name}</strong> has invited you to join 
                <strong>{org_name}</strong>.</p>
                <p>Login or create an account to get started.</p>
            """
        )

        response = sg.send(message)
        logger.info(
            "Invitation email sent",
            extra={
                "invitee_email": invitee_email,
                "org_name": org_name,
                "status_code": response.status_code
            }
        )
        return {"status": "sent", "email": invitee_email}

    except Exception as exc:
        logger.error(
            "Failed to send invitation email",
            extra={"invitee_email": invitee_email, "error": str(exc)}
        )
        raise self.retry(exc=exc)