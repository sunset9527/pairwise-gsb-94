# -*- coding: utf-8 -*-
"""Regression tests for defects found by differential audit (seed 20260929)."""
import unittest

from baseconv import BaseConverter, base2, base16, base64


CONVERS = [base2, base16, base64]


class EmptyInputTest(unittest.TestCase):
    """Empty string must raise ValueError, never leak IndexError."""

    def test_encode_empty(self):
        for conv in CONVERS:
            with self.assertRaises(ValueError):
                conv.encode('')

    def test_decode_empty(self):
        for conv in CONVERS:
            with self.assertRaises(ValueError):
                conv.decode('')


class SignOnlyInputTest(unittest.TestCase):
    """A lone sign character is not a number and must be rejected."""

    def test_encode_sign_only(self):
        for conv in CONVERS:
            with self.assertRaises(ValueError):
                conv.encode('-')

    def test_decode_sign_only(self):
        for conv in CONVERS:
            with self.assertRaises(ValueError):
                conv.decode(conv.sign)


class NegativeZeroTest(unittest.TestCase):
    """Negative zero normalizes to zero (no sign prefix)."""

    def test_encode_negative_zero(self):
        self.assertEqual(base2.encode('-0'), '0')
        self.assertEqual(base16.encode('-0'), '0')
        self.assertEqual(base64.encode('-0'), '0')

    def test_decode_negative_zero(self):
        self.assertEqual(base2.decode('-0'), '0')
        self.assertEqual(base16.decode('-0'), '0')
        self.assertEqual(base64.decode('$0'), '0')

    def test_zero_uses_first_alphabet_digit(self):
        conv = BaseConverter('ab')
        self.assertEqual(conv.encode(0), 'a')
        self.assertEqual(conv.encode('-0'), 'a')
        self.assertEqual(conv.decode('-a'), '0')


class RoundTripTest(unittest.TestCase):
    def test_roundtrip(self):
        for conv in CONVERS:
            for n in [0, 1, -1, 1234, -1234, 10 ** 30, -(10 ** 30)]:
                self.assertEqual(int(conv.decode(conv.encode(n))), n)


if __name__ == '__main__':
    unittest.main()
