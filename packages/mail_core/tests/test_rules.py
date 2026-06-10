from packages.mail_core.rules import MailSelectionRules, is_receipt_candidate


def make_rules() -> MailSelectionRules:
    return MailSelectionRules(
        version=1,
        subject_include=["чек", "receipt", "кассовый чек"],
        subject_exclude=["отчет", "newsletter"],
        sender_exclude=["noreply@", "no-reply@"],
        body_domains=["ofd.ru", "platformaofd.ru", "taxcom.ru"],
    )


def test_subject_include_matches_receipt():
    rules = make_rules()

    assert is_receipt_candidate(
        subject="Ваш кассовый чек",
        sender="shop@example.com",
        body_text="Спасибо за покупку",
        body_html=None,
        rules=rules,
    ) is True


def test_subject_exclude_blocks_message():
    rules = make_rules()

    assert is_receipt_candidate(
        subject="Еженедельный отчет по заказам",
        sender="shop@example.com",
        body_text="ofd.ru",
        body_html=None,
        rules=rules,
    ) is False


def test_sender_exclude_blocks_message():
    rules = make_rules()

    assert is_receipt_candidate(
        subject="Ваш чек",
        sender="noreply@shop.example",
        body_text="https://ofd.ru/receipt/123",
        body_html=None,
        rules=rules,
    ) is False


def test_body_domain_can_match_without_subject_keyword():
    rules = make_rules()

    assert is_receipt_candidate(
        subject="Спасибо за покупку",
        sender="shop@example.com",
        body_text="Ссылка на чек: https://ofd.ru/receipt/123",
        body_html=None,
        rules=rules,
    ) is True


def test_plain_message_without_keywords_or_domains_is_not_receipt():
    rules = make_rules()

    assert is_receipt_candidate(
        subject="Здравствуйте",
        sender="friend@example.com",
        body_text="Просто письмо без признаков чека",
        body_html=None,
        rules=rules,
    ) is False
