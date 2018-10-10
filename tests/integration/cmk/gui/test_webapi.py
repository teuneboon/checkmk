#!/usr/bin/env python
# encoding: utf-8

import pytest
import time
import os
import json
import base64
from PIL import Image
from StringIO import StringIO

import cmk
from testlib import web, APIError

def test_global_settings(site, web):
    r = web.get("wato.py")
    assert "Global Settings" in r.text


def test_add_host(web):
    try:
        # Also tests get_host
        web.add_host("test-host", attributes={
            "ipaddress": "127.0.0.1",
        })
    finally:
        web.delete_host("test-host")


def test_add_host_folder_create(web):
    web.add_host("test-host", attributes={
            "ipaddress": "127.0.0.1",
        },
        create_folders=True,
        folder="asd/eee",
    )

    web.delete_host("test-host")


def test_add_host_no_folder_create(web):
    with pytest.raises(APIError) as e:
        web.add_host("test-host", attributes={
                "ipaddress": "127.0.0.1",
            },
            create_folders=False,
            folder="eins/zwei",
            expect_error=True,
        )

    exc_msg = "%s" % e
    assert "Unable to create parent folder" in exc_msg


def test_get_all_hosts_basic(web):
    try:
        web.add_host("test-host-list", attributes={
            "ipaddress": "127.0.0.1",
        })

        hosts = web.get_all_hosts()
        assert "test-host-list" in hosts
    finally:
        web.delete_host("test-host-list")


def test_delete_host(web):
    try:
        web.add_host("test-host-delete", attributes={
            "ipaddress": "127.0.0.1",
        })
    finally:
        web.delete_host("test-host-delete")


def test_get_host_effective_attributes(web):
    try:
        web.add_host("test-host", attributes={
            "ipaddress": "127.0.0.1",
        })

        host = web.get_host("test-host", effective_attributes=False)
        assert "tag_networking" not in host["attributes"]

        host = web.get_host("test-host", effective_attributes=True)
        assert "tag_networking" in host["attributes"]
        assert host["attributes"]["tag_networking"] == "lan"
    finally:
        web.delete_host("test-host")


def test_get_all_hosts_effective_attributes(web):
    try:
        web.add_host("test-host", attributes={
            "ipaddress": "127.0.0.1",
        })

        hosts = web.get_all_hosts(effective_attributes=False)
        host = hosts["test-host"]
        assert "tag_networking" not in host["attributes"]

        hosts = web.get_all_hosts(effective_attributes=True)
        host = hosts["test-host"]
        assert "tag_networking" in host["attributes"]
        assert host["attributes"]["tag_networking"] == "lan"
    finally:
        web.delete_host("test-host")


def test_write_host_tags(web, site):
    try:
        web.add_host("test-host-dmz", attributes={
            "ipaddress": "127.0.0.1",
            "tag_networking": "dmz",
        })

        web.add_host("test-host-lan", attributes={
            "ipaddress": "127.0.0.1",
            "tag_networking": "lan",
        })

        web.add_host("test-host-lan2", attributes={
            "ipaddress": "127.0.0.1",
        })

        hosts = web.get_all_hosts(effective_attributes=True)
        assert hosts["test-host-dmz"]["attributes"]["tag_networking"] == "dmz"
        assert hosts["test-host-lan"]["attributes"]["tag_networking"] == "lan"
        assert hosts["test-host-lan2"]["attributes"]["tag_networking"] == "lan"

        cfg = {
            "FOLDER_PATH": "/",
            "all_hosts": [],
            "ipaddresses": {},
            "host_attributes": {},
        }

        exec(site.read_file("etc/check_mk/conf.d/wato/hosts.mk"), cfg, cfg)

        tags_by_host = {}
        for entry in cfg["all_hosts"]:
            hostname, tag_txt = entry.split("|", 1)
            tags_by_host[hostname] = tag_txt.split("|")


        assert "dmz" in tags_by_host["test-host-dmz"]
        assert "lan" not in tags_by_host["test-host-dmz"]

        assert "dmz" not in tags_by_host["test-host-lan"]
        assert "lan" in tags_by_host["test-host-lan"]

        assert "dmz" not in tags_by_host["test-host-lan2"]
        assert "lan" in tags_by_host["test-host-lan2"]

    finally:
        web.delete_host("test-host-lan2")
        web.delete_host("test-host-lan")
        web.delete_host("test-host-dmz")


