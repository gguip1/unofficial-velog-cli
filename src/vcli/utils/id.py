from nanoid import generate


def generate_id(size: int = 21) -> str:
    return generate(size=size)
