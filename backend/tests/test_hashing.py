from app.core.hashing import sha256_json, sha256_text


def test_sha256_text_is_stable_and_full_length() -> None:
    assert sha256_text("market intelligence") == (
        "5dc2a46f95f7bb5a8e70ff3a629eea31359f9edb515ef540a77ea5f212352112"
    )
    assert len(sha256_text("market intelligence")) == 64


def test_sha256_json_canonicalizes_mapping_order() -> None:
    first = sha256_json({"ticker": "AAPL", "inputs": {"wacc": 0.09, "growth": 0.03}})
    second = sha256_json({"inputs": {"growth": 0.03, "wacc": 0.09}, "ticker": "AAPL"})

    assert first == second