# TODO: Parameterize test for cme / non cme
@pytest.mark.parametrize(("group_type"), [ "contact", "host", "service" ])
def test_add_group(web, group_type):
    group_id     = "%s_testgroup_id" % group_type
    group_alias  = "%s_testgroup_alias" % group_type
    try:
        attributes = {"alias": group_alias}

        if cmk.is_managed_edition():
            attributes["customer"] = "provider"

        web.add_group(group_type, group_id, attributes)
        all_groups = web.get_all_groups(group_type)

        assert group_id in all_groups
        assert group_alias == all_groups[group_id]["alias"]

        if cmk.is_managed_edition():
            assert provider == all_groups[group_id]["provider"]
    finally:
        all_groups = web.get_all_groups(group_type)
        if group_id in all_groups:
            web.delete_group(group_type, group_id)


# TODO: Parameterize test for cme / non cme
@pytest.mark.parametrize(("group_type"), [ "contact", "host", "service" ])
def test_edit_group(web, group_type):
    group_id     = "%s_testgroup_id" % group_type
    group_alias  = "%s_testgroup_alias" % group_type
    group_alias2 = "%s_testgroup_otheralias" % group_type
    try:
        attributes = {"alias": group_alias}

        if cmk.is_managed_edition():
            attributes["customer"] = "provider"

        web.add_group(group_type, group_id, attributes)

        attributes["alias"] = group_alias2
        web.edit_group(group_type, group_id, attributes)

        all_groups = web.get_all_groups(group_type)
        assert group_id in all_groups
        assert group_alias2 == all_groups[group_id]["alias"]

        if cmk.is_managed_edition():
            assert "provider" == all_groups[group_id]["customer"]
    finally:
        web.delete_group(group_type, group_id)


# TODO: Parameterize test for cme / non cme
@pytest.mark.parametrize(("group_type"), [ "contact", "host", "service" ])
def test_edit_group_missing(web, group_type):
    group_id     = "%s_testgroup_id" % group_type
    group_alias  = "%s_testgroup_alias" % group_type
    group_alias2 = "%s_testgroup_otheralias" % group_type
    try:
        attributes = {"alias": group_alias}

        if cmk.is_managed_edition():
            attributes["customer"] = "provider"

        web.add_group(group_type, group_id, attributes)
        try:
            #web.edit_group(group_type, group_id, {"alias": group_alias2}, expect_error = True)
            web.edit_group(group_type, "%s_missing" % group_id, {"alias": group_alias2}, expect_error = True)
        except APIError, e:
            assert str(e) != str(None)
            return

        assert False
    finally:
        web.delete_group(group_type, group_id)


# TODO: Parameterize test for cme / non cme
def test_edit_cg_group_with_nagvis_maps(web, site):
    dummy_map_filepath1 = "%s/etc/nagvis/maps/blabla.cfg" % site.root
    dummy_map_filepath2 = "%s/etc/nagvis/maps/bloblo.cfg" % site.root
    try:
        file(dummy_map_filepath1, "w")
        file(dummy_map_filepath2, "w")

        attributes = {
            "alias": "nagvis_test_alias",
            "nagvis_maps": ["blabla"]
        }

        if cmk.is_managed_edition():
            attributes["customer"] = "provider"

        web.add_group("contact", "nagvis_test", attributes)

        attributes["nagvis_maps"] = ["bloblo"]
        web.edit_group("contact", "nagvis_test", attributes)

        all_groups = web.get_all_groups("contact")
        assert "nagvis_test" in all_groups
        assert "bloblo" in all_groups["nagvis_test"]["nagvis_maps"]
    finally:
        web.delete_group("contact", "nagvis_test")
        os.unlink(dummy_map_filepath1)
        os.unlink(dummy_map_filepath2)


# TODO: Parameterize test for cme / non cme
@pytest.mark.parametrize(("group_type"), [ "contact", "host", "service" ])
def test_delete_group(web, group_type):
    group_id     = "%s_testgroup_id" % group_type
    group_alias  = "%s_testgroup_alias" % group_type
    try:
        attributes = {"alias": group_alias}

        if cmk.is_managed_edition():
            attributes["customer"] = "provider"

        web.add_group(group_type, group_id, attributes)
    finally:
        web.delete_group(group_type, group_id)


