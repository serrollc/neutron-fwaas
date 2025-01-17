# Copyright 2013 Big Switch Networks, Inc.
# All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import copy

import mock
from neutron.tests import base
from neutron.tests.unit.api.v2 import test_base as test_api_v2
from neutron.tests.unit.extensions import base as test_api_v2_extension
from neutron_lib.db import constants as db_const
from oslo_utils import uuidutils
from webob import exc
import webtest

from neutron_fwaas.common import fwaas_constants
from neutron_fwaas.extensions import firewall

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path
_long_name = 'x' * (db_const.NAME_FIELD_SIZE + 1)
_long_description = 'y' * (db_const.DESCRIPTION_FIELD_SIZE + 1)


class FirewallExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = 'json'

    def setUp(self):
        super(FirewallExtensionTestCase, self).setUp()
        plural_mappings = {'firewall_policy': 'firewall_policies'}
        self._setUpExtension(
            'neutron_fwaas.extensions.firewall.FirewallPluginBase',
            fwaas_constants.FIREWALL, firewall.RESOURCE_ATTRIBUTE_MAP,
            firewall.Firewall, 'fw', plural_mappings=plural_mappings)

    def test_create_firewall(self):
        fw_id = _uuid()
        project_id = _uuid()
        data = {'firewall': {'description': 'descr_firewall1',
                             'name': 'firewall1',
                             'admin_state_up': True,
                             'firewall_policy_id': _uuid(),
                             'shared': False,
                             'project_id': project_id,
                             'tenant_id': project_id}}
        return_value = copy.copy(data['firewall'])
        return_value.update({'id': fw_id})
        # since 'shared' is hidden
        del return_value['shared']

        instance = self.plugin.return_value
        instance.create_firewall.return_value = return_value
        res = self.api.post(_get_path('fw/firewalls', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_firewall.assert_called_with(mock.ANY,
                                                    firewall=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall', res)
        self.assertEqual(return_value, res['firewall'])

    def test_create_firewall_invalid_long_name(self):
        project_id = _uuid()
        data = {'firewall': {'description': 'descr_firewall1',
                             'name': _long_name,
                             'admin_state_up': True,
                             'firewall_policy_id': _uuid(),
                             'shared': False,
                             'project_id': project_id,
                             'tenant_id': project_id}}
        res = self.api.post(_get_path('fw/firewalls', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            status=exc.HTTPBadRequest.code)
        self.assertIn('Invalid input for name', res.body.decode('utf-8'))

    def test_create_firewall_invalid_long_description(self):
        project_id = _uuid()
        data = {'firewall': {'description': _long_description,
                             'name': 'firewall1',
                             'admin_state_up': True,
                             'firewall_policy_id': _uuid(),
                             'shared': False,
                             'project_id': project_id,
                             'tenant_id': project_id}}
        res = self.api.post(_get_path('fw/firewalls', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            status=exc.HTTPBadRequest.code)
        self.assertIn('Invalid input for description',
                      res.body.decode('utf-8'))

    def test_firewall_list(self):
        fw_id = _uuid()
        return_value = [{'tenant_id': _uuid(),
                         'id': fw_id}]

        instance = self.plugin.return_value
        instance.get_firewalls.return_value = return_value

        res = self.api.get(_get_path('fw/firewalls', fmt=self.fmt))

        instance.get_firewalls.assert_called_with(mock.ANY,
                                                  fields=mock.ANY,
                                                  filters=mock.ANY)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_firewall_get(self):
        fw_id = _uuid()
        return_value = {'tenant_id': _uuid(),
                        'id': fw_id}

        instance = self.plugin.return_value
        instance.get_firewall.return_value = return_value

        res = self.api.get(_get_path('fw/firewalls',
                                     id=fw_id, fmt=self.fmt))

        instance.get_firewall.assert_called_with(mock.ANY,
                                                 fw_id,
                                                 fields=mock.ANY)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall', res)
        self.assertEqual(return_value, res['firewall'])

    def test_firewall_update(self):
        fw_id = _uuid()
        update_data = {'firewall': {'name': 'new_name'}}
        return_value = {'tenant_id': _uuid(),
                        'id': fw_id}

        instance = self.plugin.return_value
        instance.update_firewall.return_value = return_value

        res = self.api.put(_get_path('fw/firewalls', id=fw_id,
                                     fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_firewall.assert_called_with(mock.ANY, fw_id,
                                                    firewall=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall', res)
        self.assertEqual(return_value, res['firewall'])

    def test_firewall_delete(self):
        self._test_entity_delete('firewall')

    def _test_create_firewall_rule(self, src_port, dst_port):
        rule_id = _uuid()
        project_id = _uuid()
        data = {'firewall_rule': {'description': 'descr_firewall_rule1',
                                  'name': 'rule1',
                                  'shared': False,
                                  'protocol': 'tcp',
                                  'ip_version': 4,
                                  'source_ip_address': '192.168.0.1',
                                  'destination_ip_address': '127.0.0.1',
                                  'source_port': src_port,
                                  'destination_port': dst_port,
                                  'action': 'allow',
                                  'enabled': True,
                                  'project_id': project_id,
                                  'tenant_id': project_id}}
        expected_ret_val = copy.copy(data['firewall_rule'])
        expected_ret_val['source_port'] = str(src_port)
        expected_ret_val['destination_port'] = str(dst_port)
        expected_call_args = copy.copy(expected_ret_val)
        expected_ret_val['id'] = rule_id
        instance = self.plugin.return_value
        instance.create_firewall_rule.return_value = expected_ret_val
        res = self.api.post(_get_path('fw/firewall_rules', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_firewall_rule.assert_called_with(
            mock.ANY,
            firewall_rule={'firewall_rule': expected_call_args})
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall_rule', res)
        self.assertEqual(expected_ret_val, res['firewall_rule'])

    def test_create_firewall_rule_with_integer_ports(self):
        self._test_create_firewall_rule(1, 10)

    def test_create_firewall_rule_with_string_ports(self):
        self._test_create_firewall_rule('1', '10')

    def test_create_firewall_rule_with_port_range(self):
        self._test_create_firewall_rule('1:20', '30:40')

    def test_create_firewall_rule_invalid_long_name(self):
        project_id = _uuid()
        data = {'firewall_rule': {'description': 'descr_firewall_rule1',
                                  'name': _long_name,
                                  'shared': False,
                                  'protocol': 'tcp',
                                  'ip_version': 4,
                                  'source_ip_address': '192.168.0.1',
                                  'destination_ip_address': '127.0.0.1',
                                  'source_port': 1,
                                  'destination_port': 1,
                                  'action': 'allow',
                                  'enabled': True,
                                  'project_id': project_id,
                                  'tenant_id': project_id}}
        res = self.api.post(_get_path('fw/firewall_rules', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            status=exc.HTTPBadRequest.code)
        self.assertIn('Invalid input for name', res.body.decode('utf-8'))

    def test_create_firewall_rule_invalid_long_description(self):
        project_id = _uuid()
        data = {'firewall_rule': {'description': _long_description,
                                  'name': 'rule1',
                                  'shared': False,
                                  'protocol': 'tcp',
                                  'ip_version': 4,
                                  'source_ip_address': '192.168.0.1',
                                  'destination_ip_address': '127.0.0.1',
                                  'source_port': 1,
                                  'destination_port': 1,
                                  'action': 'allow',
                                  'enabled': True,
                                  'project_id': project_id,
                                  'tenant_id': project_id}}
        res = self.api.post(_get_path('fw/firewall_rules', fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            status=exc.HTTPBadRequest.code)
        self.assertIn('Invalid input for description',
                      res.body.decode('utf-8'))

    def test_firewall_rule_list(self):
        rule_id = _uuid()
        return_value = [{'tenant_id': _uuid(),
                         'id': rule_id}]

        instance = self.plugin.return_value
        instance.get_firewall_rules.return_value = return_value

        res = self.api.get(_get_path('fw/firewall_rules', fmt=self.fmt))

        instance.get_firewall_rules.assert_called_with(mock.ANY,
                                                       fields=mock.ANY,
                                                       filters=mock.ANY)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_firewall_rule_get(self):
        rule_id = _uuid()
        return_value = {'tenant_id': _uuid(),
                        'id': rule_id}

        instance = self.plugin.return_value
        instance.get_firewall_rule.return_value = return_value

        res = self.api.get(_get_path('fw/firewall_rules',
                                     id=rule_id, fmt=self.fmt))

        instance.get_firewall_rule.assert_called_with(mock.ANY,
                                                      rule_id,
                                                      fields=mock.ANY)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall_rule', res)
        self.assertEqual(return_value, res['firewall_rule'])

    def test_firewall_rule_update(self):
        rule_id = _uuid()
        update_data = {'firewall_rule': {'action': 'deny'}}
        return_value = {'tenant_id': _uuid(),
                        'id': rule_id}

        instance = self.plugin.return_value
        instance.update_firewall_rule.return_value = return_value

        res = self.api.put(_get_path('fw/firewall_rules', id=rule_id,
                                     fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_firewall_rule.assert_called_with(
            mock.ANY,
            rule_id,
            firewall_rule=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall_rule', res)
        self.assertEqual(return_value, res['firewall_rule'])

    def test_firewall_rule_delete(self):
        self._test_entity_delete('firewall_rule')

    def test_create_firewall_policy(self):
        policy_id = _uuid()
        project_id = _uuid()
        data = {'firewall_policy': {'description': 'descr_firewall_policy1',
                                    'name': 'new_fw_policy1',
                                    'shared': False,
                                    'firewall_rules': [_uuid(), _uuid()],
                                    'audited': False,
                                    'project_id': project_id,
                                    'tenant_id': project_id}}
        return_value = copy.copy(data['firewall_policy'])
        return_value.update({'id': policy_id})

        instance = self.plugin.return_value
        instance.create_firewall_policy.return_value = return_value
        res = self.api.post(_get_path('fw/firewall_policies',
                                      fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_firewall_policy.assert_called_with(
            mock.ANY,
            firewall_policy=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall_policy', res)
        self.assertEqual(return_value, res['firewall_policy'])

    def test_create_firewall_policy_invalid_long_name(self):
        project_id = _uuid()
        data = {'firewall_policy': {'description': 'descr_firewall_policy1',
                                    'name': _long_name,
                                    'shared': False,
                                    'firewall_rules': [_uuid(), _uuid()],
                                    'audited': False,
                                    'project_id': project_id,
                                    'tenant_id': project_id}}
        res = self.api.post(_get_path('fw/firewall_policies',
                                      fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            status=exc.HTTPBadRequest.code)
        self.assertIn('Invalid input for name', res.body.decode('utf-8'))

    def test_create_firewall_policy_invalid_long_description(self):
        project_id = _uuid()
        data = {'firewall_policy': {'description': _long_description,
                                    'name': 'new_fw_policy1',
                                    'shared': False,
                                    'firewall_rules': [_uuid(), _uuid()],
                                    'audited': False,
                                    'project_id': project_id,
                                    'tenant_id': project_id}}
        res = self.api.post(_get_path('fw/firewall_policies',
                                      fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            status=exc.HTTPBadRequest.code)
        self.assertIn('Invalid input for description',
                      res.body.decode('utf-8'))

    def test_firewall_policy_list(self):
        policy_id = _uuid()
        return_value = [{'tenant_id': _uuid(),
                         'id': policy_id}]

        instance = self.plugin.return_value
        instance.get_firewall_policies.return_value = return_value

        res = self.api.get(_get_path('fw/firewall_policies',
                                     fmt=self.fmt))

        instance.get_firewall_policies.assert_called_with(mock.ANY,
                                                          fields=mock.ANY,
                                                          filters=mock.ANY)
        self.assertEqual(exc.HTTPOk.code, res.status_int)

    def test_firewall_policy_get(self):
        policy_id = _uuid()
        return_value = {'tenant_id': _uuid(),
                        'id': policy_id}

        instance = self.plugin.return_value
        instance.get_firewall_policy.return_value = return_value

        res = self.api.get(_get_path('fw/firewall_policies',
                                     id=policy_id, fmt=self.fmt))

        instance.get_firewall_policy.assert_called_with(mock.ANY,
                                                        policy_id,
                                                        fields=mock.ANY)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall_policy', res)
        self.assertEqual(return_value, res['firewall_policy'])

    def test_firewall_policy_update(self):
        policy_id = _uuid()
        update_data = {'firewall_policy': {'audited': True}}
        return_value = {'tenant_id': _uuid(),
                        'id': policy_id}

        instance = self.plugin.return_value
        instance.update_firewall_policy.return_value = return_value

        res = self.api.put(_get_path('fw/firewall_policies',
                                     id=policy_id,
                                     fmt=self.fmt),
                           self.serialize(update_data))

        instance.update_firewall_policy.assert_called_with(
            mock.ANY,
            policy_id,
            firewall_policy=update_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('firewall_policy', res)
        self.assertEqual(return_value, res['firewall_policy'])

    def test_firewall_policy_update_malformed_rules(self):
        # emulating client request when no rule uuids are provided for
        # --firewall_rules parameter
        update_data = {'firewall_policy': {'firewall_rules': True}}
        # have to check for generic AppError
        self.assertRaises(
            webtest.AppError,
            self.api.put,
            _get_path('fw/firewall_policies', id=_uuid(), fmt=self.fmt),
            self.serialize(update_data))

    def test_firewall_policy_delete(self):
        self._test_entity_delete('firewall_policy')

    def test_firewall_policy_insert_rule(self):
        firewall_policy_id = _uuid()
        firewall_rule_id = _uuid()
        ref_firewall_rule_id = _uuid()

        insert_data = {'firewall_rule_id': firewall_rule_id,
                       'insert_before': ref_firewall_rule_id,
                       'insert_after': None}
        return_value = {'firewall_policy':
                        {'tenant_id': _uuid(),
                         'id': firewall_policy_id,
                         'firewall_rules': [ref_firewall_rule_id,
                                            firewall_rule_id]}}

        instance = self.plugin.return_value
        instance.insert_rule.return_value = return_value

        path = _get_path('fw/firewall_policies', id=firewall_policy_id,
                         action="insert_rule",
                         fmt=self.fmt)
        res = self.api.put(path, self.serialize(insert_data))
        instance.insert_rule.assert_called_with(mock.ANY, firewall_policy_id,
                                                insert_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertEqual(return_value, res)

    def test_firewall_policy_remove_rule(self):
        firewall_policy_id = _uuid()
        firewall_rule_id = _uuid()

        remove_data = {'firewall_rule_id': firewall_rule_id}
        return_value = {'firewall_policy':
                        {'tenant_id': _uuid(),
                         'id': firewall_policy_id,
                         'firewall_rules': []}}

        instance = self.plugin.return_value
        instance.remove_rule.return_value = return_value

        path = _get_path('fw/firewall_policies', id=firewall_policy_id,
                         action="remove_rule",
                         fmt=self.fmt)
        res = self.api.put(path, self.serialize(remove_data))
        instance.remove_rule.assert_called_with(mock.ANY, firewall_policy_id,
                                                remove_data)
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertEqual(return_value, res)


class TestFirewallAttributeValidators(base.BaseTestCase):

    def test_validate_port_range(self):
        msg = firewall._validate_port_range(None)
        self.assertIsNone(msg)

        msg = firewall._validate_port_range('10')
        self.assertIsNone(msg)

        msg = firewall._validate_port_range(10)
        self.assertIsNone(msg)

        msg = firewall._validate_port_range(-1)
        self.assertEqual("Invalid port '-1'", msg)

        msg = firewall._validate_port_range('66000')
        self.assertEqual("Invalid port '66000'", msg)

        msg = firewall._validate_port_range('10:20')
        self.assertIsNone(msg)

        msg = firewall._validate_port_range('1:65535')
        self.assertIsNone(msg)

        msg = firewall._validate_port_range('0:65535')
        self.assertEqual("Invalid port '0'", msg)

        msg = firewall._validate_port_range('1:65536')
        self.assertEqual("Invalid port '65536'", msg)

        msg = firewall._validate_port_range('abc:efg')
        self.assertEqual("Port 'abc' is not a valid number", msg)

        msg = firewall._validate_port_range('1:efg')
        self.assertEqual("Port 'efg' is not a valid number", msg)

        msg = firewall._validate_port_range('-1:10')
        self.assertEqual("Invalid port '-1'", msg)

        msg = firewall._validate_port_range('66000:10')
        self.assertEqual("Invalid port '66000'", msg)

        msg = firewall._validate_port_range('10:66000')
        self.assertEqual("Invalid port '66000'", msg)

        msg = firewall._validate_port_range('1:-10')
        self.assertEqual("Invalid port '-10'", msg)

    def test_validate_ip_or_subnet_or_none(self):
        msg = firewall._validate_ip_or_subnet_or_none(None)
        self.assertIsNone(msg)

        msg = firewall._validate_ip_or_subnet_or_none('1.1.1.1')
        self.assertIsNone(msg)

        msg = firewall._validate_ip_or_subnet_or_none('1.1.1.0/24')
        self.assertIsNone(msg)

        ip_addr = '1111.1.1.1'
        msg = firewall._validate_ip_or_subnet_or_none(ip_addr)
        self.assertEqual(
            ("'%s' is not a valid IP address and "
             "'%s' is not a valid IP subnet")
            % (ip_addr,
               ip_addr),
            msg)

        ip_addr = '1.1.1.1 has whitespace'
        msg = firewall._validate_ip_or_subnet_or_none(ip_addr)
        self.assertEqual(
            ("'%s' is not a valid IP address and "
             "'%s' is not a valid IP subnet") % (ip_addr,
                                                 ip_addr),
            msg)

        ip_addr = '111.1.1.1\twhitespace'
        msg = firewall._validate_ip_or_subnet_or_none(ip_addr)
        self.assertEqual(
            ("'%s' is not a valid IP address and "
             "'%s' is not a valid IP subnet") % (ip_addr,
                                                 ip_addr),
            msg)

        ip_addr = '111.1.1.1\nwhitespace'
        msg = firewall._validate_ip_or_subnet_or_none(ip_addr)
        self.assertEqual(
            ("'%s' is not a valid IP address and "
             "'%s' is not a valid IP subnet") % (ip_addr,
                                                 ip_addr),
            msg)

        # Valid - IPv4
        cidr = "10.0.2.0/24"
        msg = firewall._validate_ip_or_subnet_or_none(cidr, None)
        self.assertIsNone(msg)

        # Valid - IPv6 without final octets
        cidr = "fe80::/24"
        msg = firewall._validate_ip_or_subnet_or_none(cidr, None)
        self.assertIsNone(msg)

        # Valid - IPv6 with final octets
        cidr = "fe80::0/24"
        msg = firewall._validate_ip_or_subnet_or_none(cidr, None)
        self.assertIsNone(msg)

        cidr = "fe80::"
        msg = firewall._validate_ip_or_subnet_or_none(cidr, None)
        self.assertIsNone(msg)

        # Invalid - IPv6 with final octets, missing mask
        cidr = "fe80::0"
        msg = firewall._validate_ip_or_subnet_or_none(cidr, None)
        self.assertIsNone(msg)

        # Invalid - Address format error
        cidr = 'invalid'
        msg = firewall._validate_ip_or_subnet_or_none(cidr, None)
        self.assertEqual(
            ("'%s' is not a valid IP address and "
             "'%s' is not a valid IP subnet") % (cidr,
                                                 cidr),
            msg)


class TestFirewallConvertProtocols(base.BaseTestCase):
    def test_convert_protocol_digit(self):
        res = firewall.convert_protocol("0")
        self.assertEqual(0, res)
        res = firewall.convert_protocol("255")
        self.assertEqual(255, res)

    def test_convert_protocol_invalid_digit(self):
        res = lambda: firewall.convert_protocol("-1")
        self.assertRaises(firewall.FirewallRuleInvalidProtocol, res)

        res = lambda: firewall.convert_protocol("256")
        self.assertRaises(firewall.FirewallRuleInvalidProtocol, res)

    def test_convert_protocol_name(self):
        res = firewall.convert_protocol("tcp")
        self.assertEqual("tcp", res)

        res = firewall.convert_protocol("UDP")
        self.assertEqual("udp", res)

        res = firewall.convert_protocol("Icmp")
        self.assertEqual("icmp", res)

    def test_convert_protocol_invalid_name(self):
        res = lambda: firewall.convert_protocol("foo")
        self.assertRaises(firewall.FirewallRuleInvalidProtocol, res)


class TestConvertActionToCaseInsensitive(base.BaseTestCase):
    def test_convert_action_to_case_insensitive_none(self):
        res = firewall.convert_action_to_case_insensitive(None)
        self.assertIsNone(res)

    def test_convert_action_to_case_insensitive_value(self):
        res = firewall.convert_action_to_case_insensitive("foo")
        self.assertEqual("foo", res)

        res = firewall.convert_action_to_case_insensitive("Bar")
        self.assertEqual("bar", res)

        res = firewall.convert_action_to_case_insensitive("BAZ")
        self.assertEqual("baz", res)
