"""
Exact linear algebra over the rationals, written from scratch so every step
of the book's algorithms is visible. Only the Python standard library is used.

Matrices are lists of rows; entries are converted to fractions.Fraction so that
row reduction never suffers from rounding error.

Run this file directly to see a demonstration of every function.
"""
from fractions import Fraction
from itertools import permutations


# ---------------------------------------------------------------- basics
def mat(rows):
    """Copy a list of rows into a matrix of Fractions."""
    return [[Fraction(x) for x in row] for row in rows]


def shape(A):
    return len(A), (len(A[0]) if A else 0)


def identity(n):
    return [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]


def transpose(A):
    return [list(col) for col in zip(*A)]


def matmul(A, B):
    m, k = shape(A)
    k2, n = shape(B)
    if k != k2:
        raise ValueError(f"cannot multiply {m}x{k} by {k2}x{n}")
    return [[sum(A[i][t] * B[t][j] for t in range(k)) for j in range(n)]
            for i in range(m)]


def matvec(A, v):
    return [sum(a * x for a, x in zip(row, v)) for row in A]


def show(A, name=None):
    if name:
        print(f"{name} =")
    width = max((len(str(x)) for row in A for x in row), default=1)
    for row in A:
        print("  [" + "  ".join(str(x).rjust(width) for x in row) + "]")


# ---------------------------------------------------------------- elimination
def rref(A, verbose=False):
    """
    Return (R, pivot_columns) where R is the reduced row echelon form of A.

    Uses exactly the three elementary row operations of Chapter 2:
      swap two rows, scale a row by a non-zero scalar, add a multiple of a row.
    """
    R = [row[:] for row in mat(A)]
    m, n = shape(R)
    pivots = []
    r = 0
    for c in range(n):
        # find a row at or below r with a non-zero entry in column c
        p = next((i for i in range(r, m) if R[i][c] != 0), None)
        if p is None:
            continue
        if p != r:
            R[r], R[p] = R[p], R[r]
            if verbose:
                print(f"R{r+1} <-> R{p+1}")
        lead = R[r][c]
        if lead != 1:
            R[r] = [x / lead for x in R[r]]
            if verbose:
                print(f"R{r+1} <- R{r+1} / {lead}")
        for i in range(m):
            if i != r and R[i][c] != 0:
                f = R[i][c]
                R[i] = [a - f * b for a, b in zip(R[i], R[r])]
                if verbose:
                    print(f"R{i+1} <- R{i+1} - ({f}) R{r+1}")
        pivots.append(c)
        r += 1
        if r == m:
            break
    return R, pivots


def rank(A):
    return len(rref(A)[1])


def solve(A, b):
    """
    Solve A x = b.

    Returns (particular_solution, null_space_basis) so that the full solution
    set is  particular + span(null_space_basis),  or None if inconsistent.
    """
    m, n = shape(A)
    aug = [list(row) + [bi] for row, bi in zip(mat(A), b)]
    R, piv = rref(aug)
    if n in piv:                      # pivot in the augmented column: 0 = 1
        return None
    x = [Fraction(0)] * n
    for i, c in enumerate(piv):
        x[c] = R[i][n]
    return x, null_space(A)


def null_space(A):
    """Basis of {x : A x = 0}: one vector per free variable."""
    R, piv = rref(A)
    m, n = shape(R)
    free = [c for c in range(n) if c not in piv]
    basis = []
    for f in free:
        v = [Fraction(0)] * n
        v[f] = Fraction(1)
        for i, c in enumerate(piv):
            v[c] = -R[i][f]
        basis.append(v)
    return basis


def column_space(A):
    """Basis of the column space: the pivot columns of the ORIGINAL matrix."""
    _, piv = rref(A)
    At = transpose(mat(A))
    return [At[c] for c in piv]


def row_space(A):
    """Basis of the row space: the non-zero rows of the RREF."""
    R, piv = rref(A)
    return [R[i] for i in range(len(piv))]


def inverse(A):
    """Invert A by reducing [A | I] to [I | A^-1]; raises if A is singular."""
    n, n2 = shape(A)
    if n != n2:
        raise ValueError("only square matrices can be invertible")
    aug = [list(row) + list(e) for row, e in zip(mat(A), identity(n))]
    R, piv = rref(aug)
    if piv[:n] != list(range(n)):
        raise ValueError("matrix is singular")
    return [row[n:] for row in R]


# ---------------------------------------------------------------- determinants
def sign(perm):
    """Sign of a permutation given as a tuple: (-1)^(number of inversions)."""
    inv = sum(1 for i in range(len(perm)) for j in range(i + 1, len(perm))
              if perm[i] > perm[j])
    return -1 if inv % 2 else 1


def det_leibniz(A):
    """Definition of the determinant: sum over all n! permutations. O(n * n!)."""
    A = mat(A)
    n = len(A)
    total = Fraction(0)
    for p in permutations(range(n)):
        term = Fraction(sign(p))
        for i in range(n):
            term *= A[i][p[i]]
        total += term
    return total


