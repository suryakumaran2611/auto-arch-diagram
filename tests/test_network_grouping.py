from __future__ import annotations

from tools.generate_arch_diagram import _build_vpc_hierarchy
from tools.generate_arch_diagram import _is_subnet
from tools.generate_arch_diagram import _is_vpc_or_network


def test_network_type_detection_handles_gcp_and_exclusions() -> None:
    assert _is_vpc_or_network("google_compute_network") is True
    assert _is_subnet("google_compute_subnetwork") is True

    # Non-container networking resources must not be treated as VPC containers.
    assert _is_vpc_or_network("aws_network_interface") is False
    assert _is_vpc_or_network("aws_network_acl") is False


def test_vpc_hierarchy_is_deterministic_and_deduplicates_other_resources() -> None:
    all_resources = {
        "aws_vpc.main": {},
        "aws_subnet.a": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_subnet.b": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_instance.app": {},
        "aws_internet_gateway.igw": {},
    }

    # Intentionally include both directions for IGW edge and two subnet edges for app.
    edges = {
        ("aws_vpc.main", "aws_subnet.a"),
        ("aws_vpc.main", "aws_subnet.b"),
        ("aws_subnet.a", "aws_instance.app"),
        ("aws_subnet.b", "aws_instance.app"),
        ("aws_vpc.main", "aws_internet_gateway.igw"),
        ("aws_internet_gateway.igw", "aws_vpc.main"),
    }

    hierarchy = _build_vpc_hierarchy(all_resources, edges)

    assert "aws_vpc.main" in hierarchy

    # Multi-subnet resource should be lifted to VPC-level placement.
    assert "aws_instance.app" in hierarchy["aws_vpc.main"]["other"]
    assert "aws_instance.app" not in hierarchy["aws_vpc.main"].get("aws_subnet.a", [])
    assert "aws_instance.app" not in hierarchy["aws_vpc.main"].get("aws_subnet.b", [])

    # "other" resources should not be duplicated even with bidirectional edges.
    assert hierarchy["aws_vpc.main"]["other"].count("aws_internet_gateway.igw") == 1


def test_multi_subnet_resource_is_lifted_to_vpc_level() -> None:
    all_resources = {
        "aws_vpc.main": {},
        "aws_subnet.a": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_subnet.b": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_instance.shared": {
            "subnet_ids": ["${aws_subnet.a.id}", "${aws_subnet.b.id}"]
        },
    }

    edges = {
        ("aws_vpc.main", "aws_subnet.a"),
        ("aws_vpc.main", "aws_subnet.b"),
        ("aws_subnet.a", "aws_instance.shared"),
        ("aws_subnet.b", "aws_instance.shared"),
    }

    hierarchy = _build_vpc_hierarchy(all_resources, edges)

    assert "aws_vpc.main" in hierarchy
    assert "other" in hierarchy["aws_vpc.main"]
    assert "aws_instance.shared" in hierarchy["aws_vpc.main"]["other"]
    assert "aws_instance.shared" not in hierarchy["aws_vpc.main"].get("aws_subnet.a", [])
    assert "aws_instance.shared" not in hierarchy["aws_vpc.main"].get("aws_subnet.b", [])
