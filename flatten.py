"""Helper module for a simple speckle object tree flattening."""
from typing import Tuple, Optional

from specklepy.objects import Base
from specklepy.objects.other import Instance, Transform


# def flatten_base(base: Base) -> Iterable[Base]:
#     """Take a base and flatten it to an iterable of bases."""
#     if hasattr(base, "elements") and base["elements"] is not None:
#         for element in base["elements"]:
#             yield from flatten_base(element)
#     yield base


def extract_base_and_transform(
    base: Base,
    inherited_instance_id: Optional[str] = None,
    inherited_transform: Optional[Transform] = None,
) -> Tuple[Base, str, Optional[Transform]]:
    """
    Recursively extracts Base objects and their associated transforms from a hierarchy of Base objects.

    Parameters:
    - base (Base): The Base object to start the extraction from.
    - inherited_transform (Transform, optional): A Transform object that has been inherited from a parent Instance.

    Yields:
    - tuple: A tuple containing a Base object and an associated Transform object or None.
    """
    current_id = base.id if hasattr(base, "id") else inherited_instance_id

    # If the current object is an Instance, we capture its transform and use it for its definition
    if isinstance(base, Instance):
        current_transform = base.transform or inherited_transform
        # Traverse the definition, if it exists
        if base.definition:
            yield from extract_base_and_transform(
                base.definition,
                current_id,
                current_transform,
            )
    else:
        # For non-Instance Base objects, we yield them with the inherited transform
        yield base, current_id, inherited_transform
        # If the Base object has elements, we traverse them and pass along the inherited transform
        if hasattr(base, "elements") and base["elements"] is not None:
            for element in base.elements:
                yield from extract_base_and_transform(
                    element, current_id, inherited_transform
                )
