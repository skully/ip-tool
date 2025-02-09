import pytest
import ipaddress
import json
from unittest.mock import patch
from ip_tool import get_container_networks, check_collision


@pytest.fixture
def mock_ip_command_output():
    return json.dumps([
        {
            "ifname": "eth0",
            "addr_info": [
                {"family": "inet", "local": "10.244.1.5", "prefixlen": 24}
            ]
        }
    ])


@patch("subprocess.run")
def test_get_container_networks(mock_subprocess, mock_ip_command_output):
    """
    Test that get_container_networks correctly extracts the subnet.
    """
    mock_subprocess.return_value.stdout = mock_ip_command_output

    subnet = get_container_networks()
    assert subnet == "10.244.1.0/24"


def test_check_collision_no_conflict(tmp_path):
    """
    Test that check_collision correctly identifies no conflicts.
    """
    file_path = tmp_path / "subnets.txt"
    file_path.write_text("pod1 10.244.1.0/24\npod2 10.244.2.0/24\n")

    with patch("builtins.print") as mock_print:
        check_collision(str(file_path))
        mock_print.assert_any_call("Found none")


def test_check_collision_with_conflict(tmp_path):
    """
    Test that check_collision correctly detects collisions.
    """
    file_path = tmp_path / "subnets.txt"
    file_path.write_text("pod1 10.244.1.0/24\npod2 10.244.1.128/25\n")

    with patch("builtins.print") as mock_print:
        check_collision(str(file_path))
        mock_print.assert_any_call("Collision: 10.244.1.128/25 (pod2), 10.244.1.0/24 (pod1)")

