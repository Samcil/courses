"""
Chapter 1: fields.

* Zp      - arithmetic modulo a prime, inverses by the extended Euclidean algorithm
* brute-force verification of the field axioms for Z_n (fails exactly when n is composite)
* complex n-th roots via polar form (Theorem 1.10)
"""
import cmath
import math
from itertools import product


def ext_gcd(a, b):
    """Return (g, s, t) with s*a + t*b = g = gcd(a, b)  (Bezout, Lemma 1.3)."""
    if b == 0:
        return a, 1, 0
    g, s, t = ext_gcd(b, a % b)
    # g = s*b + t*(a - (a//b)*b) = t*a + (s - (a//b)*t)*b
    return g, t, s - (a // b) * t


class Zp:
    """An element of Z_p. Division raises ZeroDivisionError if p is not prime and a is a zero divisor."""

    def __init__(self, a, p):
        self.p = p
        self.a = a % p

    def _coerce(self, other):
        return other if isinstance(other, Zp) else Zp(other, self.p)

    def __add__(self, o):
        return Zp(self.a + self._coerce(o).a, self.p)

    def __sub__(self, o):
        return Zp(self.a - self._coerce(o).a, self.p)

    def __mul__(self, o):
        return Zp(self.a * self._coerce(o).a, self.p)

    __radd__, __rmul__ = __add__, __mul__

    def __neg__(self):
        return Zp(-self.a, self.p)

    def inverse(self):
        g, s, _ = ext_gcd(self.a, self.p)
        if g != 1:
            raise ZeroDivisionError(f"{self.a} has no inverse mod {self.p} (gcd = {g})")
        return Zp(s, self.p)

    def __truediv__(self, o):
        return self * self._coerce(o).inverse()

    def __eq__(self, o):
        return self.a == self._coerce(o).a

    def __hash__(self):
        return hash((self.a, self.p))

    def __repr__(self):
        return f"{self.a} (mod {self.p})"


def is_field_Zn(n):
    """Check every field axiom for Z_n by brute force."""
    E = range(n)
    add = lambda a, b: (a + b) % n
    mul = lambda a, b: (a * b) % n
    for a, b, c in product(E, repeat=3):
        if add(add(a, b), c) != add(a, add(b, c)): return False
        if mul(mul(a, b), c) != mul(a, mul(b, c)): return False
        if mul(a, add(b, c)) != add(mul(a, b), mul(a, c)): return False
    for a in E:
        if not any(add(a, b) == 0 for b in E): return False
        if a != 0 and not any(mul(a, b) == 1 for b in E): return False
    return True


def nth_roots(w, n):
    """All solutions of z^n = w (Theorem 1.10)."""
    rho, phi = abs(w), cmath.phase(w)
    return [rho ** (1 / n) * cmath.exp(1j * (phi + 2 * math.pi * k) / n) for k in range(n)]


if __name__ == "__main__":
    print("Which Z_n are fields?",
          [n for n in range(2, 20) if is_field_Zn(n)])          # exactly the primes

    x = (Zp(2, 7) - 4) / 3                                        # solve 3x + 4 = 2 in Z_7
    print("3x + 4 = 2 in Z_7  ->  x =", x)
    assert Zp(3, 7) * x + 4 == 2

    try:
        Zp(2, 6).inverse()
    except ZeroDivisionError as e:
        print("Z_6:", e)

    # zero divisors make polynomials misbehave: x^2 - x has 4 roots in Z_6
    print("roots of x^2 - x in Z_6:", [a for a in range(6) if (a * a - a) % 6 == 0])

    print("\ncube roots of -8i:")
    for z in nth_roots(-8j, 3):
        print(f"  {z.real:+.4f} {z.imag:+.4f}i   check z^3 = {z**3:.4f}")
        assert abs(z ** 3 - (-8j)) < 1e-9

    roots = nth_roots(1, 7)
    print("sum of 7th roots of unity:", abs(sum(roots)) < 1e-12)

    print("(1+i)^20 =", (1 + 1j) ** 20)
