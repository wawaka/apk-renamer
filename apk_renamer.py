#!/usr/bin/env python3

import sys
import subprocess
import re
import os
import hashlib
from pprint import pprint as pp

if len(sys.argv) <= 1:
    print("no arguments provided")
    exit(0)

rename_pattern = "{pn}-{vc}-{vn} s{sv}-t{tsv} ({al}) [{h}].apk"

re_packagename = r"""package: name='([^']*)' versionCode='([^']*)' versionName='([^']*)'"""
re_sdkversion = r"""sdkVersion:'(\d+)'"""
re_targetsdkversion = r"""targetSdkVersion:'(\d+)'"""
re_app_label = r"""application-label:'([^']*)'"""

for filename in sys.argv[1:]:
    try:
        out = subprocess.check_output(['aapt', 'd', '--values', 'badging', filename])
    except subprocess.CalledProcessError:
        print("problem parsing dump data for file '{}'".format(filename))
        continue

    out = str(out, 'utf8')
    #print(out)

    apk_info = {}


    apk_info['old_filename'] = filename.replace('.apk', '')
    with open(filename, 'rb') as f:
        apk_info['md5'] = hashlib.md5(f.read()).hexdigest()

    m = re.search(re_packagename, out)
    if m is not None:
        apk_info['package_name'] = m.group(1)
        apk_info['version_code'] = m.group(2)
        apk_info['version_name'] = m.group(3)

    m = re.search(re_sdkversion, out)
    if m is not None:
        apk_info['sdk_version'] = m.group(1)

    m = re.search(re_targetsdkversion, out)
    if m is not None:
        apk_info['target_sdk_version'] = m.group(1)

    m = re.search(re_app_label, out)
    if m is not None:
        apk_info['app_label'] = m.group(1)

    #pp(apk_info)

    new_filename = rename_pattern.format(
        pn = apk_info.get('package_name', apk_info['old_filename']),
        vc = apk_info.get('version_code', '?'),
        vn = apk_info.get('version_name', '?.?.?'),
        sv = apk_info.get('sdk_version', '?'),
        tsv = apk_info.get('target_sdk_version', '?'),
        al = apk_info.get('app_label', ''),
        h = apk_info['md5'],
    )

    print("{nf} <=== {of}".format(nf=new_filename, of=filename))
    #pp(apk_info)
    os.rename(filename, new_filename)
