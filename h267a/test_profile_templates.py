# SPDX-License-Identifier: GPL-2.0-only
"""Check that source-distributed radio templates contain only generic inputs."""
from pathlib import Path
import re


def check_template(text, radio):
    fields = {}
    for line in text.splitlines():
        if '=' not in line or line.startswith('#'):
            continue
        key, value = line.split('=', 1)
        assert key not in fields, 'Duplicate template field: ' + key
        fields[key] = value
    required = {'MacAddress':'', 'SSID1':'H267A_CONFIGURED_WIFI', 'WPAPSK1':'H267A_GUI_CONFIG_REQUIRED',
                'HideSSID':'0', 'BssidNum':'1'}
    if radio == 'mt7603':
        required.update(ApCliSsid='H267A_CONFIGURED_WIFI', ApCliWPAPSK='H267A_GUI_CONFIG_REQUIRED',
                        ApCliBssid='00:00:00:00:00:00')
    for key, expected in required.items():
        assert fields.get(key) == expected, 'Unexpected private or missing template field: ' + key
    for key, value in fields.items():
        if re.fullmatch(r'SSID[2-4]', key):
            prefix = 'MT7592AP' if radio == 'mt7603' else 'RT7612AP'
            assert value == prefix + key[-1], 'Unexpected secondary SSID'
        elif re.fullmatch(r'WPAPSK[2-9]|Key[1-4]Str[1-4]|WdsKey|RADIUS_Key|RADIUS_Server|WdsList|AccessControlList\d*|MeshWPAKEY|MeshWEPKEY', key):
            assert value == '', 'Nonempty credential or peer field: ' + key
    addresses = re.findall(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', text)
    assert all(value == '00:00:00:00:00:00' for value in addresses), 'Template includes a device MAC'
    for key, value in fields.items():
        if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', value):
            assert (key, value) == ('own_ip_addr', '192.168.1.1'), 'Unexpected network address field: ' + key
    return fields


if __name__ == '__main__':
    directory = Path(__file__).with_name('profile-templates')
    for radio in ('mt7603', 'mt7612'):
        text = (directory / (radio + '.dat')).read_text()
        check_template(text, radio)
        for replacement in ('MacAddress=02:00:00:00:00:99', 'SSID1=PrivateNetwork', 'WPAPSK1=PrivateKey123'):
            key = replacement.split('=', 1)[0]
            invalid = re.sub(r'^' + key + r'=.*$', replacement, text, flags=re.M)
            try:
                check_template(invalid, radio)
            except AssertionError:
                pass
            else:
                raise AssertionError('Private-data mutation was accepted: ' + key)
    print('Generic templates: placeholders, empty MACs, no private peers/keys, mutation rejection PASS')
