#!/usr/bin/env python3
"""Validate a declarative BlockTheSpot mod (experimental loader format).

Checks:
  [Compatibility] Spotify is x.y.z
  [Buffer_modify] lists files by contiguous 1..N keys
  each listed file has a section that names patch groups
  each group has Signature_N / Value_N pairs of valid hex
  value is never longer than its signature (loader rejects that)

Exit status 0 when valid, 1 otherwise. Warnings do not fail the build.
"""
import configparser
import re
import sys

HEX = re.compile(r'^(?:[0-9A-Fa-f]{2}|\?\?)(?:\s+(?:[0-9A-Fa-f]{2}|\?\?))*$')
VERSION = re.compile(r'^\d+(\.\d+){2,3}$')   # x.y.z or x.y.z.build

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def read_ini(path):
    cp = configparser.ConfigParser(strict=False, interpolation=None,
                                   delimiters=('=',), comment_prefixes=(';', '#'))
    cp.optionxform = str
    with open(path, encoding='utf-8') as fh:
        cp.read_file(fh)
    return cp


def numbered(cp, section, prefix=''):
    """Return [(index, value)] for keys prefix+1, prefix+2, ... until a gap."""
    out, i = [], 1
    while cp.has_option(section, '%s%d' % (prefix, i)):
        out.append((i, cp.get(section, '%s%d' % (prefix, i))))
        i += 1
    return out


def main(path):
    try:
        cp = read_ini(path)
    except Exception as exc:                        # noqa: BLE001
        print('error: cannot parse %s: %s' % (path, exc))
        return 1

    if not cp.has_section('Compatibility'):
        err('missing [Compatibility]')
    else:
        ver = cp.get('Compatibility', 'Spotify', fallback='')
        if not VERSION.match(ver):
            err('[Compatibility] Spotify must be x.y.z, got %r' % ver)

    if not cp.has_section('Buffer_modify'):
        err('missing [Buffer_modify]')
        files = []
    else:
        if cp.has_option('Buffer_modify', 'Enable') and \
                cp.get('Buffer_modify', 'Enable').strip() not in ('0', '1'):
            err('[Buffer_modify] Enable must be 0 or 1')
        files = numbered(cp, 'Buffer_modify')
        if not files:
            err('[Buffer_modify] lists no files')

    if not files:
        return report(path)

    for _i, name in files:
        name = name.strip()
        if not cp.has_section(name):
            err('file %r is listed but has no section' % name)
            continue
        groups = numbered(cp, name)
        if not groups:
            err('section [%s] names no patch groups' % name)
            continue
        for _j, group in groups:
            group = group.strip()
            if not cp.has_section(group):
                err('patch group %r has no section' % group)
                continue
            pairs = numbered(cp, group, prefix='Signature_')
            if not pairs:
                err('patch group %r has no Signature_1' % group)
                continue
            for idx, sig in pairs:
                vkey = 'Value_%d' % idx
                if not cp.has_option(group, vkey):
                    err('%s: Signature_%d without %s' % (group, idx, vkey))
                    continue
                val = cp.get(group, vkey)
                sig_s, val_s = sig.strip(), val.strip()
                if not HEX.match(sig_s):
                    err('%s: Signature_%d is not hex bytes' % (group, idx))
                    continue
                if not HEX.match(val_s):
                    err('%s: Value_%d is not hex bytes' % (group, idx))
                    continue
                if len(val_s.split()) > len(sig_s.split()):
                    err('%s: Value_%d is longer than Signature_%d' % (group, idx, idx))
                elif len(val_s.split()) < len(sig_s.split()):
                    warn('%s: Value_%d shorter than its signature' % (group, idx))
                okey = 'Offset_%d' % idx
                if cp.has_option(group, okey):
                    try:
                        int(cp.get(group, okey))
                    except ValueError:
                        err('%s: %s is not an integer' % (group, okey))

    return report(path)


def report(path):
    for w in warnings:
        print('warning: %s' % w)
    for e in errors:
        print('error: %s' % e)
    if errors:
        print('FAILED: %s (%d errors)' % (path, len(errors)))
        return 1
    print('ok: %s' % path)
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: validate_mod.py <mod.ini>')
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
