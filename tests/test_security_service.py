import unittest

from app.services.security_service import (
    create_access_token,
    hash_password,
    is_password_hash,
    verify_access_token,
    verify_password,
)


class SecurityServiceTest(unittest.TestCase):
    def test_password_hash_and_verification(self):
        plain = "unit-test-password"
        encoded = hash_password(plain)
        self.assertTrue(is_password_hash(encoded))
        self.assertNotIn(plain, encoded)
        self.assertTrue(verify_password(plain, encoded)[0])
        self.assertFalse(verify_password("wrong", encoded)[0])

    def test_plaintext_password_is_upgraded_after_successful_check(self):
        plain = "legacy-test-password"
        valid, upgraded = verify_password(plain, plain)
        self.assertTrue(valid)
        self.assertTrue(is_password_hash(upgraded))

    def test_signed_access_token_rejects_tampering(self):
        token = create_access_token("student", "student")
        claims = verify_access_token(token)
        self.assertEqual(claims.get("sub"), "student")
        self.assertEqual(verify_access_token(token + "x"), {})


if __name__ == "__main__":
    unittest.main()
