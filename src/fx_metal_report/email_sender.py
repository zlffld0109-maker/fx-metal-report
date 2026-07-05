import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)
_TIMEOUT_SECONDS = 20


def send_email(
    smtp_host: str,
    smtp_port: int,
    user: str,
    password: str,
    to: str,
    subject: str,
    html_body: str,
    attachments: list[Path] | None = None,
    inline_images: dict[str, Path] | None = None,
) -> bool:
    """port 465는 SMTP_SSL, 그 외(587 등)는 SMTP+STARTTLS로 발송한다.

    inline_images: {cid: 파일경로} 형태. html_body에서 `<img src="cid:{cid}">`로 참조하면
    첨부가 아니라 본문에 바로 표시되는 인라인 이미지로 삽입된다.
    """
    to_list = [addr.strip() for addr in to.split(",") if addr.strip()]

    msg_root = MIMEMultipart("mixed")
    msg_root["Subject"] = subject
    msg_root["From"] = user
    msg_root["To"] = to

    msg_related = MIMEMultipart("related")
    msg_related.attach(MIMEText(html_body, "html", "utf-8"))

    for cid, path in (inline_images or {}).items():
        subtype = path.suffix.lstrip(".").lower() or "png"
        with path.open("rb") as f:
            image = MIMEImage(f.read(), _subtype=subtype)
        image.add_header("Content-ID", f"<{cid}>")
        image.add_header("Content-Disposition", "inline", filename=path.name)
        msg_related.attach(image)

    msg_root.attach(msg_related)

    for path in attachments or []:
        with path.open("rb") as f:
            part = MIMEApplication(f.read(), Name=path.name)
        part["Content-Disposition"] = f'attachment; filename="{path.name}"'
        msg_root.attach(part)

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=_TIMEOUT_SECONDS)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=_TIMEOUT_SECONDS)
            server.starttls()
        with server:
            server.login(user, password)
            server.sendmail(user, to_list, msg_root.as_string())
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning(f"이메일 발송 실패: {exc}")
        return False
