from __future__ import annotations

from tools.generate_arch_diagram import _filter_architectural_edges
from tools.generate_arch_diagram import _build_region_hierarchy
from tools.generate_arch_diagram import _build_vpc_hierarchy
from tools.generate_arch_diagram import _infer_resource_regions
from tools.generate_arch_diagram import _is_subnet
from tools.generate_arch_diagram import _is_vpc_or_network


def test_network_type_detection_handles_gcp_and_exclusions() -> None:
    assert _is_vpc_or_network("google_compute_network") is True
    assert _is_subnet("google_compute_subnetwork") is True
    assert _is_subnet("aws_db_subnet_group") is False
    assert _is_subnet("aws_elasticache_subnet_group") is False

    # Non-container networking resources must not be treated as VPC containers.
    assert _is_vpc_or_network("aws_network_interface") is False
    assert _is_vpc_or_network("aws_network_acl") is False
    assert _is_vpc_or_network("aws_vpc_peering_connection") is False
    assert _is_vpc_or_network("aws_vpc_endpoint") is False


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


def test_cross_vpc_connector_is_not_duplicated_inside_vpc_clusters() -> None:
    all_resources = {
        "aws_vpc.primary": {},
        "aws_vpc.peer": {},
        "aws_subnet.primary_private": {"vpc_id": "${aws_vpc.primary.id}"},
        "aws_subnet.peer_private": {"vpc_id": "${aws_vpc.peer.id}"},
        "aws_instance.primary_app": {"subnet_id": "${aws_subnet.primary_private.id}"},
        "aws_instance.peer_app": {"subnet_id": "${aws_subnet.peer_private.id}"},
        "aws_vpc_peering_connection.link": {
            "vpc_id": "${aws_vpc.primary.id}",
            "peer_vpc_id": "${aws_vpc.peer.id}",
        },
    }

    edges = {
        ("aws_vpc.primary", "aws_subnet.primary_private"),
        ("aws_vpc.peer", "aws_subnet.peer_private"),
        ("aws_subnet.primary_private", "aws_instance.primary_app"),
        ("aws_subnet.peer_private", "aws_instance.peer_app"),
        ("aws_vpc.primary", "aws_vpc_peering_connection.link"),
        ("aws_vpc.peer", "aws_vpc_peering_connection.link"),
    }

    hierarchy = _build_vpc_hierarchy(all_resources, edges)

    assert "aws_vpc.primary" in hierarchy
    assert "aws_vpc.peer" in hierarchy

    # The peering connector spans multiple VPCs and should stay outside VPC clusters.
    assert "aws_vpc_peering_connection.link" not in hierarchy["aws_vpc.primary"].get(
        "other", []
    )
    assert "aws_vpc_peering_connection.link" not in hierarchy["aws_vpc.peer"].get(
        "other", []
    )


def test_subnet_group_backed_services_stay_inside_vpc_hierarchy() -> None:
    all_resources = {
        "aws_vpc.main": {},
        "aws_subnet.private_a": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_subnet.private_b": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_db_subnet_group.app": {
            "subnet_ids": [
                "${aws_subnet.private_a.id}",
                "${aws_subnet.private_b.id}",
            ]
        },
        "aws_db_instance.app": {"db_subnet_group_name": "${aws_db_subnet_group.app.name}"},
        "aws_elasticache_subnet_group.app": {
            "subnet_ids": [
                "${aws_subnet.private_a.id}",
                "${aws_subnet.private_b.id}",
            ]
        },
        "aws_elasticache_cluster.app": {
            "subnet_group_name": "${aws_elasticache_subnet_group.app.name}"
        },
    }

    edges = {
        ("aws_vpc.main", "aws_subnet.private_a"),
        ("aws_vpc.main", "aws_subnet.private_b"),
        ("aws_subnet.private_a", "aws_db_subnet_group.app"),
        ("aws_subnet.private_b", "aws_db_subnet_group.app"),
        ("aws_subnet.private_a", "aws_elasticache_subnet_group.app"),
        ("aws_subnet.private_b", "aws_elasticache_subnet_group.app"),
        ("aws_db_subnet_group.app", "aws_db_instance.app"),
        ("aws_elasticache_subnet_group.app", "aws_elasticache_cluster.app"),
    }

    hierarchy = _build_vpc_hierarchy(all_resources, edges)

    private_a_resources = set(hierarchy["aws_vpc.main"].get("aws_subnet.private_a", []))
    private_b_resources = set(hierarchy["aws_vpc.main"].get("aws_subnet.private_b", []))
    placed_resources = private_a_resources | private_b_resources

    # Subnet-group-backed resources should be placed inside the VPC subnets,
    # not left outside the VPC hierarchy.
    assert "aws_db_instance.app" in placed_resources
    assert "aws_elasticache_cluster.app" in placed_resources


