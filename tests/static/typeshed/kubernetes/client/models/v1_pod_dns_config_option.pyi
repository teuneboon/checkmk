# Stubs for kubernetes.client.models.v1_pod_dns_config_option (Python 2)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional

class V1PodDNSConfigOption:
    swagger_types: Any = ...
    attribute_map: Any = ...
    discriminator: Any = ...
    name: Any = ...
    value: Any = ...
    def __init__(self, name: Optional[Any] = ..., value: Optional[Any] = ...) -> None: ...
    @property
    def name(self): ...
    @name.setter
    def name(self, name: Any) -> None: ...
    @property
    def value(self): ...
    @value.setter
    def value(self, value: Any) -> None: ...
    def to_dict(self): ...
    def to_str(self): ...
    def __eq__(self, other: Any): ...
    def __ne__(self, other: Any): ...