def test_get_all_users(web):
    users = {"klaus": {"alias": "mr. klaus", "pager": "99221199", "password": "1234"},
             "monroe": {"alias": "mr. monroe"}}
    expected_users = set(["cmkadmin", "automation"] + users.keys())
    try:
        response = web.add_htpasswd_users(users)
        all_users = web.get_all_users()
        assert not expected_users - set(all_users.keys())
    finally:
        web.delete_htpasswd_users(users.keys())


def test_add_htpasswd_users(web):
    users = {"klaus": {"alias": "mr. klaus", "pager": "99221199", "password": "1234"},
             "monroe": {"alias": "mr. monroe"}}
    try:
        web.add_htpasswd_users(users)
    finally:
        web.delete_htpasswd_users(users.keys())


def test_edit_htpasswd_users(web):
    users = {"klaus": {"alias": "mr. klaus", "pager": "99221199", "password": "1234"},
             "monroe": {"alias": "mr. monroe"}}
    try:
        web.add_htpasswd_users(users)
        web.edit_htpasswd_users({"monroe": {"set_attributes": {"alias": "ms. monroe"}},
                                 "klaus": {"unset_attributes": ["pager"]}})
        all_users = web.get_all_users()
        assert not "pager" in all_users["klaus"]
        assert all_users["monroe"]["alias"] == "ms. monroe"
    finally:
        web.delete_htpasswd_users(users.keys())
        pass


def test_discover_servics(web):
    try:
        web.add_host("test-host-discovery", attributes={
            "ipaddress": "127.0.0.1",
        })

        web.discover_services("test-host-discovery")
    finally:
        web.delete_host("test-host-discovery")


def test_activate_changes(web, site):
    try:
        web.add_host("test-host-activate", attributes={
            "ipaddress": "127.0.0.1",
        })

        web.activate_changes()

        result = site.live.query("GET hosts\nColumns: name\nFilter: name = test-host-activate\n")
        assert result == [["test-host-activate"]]
    finally:
        web.delete_host("test-host-activate")
        web.activate_changes()


@pytest.fixture(scope="module")
def graph_test_config(web, site):
    # No graph yet...
    with pytest.raises(APIError) as e:
        web.get_regular_graph("test-host-get-graph", "Check_MK", 0, expect_error=True)
        assert "Cannot calculate graph recipes" in "%s" % e

    # Now add the host
    web.add_host("test-host-get-graph", attributes={
        "ipaddress": "127.0.0.1",
    })
    web.discover_services("test-host-get-graph")
    web.activate_changes()
    site.schedule_check("test-host-get-graph", "Check_MK", 0)

    # Wait for RRD file creation
    # Isn't this a bug that the graph is not instantly available?
    timeout = 10
    print "Checking for graph..."
    while timeout and not site.file_exists("var/check_mk/rrd/test-host-get-graph/Check_MK.rrd"):
        try:
            web.get_regular_graph("test-host-get-graph", "Check_MK", 0, expect_error=True)
        except Exception:
            pass
        timeout -= 1
        time.sleep(1)
        print "Checking for graph..."
    assert site.file_exists("var/check_mk/rrd/test-host-get-graph/Check_MK.rrd"), \
                    "RRD %s is still missing" % "var/check_mk/rrd/test-host-get-graph/Check_MK.rrd"

    yield

    web.delete_host("test-host-get-graph")
    web.activate_changes()


def test_get_graph_api(web, graph_test_config):
    # Now we get a graph
    data = web.get_regular_graph("test-host-get-graph", "Check_MK", 0)

    assert len(data["curves"]) == 4
    assert data["curves"][0]["title"] == "CPU time in user space"
    assert data["curves"][1]["title"] == "CPU time in operating system"
    assert data["curves"][2]["title"] == "Time spent waiting for Check_MK agent"
    assert data["curves"][3]["title"] == "Total execution time"


def test_get_graph_image(web, graph_test_config):
    result = web.post("graph_image.py", data={
        "request": json.dumps({
            "specification": ["template", {
                "service_description" : "Check_MK",
                "site"                : web.site.id,
                "graph_index"         : 0,
                "host_name"           : "test-host-get-graph",
            }],
        }),
    })

    content = result.content

    assert content.startswith('\x89PNG')

    try:
        Image.open(StringIO(content))
    except IOError:
        raise Exception("Failed to open image: %r" % content)


