import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fx_metal_report.email_sender import send_email  # noqa: E402


def test_send_email_uses_ssl_for_port_465():
    mock_server = MagicMock()
    with patch("fx_metal_report.email_sender.smtplib.SMTP_SSL", return_value=mock_server) as mock_ssl, patch(
        "fx_metal_report.email_sender.smtplib.SMTP"
    ) as mock_plain:
        ok = send_email(
            "smtp.example.com", 465, "me@example.com", "pw", "me@example.com", "제목", "<p>본문</p>"
        )

    assert ok is True
    mock_ssl.assert_called_once()
    mock_plain.assert_not_called()
    mock_server.login.assert_called_once_with("me@example.com", "pw")
    mock_server.sendmail.assert_called_once()


def test_send_email_uses_starttls_for_port_587():
    mock_server = MagicMock()
    with patch("fx_metal_report.email_sender.smtplib.SMTP", return_value=mock_server) as mock_plain, patch(
        "fx_metal_report.email_sender.smtplib.SMTP_SSL"
    ) as mock_ssl:
        ok = send_email(
            "smtp.example.com", 587, "me@example.com", "pw", "me@example.com", "제목", "<p>본문</p>"
        )

    assert ok is True
    mock_plain.assert_called_once()
    mock_ssl.assert_not_called()
    mock_server.starttls.assert_called_once()


def test_send_email_includes_attachments(tmp_path):
    attachment = tmp_path / "chart.png"
    attachment.write_bytes(b"fake-png-bytes")
    mock_server = MagicMock()

    with patch("fx_metal_report.email_sender.smtplib.SMTP_SSL", return_value=mock_server):
        send_email(
            "smtp.example.com",
            465,
            "me@example.com",
            "pw",
            "me@example.com",
            "제목",
            "<p>본문</p>",
            attachments=[attachment],
        )

    sent_call = mock_server.sendmail.call_args
    raw_message = sent_call.args[2]
    assert "chart.png" in raw_message


def test_send_email_embeds_inline_images_with_content_id(tmp_path):
    chart = tmp_path / "fx_chart.png"
    chart.write_bytes(b"fake-png-bytes")
    mock_server = MagicMock()

    with patch("fx_metal_report.email_sender.smtplib.SMTP_SSL", return_value=mock_server):
        send_email(
            "smtp.example.com",
            465,
            "me@example.com",
            "pw",
            "me@example.com",
            "제목",
            '<img src="cid:fx_chart">',
            inline_images={"fx_chart": chart},
        )

    raw_message = mock_server.sendmail.call_args.args[2]
    assert "Content-ID: <fx_chart>" in raw_message
    assert "inline" in raw_message
    assert "multipart/related" in raw_message


def test_send_email_returns_false_on_smtp_failure():
    with patch("fx_metal_report.email_sender.smtplib.SMTP_SSL", side_effect=OSError("연결 실패")):
        ok = send_email(
            "smtp.example.com", 465, "me@example.com", "pw", "me@example.com", "제목", "<p>본문</p>"
        )
    assert ok is False
