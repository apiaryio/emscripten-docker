#!/usr/bin/env python

import os
import sys
import logging
import re
import json
import argparse
import textwrap
import subprocess

import requests

VERSIONS = ['1.35', '1.36']
TAGS_URL = "https://api.github.com/repos/kripken/emscripten/tags"
VER_LINE = re.compile(r"^ENV EMCC_SDK_VERSION (1\.[0-9]+)\.[0-9]+$")


verbose = False

def get_tags(versions):
    logging.info("Reading tags from repo %s"%(TAGS_URL))
    r = requests.get(TAGS_URL)
    if r.status_code != 200:
        raise RuntimeError(r.text)
    else:
        tags = [i['name'] for i in json.loads(r.text) if any(x in i['name'] for x in versions)]
        while 'next' in r.links:
            r = requests.get(r.links['next']['url'])
            if r.status_code != 200:
                raise RuntimeError(r.text)
            else:
                 tags.extend([i['name'] for i in json.loads(r.text) if any(x in i['name'] for x in versions)])
    return tags


def tag_filter(tag):
    def _tagf(t):
        if t.find(tag) is not -1:
            return t;
    return _tagf


def update_dockerfile(minor, ver):
    df = os.path.join(minor, 'Dockerfile')
    dfup = []
    with open(df) as f:
        for l in f.readlines():
            vl = VER_LINE.search(l)
            if vl and vl.group(1) == minor:
                dfup.append("ENV EMCC_SDK_VERSION %s\n"%(ver))
                continue
            dfup.append(l)

    with open(df, 'w') as f:
        f.writelines(dfup)

def cmd_update(versions):
    tags = get_tags(versions)
    latest = list(map((lambda x: list(filter(tag_filter(x), tags))[0]), versions))
    for i in range(len(versions)):
        logging.info("Updating %s/Dockerfile with %s"%(versions[i], latest[i]))
        update_dockerfile(versions[i], latest[i])

def push_tag(tag):
    for i in range(3):
        if subprocess.call(['docker', 'push', tag]):
            logging.warning("Pushing %s failed. Trying again..,"%(tag))
        else:
            logging.info("Pushed tag: %s"%(tag))
            return
    logging.error("Pushing %s failed."%(tag))


def cmd_build(versions, push, latest):
    cdir = os.getcwd()
    for v in versions:
        os.chdir(v)
        logging.info("Building emscripten-%s"%(v))
        if subprocess.call(['docker', 'build', '-t,'  "apiaryio/emcc:%s"%(v), '.']):
            logging.error("Building apiaryio/emcc: failed"%(v))
            os.chdir(cdir)
            continue
        logging.info("Building of apiaryio/emcc:%s finished."%(v))
        os.chdir(cdir)
        if v is latest:
            di = subprocess.check_output('docker images -q | head -n 1',
                                         shell=True).decode('utf-8')
            if subprocess.call(["docker",
                                "tag",
                                di,
                                "apiaryio/emcc:latest"]):
            logging.error("Tagging as latest the apiaryio/emcc:%s failed"%(v))
            continue

    if push:
        logging.info('Pushing tags apiaryio/emcc')
        push_tag("apiaryio/emcc")


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
        Update and build docker images of emscripten'''),
        epilog=textwrap.dedent('''\
    Example:
        emccbuild.py update -v 1.36
        emccbuild.py build -v 1.35 1.36 -t 1.36'''),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--logverbose', help='be verbose mode',
                        action='store_true', default=False)
    subparsers = parser.add_subparsers(title='sub-commands', dest='command')
    # create the parser for the "update" command
    parser_u = subparsers.add_parser('update', help='Update the Dockerfiles according to releases')
    parser_u.add_argument('-v', '--version',help='Update just given versions',
                          metavar="VERSION", nargs='+', type=str,  default=VERSIONS)
    # create the parser for the "build" command
    parser_b = subparsers.add_parser('build', help='Build/Push the docker images to docker repo')
    parser_b.add_argument('-p', '--push',help='Also push the built images',
                          action='store_true', default=False)
    parser_b.add_argument('-v', '--version',help='Build just given versions',
                          metavar="VERSIONS", nargs='+', type=str, default=None)
    parser_b.add_argument('-t', '--latest', help='Tag and push version as latest.',
                          metavar="VERSION", nargs='?', type=str, default=None)

    args = parser.parse_args()

    loglevel = logging.INFO
    if args.logverbose:
        loglevel = logging.DEBUG

    logging.basicConfig(format='%(message)s',
                        datefmt='%I:%M:%S', level=loglevel)

    if args.command == 'update':
        cmd_update(args.version)
    if args.command == 'build':
        cmd_build(args.version, args.push)

    sys.exit(0)

if __name__ == '__main__':
    main()


