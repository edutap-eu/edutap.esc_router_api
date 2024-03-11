import uuid


class ESCN_Factory_Exception(Exception):
    pass


def generate_ESCN(pic: str, prefix: int = 1) -> uuid.uuid1:
    if len(pic) == 9 and pic.isdigit():
        node: int = int(f"{prefix:03d}{pic}", 16)
        return uuid.uuid1(node=node)
    raise ESCN_Factory_Exception("PIC is not in valid format")