def test_get_graph_notification_image(web, graph_test_config):
    result = web.get("ajax_graph_images.py?host=test-host-get-graph&service=Check_MK")

    # Provides a json list containing base64 encoded PNG images of the current 24h graphs
    encoded_graph_list = json.loads(result.text)
    assert type(encoded_graph_list) == list
    assert len(encoded_graph_list) > 0

    for encoded_graph_image in encoded_graph_list:
        graph_image = base64.b64decode(encoded_graph_image)

        assert graph_image.startswith('\x89PNG')

        try:
            Image.open(StringIO(graph_image))
        except IOError:
            raise Exception("Failed to open image: %r" % graph_image)


def test_get_graph_hover(web, graph_test_config):
    graph_context = {
        u'definition': {
            u'explicit_vertical_range': [None, None],
            u'title': u'Time usage by phase',
            u'horizontal_rules': [],
            u'specification': [
                u'template', {
                    u'service_description': u'Check_MK',
                    u'site': web.site.id,
                    u'graph_index': 0,
                    u'host_name': u'test-host-get-graph'
                }
            ],
            u'consolidation_function': u'max',
            u'metrics': [
                {
                    u'color': u'#87f058',
                    u'line_type': u'stack',
                    u'expression': [
                        u'operator', u'+',
                        [[u'rrd', u'test-host-get-graph', u'test-host-get-graph', u'Check_MK', u'user_time', None, 1], [u'rrd', u'test-host-get-graph', u'test-host-get-graph', u'Check_MK', u'children_user_time', None, 1]]
                    ],
                    u'unit': u's',
                    u'title': u'CPU time in user space'
                },
                {
                    u'color': u'#ff8840', u'line_type': u'stack',
                    u'expression': [
                        u'operator', u'+',
                        [[u'rrd', u'test-host-get-graph', u'test-host-get-graph', u'Check_MK', u'system_time', None, 1], [u'rrd', u'test-host-get-graph', u'test-host-get-graph', u'Check_MK', u'children_system_time', None, 1]]
                    ],
                    u'unit': u's',
                    u'title': u'CPU time in operating system'
                },
                {
                    u'color': u'#00b2ff',
                    u'line_type': u'stack',
                    u'expression': [u'rrd', u'test-host-get-graph', u'test-host-get-graph', u'Check_MK', u'cmk_time_agent', None, 1],
                    u'unit': u's',
                    u'title': u'Time spent waiting for Check_MK agent'
                },
                {
                    u'color': u'#d080af',
                    u'line_type': u'line',
                    u'expression': [u'rrd', u'test-host-get-graph', u'test-host-get-graph', u'Check_MK', u'execution_time', None, 1],
                    u'unit': u's', u'title': u'Total execution time'
                }
            ],
            u'omit_zero_metrics': False,
            u'unit': u's'
        },
        u'graph_id': u'graph_0',
        u'data_range': {
            u'step': 20,
            u"time_range": [time.time()-3600, time.time()]
        },
        u'render_options': {
            u'preview': False,
            u'editing': False,
            u'font_size': 8,
            u'show_graph_time': True,
            u'resizable': True,
            u'show_time_axis': True,
            u'fixed_timerange': False,
            u'foreground_color': u'#000000',
            u'title_format': u'plain',
            u'canvas_color': u'#ffffff',
            u'show_legend': True,
            u'interaction': True,
            u'show_time_range_previews': True,
            u'show_title': True,
            u'show_margin': True,
            u'vertical_axis_width': u'fixed',
            u'show_controls': True,
            u'show_pin': True,
            u'background_color': u'#f8f4f0',
            u'show_vertical_axis': True,
            u'size': [70, 16]
        }
    }

    result = web.post("ajax_graph_hover.py", data={
        "context": json.dumps(graph_context),
        "hover_time": int(time.time() - 300),
    })

    data = result.json()

    assert "rendered_hover_time" in data
    assert len(data["curve_values"]) == 4

    for index, metric in enumerate(graph_context["definition"]["metrics"][::-1]):
        curve_value = data["curve_values"][index]

        assert curve_value["color"] == metric["color"]
        assert curve_value["title"] == metric["title"]

        # TODO: Wait for first values?
        assert curve_value["rendered_value"][0] is None
        assert curve_value["rendered_value"][1] == "n/a"
        #assert isinstance(curve_value["rendered_value"][0], (int, float))
        #assert curve_value["rendered_value"][1] != ""