def test_multi_subnet_control_plane_edges_drop_public_subnet_links() -> None:
    all_resources = {
        "aws_subnet.public": {"map_public_ip_on_launch": True},
        "aws_subnet.private": {},
        "aws_eks_cluster.main": {
            "subnet_ids": [
                "${aws_subnet.public.id}",
                "${aws_subnet.private.id}",
            ]
        },
    }

    edges = {
        ("aws_subnet.public", "aws_eks_cluster.main"),
        ("aws_subnet.private", "aws_eks_cluster.main"),
    }

    filtered = _filter_architectural_edges(all_resources, edges)

    assert ("aws_subnet.public", "aws_eks_cluster.main") not in filtered
    assert ("aws_subnet.private", "aws_eks_cluster.main") in filtered


def test_resource_regions_are_inferred_from_provider_alias_and_tags() -> None:
    all_resources = {
        "aws_vpc.primary": {"tags": {"Region": "us-east-1"}},
        "aws_subnet.primary_a": {"vpc_id": "${aws_vpc.primary.id}"},
        "aws_vpc.dr": {"provider": "aws.us-west-2"},
        "aws_subnet.dr_a": {"vpc_id": "${aws_vpc.dr.id}"},
    }
    edges = {
        ("aws_vpc.primary", "aws_subnet.primary_a"),
        ("aws_vpc.dr", "aws_subnet.dr_a"),
    }

    resource_regions = _infer_resource_regions(all_resources, edges)

    assert resource_regions["aws_vpc.primary"] == "us-east-1"
    assert resource_regions["aws_subnet.primary_a"] == "us-east-1"
    assert resource_regions["aws_vpc.dr"] == "us-west-2"
    assert resource_regions["aws_subnet.dr_a"] == "us-west-2"


def test_region_hierarchy_only_activates_for_multi_region_architecture() -> None:
    all_resources = {
        "aws_vpc.main": {"tags": {"Region": "us-east-1"}},
        "aws_subnet.main_a": {"vpc_id": "${aws_vpc.main.id}"},
        "aws_instance.app": {"subnet_id": "${aws_subnet.main_a.id}"},
    }
    edges = {
        ("aws_vpc.main", "aws_subnet.main_a"),
        ("aws_subnet.main_a", "aws_instance.app"),
    }

    hierarchy = _build_region_hierarchy(all_resources, edges)
    assert hierarchy == {}

    all_resources["aws_vpc.dr"] = {"provider": "aws.us-west-2"}
    all_resources["aws_subnet.dr_a"] = {"vpc_id": "${aws_vpc.dr.id}"}
    edges.add(("aws_vpc.dr", "aws_subnet.dr_a"))

    hierarchy = _build_region_hierarchy(all_resources, edges)
    assert set(hierarchy.keys()) == {"us-east-1", "us-west-2"}
    assert "aws_vpc.main" in hierarchy["us-east-1"]
    assert "aws_vpc.dr" in hierarchy["us-west-2"]
