#!/usr/bin/env python3

import sys
import subprocess
import re
import os
import shutil
import hashlib
from optparse import OptionParser
from pprint import pprint as pp

rename_pattern = "{pn}-{vc}-{vn} s{sv}-t{tsv} ({al}) [{h}].apk"

re_packagename = r"""package: name='([^']*)' versionCode='([^']*)' versionName='([^']*)'"""
re_sdkversion = r"""sdkVersion:'(\d+)'"""
re_targetsdkversion = r"""targetSdkVersion:'(\d+)'"""
re_app_label = r"""application-label:'([^']*)'"""


def generate_filename(apk_info, pattern):
    new_filename = pattern.format(
        pn = apk_info.get('package_name', apk_info['old_filename']),
        vc = apk_info.get('version_code', '?'),
        vn = apk_info.get('version_name', '?.?.?')[:32],
        sv = apk_info.get('sdk_version', '?'),
        tsv = apk_info.get('target_sdk_version', '?'),
        al = apk_info.get('app_label', '')[:128],
        h = apk_info['md5'],
    )
    return new_filename.replace('/', '_')

def extract_metadata(path):
    try:
        out = subprocess.check_output(['aapt', 'd', '--values', 'badging', path])
    except subprocess.CalledProcessError:
        print("problem parsing dump data for file '{}'".format(path))
        return

    out = str(out, 'utf8')
    #print(out)

    apk_info = {}


    with open(path, 'rb') as f:
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

    return apk_info

def parse_paths(paths, action):
    statistic = {
        'not_apks': 0,
        'bad_metadata': 0,
        'filenames_up_to_date': 0,
        'dirs_walked': 0,
        'files_checked': 0,
        'actions_performed': 0,
    }

    for path in paths:
        for (root, dirs, files) in os.walk(path):
            statistic['dirs_walked'] += 1

            for filename in files:
                statistic['files_checked'] += 1

                if filename[-4:] != '.apk':
                    statistic['not_apks'] += 1
                    continue

                full_path = os.path.join(root, filename)
                metadata = extract_metadata(full_path)
                if metadata is None:
                    statistic['bad_metadata'] += 1
                    continue

                metadata['old_filename'] = filename[:-4]
                new_filename = generate_filename(metadata, rename_pattern)
                if filename == new_filename:
                    statistic['filenames_up_to_date'] += 1

                #new_full_path = os.path.join(root, new_filename)
                #print(new_filename)
                #os.rename(full_path, new_full_path)
                action(root, filename, new_filename, metadata['package_name'])
                statistic['actions_performed'] += 1

    #print("Statistics:")
    #print("directories walked: {}".format(dirs_walked))
    #print("files checked: {}".format(files_checked))
    #print("    not .apk files: {}".format(not_apks))
    #print("    files with bad metadata: {}".format(bad_metadata))
    #print("    files with names up to date: {}".format(filename_up_to_date))
    #print("    files renamed: {}".format(renamed))
    return statistic

def main():
    parser = OptionParser(
        usage = "%prog [options] <file> ...",
        description = "walk recursively dirs and files on the command line and perform action according to the options specified"
    )
    parser.add_option("-r", "--rename", action="store_true", default=False, help="rename APKs")
    parser.add_option("-s", "--sort", action="store_true", default=False, help="sort APKs to directory")
    parser.add_option("-d", "--dir", dest="dir", help="directory to output apk files to")
    parser.add_option("-c", "--copy", action="store_true", default=False, help="copy APKs instead of move")

    (options, args) = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    #print(options, args)

    def action(root, filename, new_filename, package_name):
        path = os.path.join(root, filename)

        output_dir = options.dir if options.dir else root
        if options.sort:
            package_path = os.path.join(*package_name.split('.'))
            output_dir = os.path.join(output_dir, package_path)

        output_filename = new_filename if options.rename else filename
        output_path = os.path.join(output_dir, output_filename)

        try:
            os.makedirs(output_dir)
        except OSError:
            pass

        if options.copy:
            shutil.copyfile(path, output_path)
            print("COPY '{}' -> '{}'".format(path, output_path))
        else:
            os.rename(path, output_path)
            print("MOVE '{}' -> '{}'".format(path, output_path))

    stat = parse_paths(args, action)
    pp(stat)


if __name__ == "__main__":
    main()
