# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import json
import os
import re
import subprocess
import tempfile

SOURCE = Path(__file__).with_name('wireless-bridge.sh')
MOCK = r'''#!/usr/bin/python3
import json, os, sys
from pathlib import Path
p=Path(os.environ['MOCK_STATE']); s=json.loads(p.read_text())
name=Path(sys.argv[0]).name; a=sys.argv[1:]; rc=0
s['commands'].append([name]+a)
if name in ('grep','sed','sleep','chmod'):
    raise RuntimeError('Unavailable command: '+name)
elif name=='ip':
    if a[:4]==['link','show','dev',a[-1]]:
        interface=a[-1]
        print('50: '+interface+': <BROADCAST,UP> mtu 1500')
        if not (s['fault']=='missing-mac' and interface=='wlan5g0'):
            print('    link/ether '+s['macs'][interface]+(':' if s['fault']=='malformed-mac' and interface=='wlan5g0' else '')+' brd ff:ff:ff:ff:ff:ff')
    elif a==['-4','addr','show','dev','br0']:
        if s['fault']!='missing-ip':
            print('50: br0: <BROADCAST,UP> mtu 1500')
            print('    inet '+s['address']+('.' if s['fault']=='malformed-ip' else '')+'/24 brd 192.168.50.255 scope global br0')
    elif a==['-4','route','show','default']:
        print('default via 198.51.100.1 dev eth0 metric 1')
        if s['gateway_route']:
            print('default via '+s['gateway_route']+' dev br0 proto static metric 10')
elif name=='brctl':
    if a[0]=='show': print('br0 '+' '.join(s['ports']))
    elif a[0]=='delif': s['ports'].remove(a[2])
    elif a[0]=='addif':
        if a[2] not in s['ports']: s['ports'].append(a[2])
        if s['uplink_cable_present'] and 'eth0' in s['ports'] and 'wlan2' in s['ports']: raise RuntimeError('L2 LOOP')
elif name=='ifconfig':
    if a==['wlan2','down']: s['restoring']=True
    if a[:1]==['eth0'] and len(a)==2: s['eth0_up']=a[1]=='up'
elif name=='sendcmd':
    assert a[:3]==['1','DB','pf'], 'Masked DB p must not be used'
    table=a[3]
    if table=='WLANCfg': fields=[('ESSID',s['gui_ssid_xml'])]
    elif table=='WLANPSK': fields=[('PreSharedKey',s['gui_psk_xml']),('KeyPassphrase',s['gui_key_xml'])]
    else: raise AssertionError('Unexpected GUI table')
    lines=['<Tbl name="'+table+'" RowCount="2">','<Row No="1">','<DM name="ESSID" val="WrongRow"/>','<DM name="KeyPassphrase" val="WrongRowKey123"/>','</Row>','<Row No="0">']
    lines += ['<DM name="'+key+'" val="'+value+'"/>' for key,value in fields]
    lines += ['</Row>','</Tbl>']
    (p.parent/'var/tmp/dbtable').write_text('\n'.join(lines)+'\n')
    rc=int(s['fault']=='gui-export-fail' or (s['fault']=='gui-key-export-fail' and table=='WLANPSK'))
elif name=='busybox':
    assert a[:2]==['rm','-f'], 'Only export cleanup is expected'
    Path(a[2]).unlink(missing_ok=True)
elif name=='rmmod':
    if s['restoring'] and ('eth0' not in s['ports'] or not s['eth0_up'] or 'wlan2' in s['ports']): raise RuntimeError('ROLLBACK_WIRED_DOWN')
    if a[0] in s['modules']: s['modules'].remove(a[0])
elif name=='insmod':
    m={'mt7603-apcli.ko':'mt7603e_ap','mt7603eap.ko':'mt7603eap','mt7612e_ap.ko':'mt7612e_ap'}[Path(a[0]).name]
    if (s['fault']=='new-insmod' and m=='mt7603e_ap') or (s['fault']=='five-insmod' and m=='mt7612e_ap' and not s['failed']):
        rc=1; s['failed']=True
    elif m not in s['modules']: s['modules'].append(m)
elif name=='ping':
    if a[-1]==s['expected_gateway']:
        rc=int(s['fault']=='gateway' or s['watch']==1)
    elif a[1]=='31': s['watch']+=1
elif name=='iwpriv' and a[-1]=='ApCliAutoConnect=1' and s['watch']:
    s['rescans']+=1
p.write_text(json.dumps(s))
(p.parent/'proc/modules').write_text(''.join(m+' 1 0 - Live 0x1\n' for m in s['modules']))
sys.exit(rc)
'''


