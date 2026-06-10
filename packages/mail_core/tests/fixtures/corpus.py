"""T-039: Corpus of anonymized receipt email fixtures.

Covers:
  - ofd.ru URL in body_text (positive)
  - check.ofd.ru URL in body_html (positive, html fallback)
  - consumer.rnko.ru URL (positive)
  - 1k.platformaofd.ru URL (positive)
  - taxcom.ru URL (positive, from rules body_domains)
  - Subject with RU keyword only (positive)
  - Subject with EN keyword only (positive)
  - No OFD URL but receipt subject (positive subject, negative url)
  - Subject excluded via subject_exclude (negative)
  - Sender excluded via sender_exclude (negative)
  - Newsletter email (negative)
  - Edge: URL in both text and html (prefers text)
"""
from datetime import datetime, timezone
from packages.mail_core.models import ParsedEmail


BASE_DATE = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Positive fixtures — should_process == True
# ---------------------------------------------------------------------------

CORPUS_POSITIVE = [
    # 1. ofd.ru URL in body_text, subject with RU keyword
    ParsedEmail(
        uid="001",
        message_id="<001@anon.test>",
        subject="Ваш чек от SHOP_A",
        body_text="Спасибо за покупку! Ссылка: https://ofd.ru/r/aaa111bbb222",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 2. check.ofd.ru URL in body_html only (text fallback)
    ParsedEmail(
        uid="002",
        message_id="<002@anon.test>",
        subject="Электронный чек SHOP_B",
        body_text="Спасибо за покупку!",
        body_html="<a href='https://check.ofd.ru/rec/ccc333ddd444'>Чек</a>",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 3. consumer.rnko.ru URL
    ParsedEmail(
        uid="003",
        message_id="<003@anon.test>",
        subject="Кассовый чек SHOP_C",
        body_text="Оплата подтверждена. https://consumer.rnko.ru/receipt/eee555fff666",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 4. 1k.platformaofd.ru URL
    ParsedEmail(
        uid="004",
        message_id="<004@anon.test>",
        subject="Оплата принята SHOP_D",
        body_text="Ваш чек: https://1k.platformaofd.ru/web/ggg777hhh888",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 5. taxcom.ru URL (matches generic /check/ pattern)
    ParsedEmail(
        uid="005",
        message_id="<005@anon.test>",
        subject="receipt from SHOP_E",
        body_text="Your receipt: https://receipt.taxcom.ru/check/iii999jjj000",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 6. EN subject keyword only — 'invoice'
    ParsedEmail(
        uid="006",
        message_id="<006@anon.test>",
        subject="Invoice #98765 from SHOP_F",
        body_text="Payment confirmed. https://ofd.ru/r/kkk111lll222",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 7. URL in both text and html — parser should prefer text
    ParsedEmail(
        uid="007",
        message_id="<007@anon.test>",
        subject="Ваш чек SHOP_G",
        body_text="https://ofd.ru/r/text-url-mmm333",
        body_html="<a href='https://check.ofd.ru/rec/html-url-nnn444'>Чек</a>",
        date=BASE_DATE,
        folder="INBOX",
    ),
]


# ---------------------------------------------------------------------------
# Negative fixtures — should_process == False
# ---------------------------------------------------------------------------

CORPUS_NEGATIVE = [
    # 8. Subject has receipt keyword but no OFD URL — receipt_url should be None
    ParsedEmail(
        uid="008",
        message_id="<008@anon.test>",
        subject="Ваш чек готов",
        body_text="Спасибо за покупку! Никаких ссылок.",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 9. Subject matches subject_exclude: 'отчет'
    ParsedEmail(
        uid="009",
        message_id="<009@anon.test>",
        subject="Еженедельный отчет о покупках",
        body_text="https://ofd.ru/r/ooo555ppp666",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 10. Newsletter — subject_exclude: 'newsletter'
    ParsedEmail(
        uid="010",
        message_id="<010@anon.test>",
        subject="Weekly newsletter from SHOP_H",
        body_text="Check out our deals!",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 11. Sender excluded: noreply@
    ParsedEmail(
        uid="011",
        message_id="<011@anon.test>",
        subject="Электронный чек SHOP_I",
        body_text="https://ofd.ru/r/qqq777rrr888",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
    # 12. Unrelated email — no keywords, no URL
    ParsedEmail(
        uid="012",
        message_id="<012@anon.test>",
        subject="Новости недели",
        body_text="Прочитайте нашу подборку.",
        body_html="",
        date=BASE_DATE,
        folder="INBOX",
    ),
]


# All fixtures combined
CORPUS_ALL = CORPUS_POSITIVE + CORPUS_NEGATIVE

# Negative UIDs excluded only by sender (need dispatcher with from_addr check)
CORPUS_SENDER_EXCLUDED_UIDS = {"011"}
