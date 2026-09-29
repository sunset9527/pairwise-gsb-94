# -*- coding: utf-8 -*-
"""Differential audit of baseconv against a reference implementation.

Invariant: for ANY input, BaseConverter.encode/decode must either
  (a) return the mathematically correct result, or
  (b) raise a clean, documented exception (ValueError/TypeError).
It must NEVER leak internal IndexError/KeyError/etc., and must never
return a wrong result silently.
"""
import random
import sys

try:
    sys.set_int_max_str_digits(0)
except AttributeError:
    pass

sys.path.insert(0, '/home/sunset/gsb/uid90/A')
from baseconv import BaseConverter, base2, base16, base36, base56, base58, base62, base64

FRIENDLY = (ValueError, TypeError)


def ref_encode(number, digits, sign='-'):
    """Reference: decimal-string/int -> base-len(digits) string."""
    s = str(number)
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    if not s or any(c not in '0123456789' for c in s):
        raise ValueError('invalid literal')
    x = int(s)
    if x == 0:
        return digits[0]  # zero (incl. -0) normalizes to digits[0]
    out = ''
    b = len(digits)
    while x:
        out = digits[x % b] + out
        x //= b
    return (sign + out) if neg else out


def ref_decode(text, digits, sign='-'):
    """Reference: base-len(digits) string -> decimal string."""
    s = str(text)
    neg = s.startswith(sign)
    if neg:
        s = s[len(sign):]
    if not s:
        raise ValueError('empty string')
    x = 0
    b = len(digits)
    for ch in s:
        i = digits.find(ch)
        if i < 0:
            raise ValueError('invalid digit %r' % ch)
        x = x * b + i
    # normalize: strip leading zeros semantics via int
    out = str(x)
    return ('-' + out) if neg and x != 0 else out


def check(conv, fn_name, arg, ref_fn):
    fn = getattr(conv, fn_name)
    try:
        expected = ref_fn(arg)
        expected_exc = None
    except FRIENDLY as e:
        expected, expected_exc = None, e
    try:
        got = fn(arg)
        got_exc = None
    except Exception as e:
        got, got_exc = None, e

    if expected_exc is None:
        if got_exc is not None:
            return ('RAISES_BUT_SHOULD_RETURN', arg, expected, repr(got_exc))
        if got != expected:
            return ('WRONG_RESULT', arg, expected, got)
    else:
        if got_exc is None:
            return ('RETURNS_BUT_SHOULD_RAISE', arg, 'ValueError', got)
        if not isinstance(got_exc, FRIENDLY):
            return ('UNFRIENDLY_EXCEPTION', arg, 'ValueError', repr(got_exc))
    return None


def main():
    rng = random.Random(20260929)
    convs = {
        'base2': base2, 'base16': base16, 'base36': base36, 'base56': base56,
        'base58': base58, 'base62': base62, 'base64': base64,
    }
    failures = []

    def run(conv_name, conv, sign):
        digits = conv.digits
        # ---- encode inputs ----
        enc_inputs = ['', '-', '--', ' ', '+5', '3.14', '0x1F', '１２', '1_000',
                      '00', '-0', '-00', '007', None, True]
        for _ in range(300):
            enc_inputs.append(rng.randint(-10**30, 10**30))
        for _ in range(100):
            enc_inputs.append(str(rng.randint(-10**6, 10**6)))
        for _ in range(50):  # garbage strings
            enc_inputs.append(''.join(rng.choice('abcXYZ-.+ \t') for _ in range(rng.randint(0, 6))))
        enc_inputs.append('9' * 5000)  # very long input
        for a in enc_inputs:
            try:
                r = check(conv, 'encode', a, lambda v: ref_encode(v, digits, sign))
            except Exception as e:
                r = ('HARNESS', a, None, repr(e))
            if r:
                failures.append((conv_name, 'encode') + r)

        # ---- decode inputs ----
        dec_inputs = ['', sign, sign * 2, ' ', '0', '00', '0007', sign + '0',
                      sign + '00', 'abcXYZ', digits[0], digits[-1],
                      digits[-1] * 2000]  # very long input
        for _ in range(300):
            dec_inputs.append(''.join(rng.choice(digits) for _ in range(rng.randint(1, 40))))
        for _ in range(100):  # with invalid chars mixed in
            s = ''.join(rng.choice(digits) for _ in range(rng.randint(1, 10)))
            pos = rng.randrange(len(s))
            dec_inputs.append(s[:pos] + rng.choice('!@~|}{') + s[pos:])
        for _ in range(50):
            dec_inputs.append(''.join(rng.choice(digits + sign + ' .-+') for _ in range(rng.randint(0, 8))))
        for a in dec_inputs:
            try:
                r = check(conv, 'decode', a, lambda v: ref_decode(v, digits, sign))
            except Exception as e:
                r = ('HARNESS', a, None, repr(e))
            if r:
                failures.append((conv_name, 'decode') + r)

        # ---- roundtrip symmetry ----
        for _ in range(200):
            n = rng.randint(-10**25, 10**25)
            if int(conv.decode(conv.encode(n))) != n:
                failures.append((conv_name, 'roundtrip', 'ASYMMETRY', n,
                                 conv.encode(n), conv.decode(conv.encode(n))))

    for name, conv in convs.items():
        run(name, conv, conv.sign)

    # single-char / empty alphabet must be rejected at construction
    for bad in ['', 'a']:
        try:
            BaseConverter(bad)
            failures.append(('ctor', 'init', 'NO_RAISE', bad, 'ValueError', 'constructed ok'))
        except ValueError:
            pass
        except Exception as e:
            failures.append(('ctor', 'init', 'UNFRIENDLY_EXCEPTION', bad, 'ValueError', repr(e)))

    # summarize
    from collections import Counter
    kinds = Counter(f[2] for f in failures)
    print('total failures: %d' % len(failures))
    for k, c in kinds.items():
        print('  %-28s %d' % (k, c))
    seen = set()
    for f in failures:
        key = (f[0], f[1], f[2])
        if key in seen:
            continue
        seen.add(key)
        print('SAMPLE', f)
    return len(failures)


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
