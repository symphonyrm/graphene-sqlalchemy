from functools import partial

from graphene.types import Scalar
from graphql.language.ast import IntValue


def coerce_int(min_value, max_value, value):
    try:
        num = int(value)
    except ValueError:
        try:
            num = int(float(value))
        except ValueError:
            return None
    if min_value <= num <= max_value:
        return num


def parse_literal(min_value, max_value, ast):
    if isinstance(ast, IntValue):
        num = int(ast.value)
        if min_value <= num <= max_value:
            return num


class UnsignedInt8(Scalar):
    """
    The `UnsignedInt8` scalar type represents non-fractional unsigned whole
    numeric values. `UnsignedInt8` can represent values between 0 and 2^8 - 1.
    """

    serialize = partial(coerce_int, 0, 2**8 - 1)
    parse_value = partial(coerce_int, 0, 2**8 - 1)
    parse_literal = partial(parse_literal, 0, 2**8 - 1)


class SignedInt8(Scalar):
    """
    The `SignedInt8` scalar type represents non-fractional unsigned whole
    numeric values. `SignedInt8` can represent values between -(2^7) and 2^7 - 1.
    """

    serialize = partial(coerce_int, -(2**7), 2**7 - 1)
    parse_value = partial(coerce_int, -(2**7), 2**7 - 1)
    parse_literal = partial(parse_literal, -(2**7), 2**7 - 1)


class UnsignedInt16(Scalar):
    """
    The `UnsignedInt16` scalar type represents non-fractional unsigned whole
    numeric values. `UnsignedInt16` can represent values between 0 and 2^16 - 1.
    """

    serialize = partial(coerce_int, 0, 2**16 - 1)
    parse_value = partial(coerce_int, 0, 2**16 - 1)
    parse_literal = partial(parse_literal, 0, 2**16 - 1)


class SignedInt16(Scalar):
    """
    The `SignedInt16` scalar type represents non-fractional unsigned whole
    numeric values. `SignedInt16` can represent values between -(2^15) and 2^15 - 1.
    """

    serialize = partial(coerce_int, -(2**15), 2**15 - 1)
    parse_value = partial(coerce_int, -(2**15), 2**15 - 1)
    parse_literal = partial(parse_literal, -(2**15), 2**15 - 1)


class UnsignedInt24(Scalar):
    """
    The `UnsignedInt24` scalar type represents non-fractional unsigned whole
    numeric values. `UnsignedInt24` can represent values between 0 and 2^24 - 1.
    """

    serialize = partial(coerce_int, 0, 2**24 - 1)
    parse_value = partial(coerce_int, 0, 2**24 - 1)
    parse_literal = partial(parse_literal, 0, 2**24 - 1)


class SignedInt24(Scalar):
    """
    The `SignedInt32` scalar type represents non-fractional unsigned whole
    numeric values. `SignedInt32` can represent values between -(2^31) and 2^31 - 1.
    """

    serialize = partial(coerce_int, -(2**23), 2**23 - 1)
    parse_value = partial(coerce_int, -(2**23), 2**23 - 1)
    parse_literal = partial(parse_literal, -(2**23), 2**23 - 1)


class UnsignedInt32(Scalar):
    """
    The `UnsignedInt32` scalar type represents non-fractional unsigned whole
    numeric values. `UnsignedInt32` can represent values between 0 and 2^32 - 1.
    """

    serialize = partial(coerce_int, 0, 2**32 - 1)
    parse_value = partial(coerce_int, 0, 2**32 - 1)
    parse_literal = partial(parse_literal, 0, 2**32 - 1)


class SignedInt32(Scalar):
    """
    The `SignedInt32` scalar type represents non-fractional unsigned whole
    numeric values. `SignedInt32` can represent values between -(2^31) and 2^31 - 1.
    """

    serialize = partial(coerce_int, -(2**31), 2**31 - 1)
    parse_value = partial(coerce_int, -(2**31), 2**31 - 1)
    parse_literal = partial(parse_literal, -(2**31), 2**31 - 1)