def det_cofactor(A):
    """Laplace expansion along the first row. Still exponential."""
    A = mat(A)
    n = len(A)
    if n == 1:
        return A[0][0]
    total = Fraction(0)
    for j in range(n):
        minor = [row[:j] + row[j + 1:] for row in A[1:]]
        total += (-1) ** j * A[0][j] * det_cofactor(minor)
    return total


def det(A):
    """
    Determinant by Gaussian elimination, O(n^3):
    a swap flips the sign, adding a multiple of a row changes nothing,
    and the determinant of a triangular matrix is the product of its diagonal.
    """
    U = [row[:] for row in mat(A)]
    n = len(U)
    d = Fraction(1)
    for c in range(n):
        p = next((i for i in range(c, n) if U[i][c] != 0), None)
        if p is None:
            return Fraction(0)
        if p != c:
            U[c], U[p] = U[p], U[c]
            d = -d
        d *= U[c][c]
        for i in range(c + 1, n):
            f = U[i][c] / U[c][c]
            U[i] = [a - f * b for a, b in zip(U[i], U[c])]
    return d


def adjugate(A):
    A = mat(A)
    n = len(A)
    C = [[(-1) ** (i + j) * det([r[:j] + r[j + 1:] for k, r in enumerate(A) if k != i])
          for j in range(n)] for i in range(n)]
    return transpose(C)


def cramer(A, b):
    """Cramer's rule: x_i = det(A_i) / det(A), A_i = A with column i replaced by b."""
    A = mat(A)
    D = det(A)
    if D == 0:
        raise ValueError("Cramer's rule needs det(A) != 0")
    xs = []
    for i in range(len(A)):
        Ai = [row[:i] + [Fraction(bi)] + row[i + 1:] for row, bi in zip(A, b)]
        xs.append(det(Ai) / D)
    return xs


# ---------------------------------------------------------------- polynomials
def char_poly(A):
    """
    Coefficients [c_n, ..., c_1, c_0] of p(t) = det(tI - A) (monic, c_n = 1),
    computed exactly with the Faddeev-LeVerrier recursion:
        M_0 = 0, c_n = 1
        M_k = A M_{k-1} + c_{n-k+1} I,   c_{n-k} = -tr(A M_k) / k
    """
    A = mat(A)
    n = len(A)
    coeffs = [Fraction(1)]
    M = [[Fraction(0)] * n for _ in range(n)]
    I = identity(n)
    for k in range(1, n + 1):
        AM = matmul(A, M)
        M = [[AM[i][j] + coeffs[-1] * I[i][j] for j in range(n)] for i in range(n)]
        AM = matmul(A, M)
        coeffs.append(-sum(AM[i][i] for i in range(n)) / k)
    return coeffs


def poly_eval(coeffs, t):
    v = Fraction(0)
    for c in coeffs:
        v = v * t + c
    return v


def rational_roots(coeffs):
    """All rational roots of an integer/rational polynomial (rational root test)."""
    from math import gcd
    # clear denominators
    lcm = 1
    for c in coeffs:
        lcm = lcm * c.denominator // gcd(lcm, c.denominator)
    ints = [int(c * lcm) for c in coeffs]
    while ints and ints[-1] == 0:        # factor out t = 0
        ints.pop()
    roots = {Fraction(0)} if len(ints) < len(coeffs) else set()
    if len(ints) <= 1:
        return sorted(roots)
    a0, an = abs(ints[-1]), abs(ints[0])

    def divisors(k):
        return [d for d in range(1, k + 1) if k % d == 0]

    for p in divisors(a0):
        for q in divisors(an):
            for s in (1, -1):
                r = Fraction(s * p, q)
                if poly_eval([Fraction(c) for c in ints], r) == 0:
                    roots.add(r)
    return sorted(roots)


def eigen_rational(A):
    """
    Eigenvalues that happen to be rational, each with a basis of its eigenspace
    (the null space of A - lambda I).  Returns {lambda: [basis vectors]}.
    """
    A = mat(A)
    n = len(A)
    out = {}
    for lam in rational_roots(char_poly(A)):
        B = [[A[i][j] - (lam if i == j else 0) for j in range(n)] for i in range(n)]
        out[lam] = null_space(B)
    return out


def diagonalize(A):
    """
    Return (P, D) with A = P D P^-1 if A is diagonalizable over Q, else None.
    A is diagonalizable iff the eigenspace dimensions add up to n.
    """
    n = len(A)
    eig = eigen_rational(A)
    cols, diag = [], []
    for lam, basis in eig.items():
        for v in basis:
            cols.append(v)
            diag.append(lam)
    if len(cols) < n:
        return None
    P = transpose(cols)
    D = [[diag[i] if i == j else Fraction(0) for j in range(n)] for i in range(n)]
    return P, D


