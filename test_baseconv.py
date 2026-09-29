import unittest

from baseconv import BaseConverter, base2, base16, base58, base64


class BaseConverterTests(unittest.TestCase):
    def test_empty_and_sign_only_inputs(self):
        for converter in (base2, base16, base58, base64):
            with self.assertRaisesRegex(ValueError, 'empty string'):
                converter.encode('')
            with self.assertRaisesRegex(ValueError, 'empty string'):
                converter.decode('')
            with self.assertRaisesRegex(ValueError, 'without digits'):
                converter.encode('-')
            with self.assertRaisesRegex(ValueError, 'without digits'):
                converter.decode(converter.sign)

    def test_invalid_digits(self):
        with self.assertRaisesRegex(ValueError, 'invalid digit'):
            base2.encode('1a')
        with self.assertRaisesRegex(ValueError, 'invalid digit'):
            base2.decode('2')

    def test_single_digit_alphabet_rejected(self):
        for digits in ('', 'a'):
            with self.assertRaises(ValueError):
                BaseConverter(digits)

    def test_round_trip_boundaries(self):
        long_number = 10 ** 500 + 123456789
        for converter in (base2, base16, base58, base64):
            for number in (0, 1, -1, 10 ** 80, -(10 ** 80), long_number, -long_number):
                self.assertEqual(int(converter.decode(converter.encode(number))), number)


if __name__ == '__main__':
    unittest.main()