def run_case(fault='none', address='10.23.4.9', gateway_route=''):
    with tempfile.TemporaryDirectory(prefix='h267a-startup-') as directory:
        root = Path(directory)
        for relative in ('etc/h267a-wireless', 'var/tmp', 'tmp', 'lib/modules', 'usr/sbin',
                         'proc/sys/net/ipv4/conf/all', 'proc/sys/net/ipv4/conf/br0', 'mock-bin'):
            (root / relative).mkdir(parents=True, exist_ok=True)
        for relative in ('etc/h267a-wireless/mt7603.dat', 'etc/h267a-wireless/mt7612.dat',
                         'var/tmp/MT7612E.dat', 'lib/modules/mt7603-apcli.ko'):
            (root / relative).write_text('test-data\n')
        (root/'var/tmp/MT7592.dat').write_text('SSID1=FactoryTemplateOnly\nWPAPSK1=\n')
        (root/'etc/h267a-wireless/mt7603.dat').write_text('SSID1=OldName\nWPAPSK1=OldKey123\nApCliSsid=OldName\nApCliWPAPSK=OldKey123\nApCliBssid=01:02:03:04:05:06\nHideSSID=1\n')
        (root/'etc/h267a-wireless/mt7612.dat').write_text('SSID1=OldName\nWPAPSK1=OldKey123\nHideSSID=1\n')
        (root/'proc/modules').write_text('mt7603eap 1 0 - Live 0x1\nmt7612e_ap 1 0 - Live 0x1\n' if fault!='not-ready' else '')
        mock = root / 'mock-bin/mock'
        mock.write_text(MOCK)
        mock.chmod(0o755)
        for name in ('ip', 'ifconfig', 'brctl', 'rmmod', 'insmod', 'iwpriv', 'ping', 'grep', 'sed', 'sleep', 'chmod', 'sendcmd', 'busybox'):
            (mock.parent / name).symlink_to(mock)
        (root / 'usr/sbin/h267a-register-wlan2').symlink_to(mock)
        state = root / 'state.json'
        macs = {'wlan0':'02:00:00:00:00:10', 'wlan5g0':'02:00:00:00:00:20', 'br0':'02:00:00:00:00:30'}
        gateway = gateway_route or address.rsplit('.', 1)[0]+'.1'
        expected_ssid=gui_ssid_xml='New_$HOME;WiFi'
        expected_key=gui_key_xml='unittest$(false);key123'
        gui_psk_xml=''
        if fault=='gui-entities':
            gui_ssid_xml='Entity&amp;&quot;&lt;&gt;&apos;$HOME'
            expected_ssid="Entity&\"<>'$HOME"
            gui_key_xml='key&amp;&quot;&lt;&gt;&apos;$(false);123'
            expected_key="key&\"<>'$(false);123"
        elif fault=='gui-key-fallback':
            gui_key_xml=''
            expected_key=gui_psk_xml='abcdef0123456789'*4
        elif fault=='gui-empty-key': expected_key=gui_key_xml=''
        elif fault=='gui-short-key': expected_key=gui_key_xml='short'
        elif fault=='gui-empty-ssid': expected_ssid=gui_ssid_xml=''
        elif fault=='gui-long-ssid': expected_ssid=gui_ssid_xml='X'*33
        elif fault=='gui-invalid-hex': expected_key=gui_key_xml='x'*64
        state.write_text(json.dumps({'modules': [] if fault == 'not-ready' else ['mt7603eap', 'mt7612e_ap'],
                                    'ports': ['eth0', 'eth1', 'eth2', 'eth3', 'wlan0', 'wlan5g0'],
                                    'fault': fault, 'failed': False, 'commands': [], 'watch': 0, 'rescans': 0,
                                    'uplink_cable_present': False, 'macs':macs, 'address':address,
                                    'gateway_route':gateway_route, 'expected_gateway':gateway, 'gui_ssid_xml':gui_ssid_xml,
                                    'gui_key_xml':gui_key_xml,'gui_psk_xml':gui_psk_xml,'restoring':False,'eth0_up':True}))
        script = SOURCE.read_text()
        script = re.sub(r'/(?:tmp|etc|var|lib|usr/sbin|proc/sys)/', lambda m: str(root) + m[0], script)
        script = script.replace('PATH=/sbin:/bin:/usr/bin:/usr/sbin', f'PATH={mock.parent}:/usr/bin:/bin')
        script = script.replace('/bin/ip ', str(mock.parent / 'ip') + ' ')
        script = script.replace('/bin/busybox ', str(mock.parent / 'busybox') + ' ')
        script = script.replace('/proc/modules', str(root/'proc/modules'))
        script = script.replace('while :; do', 'for mock_iteration in 1 2; do')
        staged = root / 'startup.sh'
        staged.write_text(script)
        result = subprocess.run(['/bin/sh', str(staged)], env={**os.environ, 'MOCK_STATE': str(state)},
                                capture_output=True, text=True, timeout=15)
        final = json.loads(state.read_text())
        assert 'L2 LOOP' not in result.stderr, result.stderr
        assert 'ROLLBACK_WIRED_DOWN' not in result.stderr, 'Rollback unloaded radios before restoring wired management'
        assert not (root/'var/tmp/dbtable').exists(), 'Plaintext GUI export was left behind'
        assert not any(c[0]=='ip' and 'name' in c for c in final['commands']), 'Unexpected interface rename'
        untouched = fault in ('not-ready','missing-mac','missing-ip','malformed-mac','malformed-ip','gui-empty-key','gui-short-key','gui-empty-ssid','gui-long-ssid','gui-invalid-hex','gui-export-fail','gui-key-export-fail')
        if untouched:
            assert result.returncode != 0, 'Missing preflight input was accepted'
            assert 'H267A_STOCK_RESTORED' not in result.stdout
            assert not any(c[0] in ('insmod', 'rmmod', 'ifconfig') for c in final['commands']), 'Preflight failure changed radios'
        elif fault in ('none','gui-entities','gui-key-fallback'):
            assert result.returncode == 0, (result.stdout, result.stderr)
            assert 'H267A_WIRELESS_BRIDGE_READY' in result.stdout
            assert 'wlan2' in final['ports'] and 'eth0' in final['ports']
            assert 'mt7603e_ap' in final['modules'] and 'mt7612e_ap' in final['modules']
            assert final['rescans'] == 1, 'Watchdog did not rescan after gateway loss'
            route = ['ip','route','replace','default','via',gateway,'dev','br0']
            assert route in final['commands'], 'Gateway was not derived from br0 route or local subnet'
            assert all(c[-1] in ('127.0.0.1',gateway) for c in final['commands'] if c[0]=='ping'), 'Gateway probe used a fixed address'
            assert ['rmmod','mt7603e_ap'] not in final['commands'], 'Normal startup unloaded the new driver'
            assert ['ifconfig','br0','hw','ether',macs['br0']] in final['commands'], 'Bridge MAC changed'
            profile=dict(line.split('=',1) for line in (root/'tmp/h267a-apcli-test.dat').read_text().splitlines() if '=' in line)
            assert profile['SSID1']==profile['ApCliSsid']==expected_ssid
            assert profile['WPAPSK1']==profile['ApCliWPAPSK']==expected_key
            assert profile['ApCliBssid']=='00:00:00:00:00:00' and profile['HideSSID']=='0'
            five=dict(line.split('=',1) for line in (root/'var/tmp/MT7612E.dat').read_text().splitlines() if '=' in line)
            assert five['SSID1']==profile['SSID1'] and five['WPAPSK1']==profile['WPAPSK1'] and five['HideSSID']=='0'
        else:
            assert result.returncode != 0, result.stdout
            assert 'H267A_STOCK_RESTORED' in result.stdout
            assert 'wlan2' not in final['ports'] and 'eth0' in final['ports']
            assert set(final['modules']) == {'mt7603eap', 'mt7612e_ap'}
        if not untouched:
            for command in final['commands']:
                if command[0]=='insmod':
                    expected=macs['wlan5g0'] if command[1].endswith('mt7612e_ap.ko') else macs['wlan0']
                    assert command[2:]==['mac='+expected], 'Radio MAC was not preserved'
        return {'case': fault, 'address':address, 'gateway':gateway, 'passed': True, 'commands': len(final['commands'])}


if __name__ == '__main__':
    results=[run_case(case) for case in ('none','not-ready','missing-mac','missing-ip','malformed-mac','malformed-ip','new-insmod','five-insmod','gateway','gui-entities','gui-key-fallback','gui-empty-key','gui-short-key','gui-empty-ssid','gui-long-ssid','gui-invalid-hex','gui-export-fail','gui-key-export-fail')]
    results += [run_case('missing-ip',gateway_route='10.23.4.254'), run_case(address='192.168.50.2'), run_case(address='192.168.50.2',gateway_route='192.168.50.254')]
    print(json.dumps(results))