# ---------------------------------------------------------------- coordinates
def coordinates(basis, v):
    """[v]_B : solve  sum c_i b_i = v."""
    sol = solve(transpose(mat(basis)), v)
    if sol is None:
        raise ValueError("v is not in the span of the basis")
    return sol[0]


def change_of_basis(B, C):
    """Matrix P_{C<-B} whose j-th column is [b_j]_C, so [v]_C = P [v]_B."""
    return transpose([coordinates(C, b) for b in B])


# ---------------------------------------------------------------- inner products
def dot(u, v):
    return sum(Fraction(a) * Fraction(b) for a, b in zip(u, v))


def gram_schmidt(vectors):
    """Orthogonal (not normalised, to stay rational) basis of span(vectors)."""
    out = []
    for v in vectors:
        w = [Fraction(x) for x in v]
        for u in out:
            c = dot(w, u) / dot(u, u)
            w = [a - c * b for a, b in zip(w, u)]
        if any(w):
            out.append(w)
    return out


# ---------------------------------------------------------------- demo
if __name__ == "__main__":
    print("== Chapter 2: Gaussian elimination, showing each row operation ==")
    A = [[1, 2, -1], [2, 3, 1], [3, 5, 0]]
    b = [3, 8, 11]
    R, piv = rref([r + [bi] for r, bi in zip(A, b)], verbose=True)
    show(R, "RREF of [A|b]")
    x0, N = solve(A, b)
    print("particular solution:", [str(t) for t in x0])
    print("null space basis   :", [[str(t) for t in v] for v in N])
    for t in range(-2, 3):          # every x0 + t*n really is a solution
        x = [a + t * c for a, c in zip(x0, N[0])]
        assert matvec(mat(A), x) == [Fraction(v) for v in b]

    print("\n== Chapter 3: inverse via [A|I] -> [I|A^-1] ==")
    M = [[2, 1, 1], [1, 3, 2], [1, 0, 0]]
    Minv = inverse(M)
    show(Minv, "M^-1")
    assert matmul(mat(M), Minv) == identity(3)

    print("\n== Chapter 4: three ways to compute a determinant ==")
    for f in (det_leibniz, det_cofactor, det):
        print(f"{f.__name__:13s}", f(M))
    assert det_leibniz(M) == det_cofactor(M) == det(M)
    # A^-1 = adj(A) / det(A)
    assert [[x / det(M) for x in row] for row in adjugate(M)] == Minv
    print("Cramer:", [str(t) for t in cramer(M, [1, 2, 3])])

    print("\n== Chapters 6-7: four fundamental subspaces, rank-nullity ==")
    A = [[1, 2, 0, 1], [2, 4, 1, 4], [3, 6, 1, 5]]
    print("rank =", rank(A), " nullity =", len(null_space(A)), " n =", len(A[0]))
    assert rank(A) + len(null_space(A)) == len(A[0])
    print("column space basis:", [[str(t) for t in v] for v in column_space(A)])
    print("row space basis   :", [[str(t) for t in v] for v in row_space(A)])

    print("\n== Chapter 9: change of basis ==")
    B = [[1, 1], [1, -1]]
    C = [[2, 0], [0, 3]]
    P = change_of_basis(B, C)
    show(P, "P_{C<-B}")
    v = [5, 1]
    assert matvec(P, coordinates(B, v)) == coordinates(C, v)

    print("\n== Chapter 10: eigenvalues and diagonalisation ==")
    A = [[4, -1, 6], [2, 1, 6], [2, -1, 8]]      # eigenvalues 2, 2, 9
    print("char poly coefficients:", [str(c) for c in char_poly(A)])
    for lam, basis in eigen_rational(A).items():
        print(f"lambda = {lam}: eigenspace basis {[[str(t) for t in v] for v in basis]}")
    P, D = diagonalize(A)
    assert matmul(matmul(P, D), inverse(P)) == mat(A)
    show(D, "D")
    # Same characteristic-polynomial shape (a double root), but the eigenspace
    # of the double root is only 1-dimensional, so it is NOT diagonalizable.
    K = [[4, 1, 2], [0, 2, 0], [1, 1, 3]]        # eigenvalues 2, 2, 5
    print("char poly of K:", [str(c) for c in char_poly(K)])
    print("eigenspace dims of K:", {str(l): len(b) for l, b in eigen_rational(K).items()})
    assert diagonalize(K) is None
    J = [[1, 1], [0, 1]]               # a Jordan block is NOT diagonalizable
    print("diagonalize([[1,1],[0,1]]) ->", diagonalize(J))

    print("\n== Chapter 11 (add-on): Gram-Schmidt ==")
    Q = gram_schmidt([[1, 1, 0], [1, 0, 1], [0, 1, 1]])
    for q in Q:
        print("  ", [str(t) for t in q])
    assert all(dot(Q[i], Q[j]) == 0 for i in range(3) for j in range(i))
    print("\nall checks passed")
