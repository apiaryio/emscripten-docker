#!/usr/bin/env python


import os
import sys
import argparse
import textwrap
import re
import string

try:
    import pexpect
    from pexpect import pxssh
except ImportError:
    sys.stderr.write("You do not have 'pexpect' installed.\n")
    sys.stderr.write('pip install pexpect or use your package manager.\n')
    sys.exit(1)

try:
    from runitconfig import *
except ImportError:
    sys.stderr.write('No runitconfig.py file found.\n')
    with open('runitconfig.py', 'w') as f:
        for i in ['aws_access = "<AWS ACCESS CODE>"',
                  'aws_secret = "<AWS SECRET>"',
                  'aws_instance_type = "c4.2xlarge"',
                  'aws_subnet_id = "<AWS SUBNET ID>"',
                  'key_name = "<AWS KEY NAME>"',
                  'ssh_key = "<PATH TO AWS KEY FILE>"',
                  'user = "<DOCKER USERNAME>"',
                  'passwd = "<DOCKER PASSWORD>"',
                  'email = "<DOCKER EMAIL>"']:
            f.write(i + '\n')

    sys.stderr.write('runitconfig.py template file created.\n')
    sys.stderr.write('Please edit it before running again.\n')
    sys.exit(1)

VERBOSE = False
ansi = re.compile(r'\x1b[^m]*m')


class color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_step(pre, msg):
    print(color.OKGREEN + pre + color.HEADER + msg + color.ENDC)


def print_local_step(msg):
    print_step('[PEXPECT]: ', msg)


def print_remote_step(msg):
    print_step('[PEXPECT-SSH]: ', msg)


def bail_out(msg, data):
    print(color.FAIL + '[PEXPECT]: ' + color.ENDC + '\n' + msg)
    sys.exit(2)


def log(msg):
    if VERBOSE:
        print(msg)


def ssh_session(ip, versions, latest=None):
    s = pxssh.pxssh(encoding='utf-8')
    s.login(ip, 'ec2-user', ssh_key=ssh_key)

    try:
        print_remote_step('Docker login')
        s.sendline("docker login -u '%s' -p '%s'" % (user, passwd))
        s.expect_exact('Email:', timeout=60)
        s.sendline(email)
        s.prompt(timeout=120)
        log(s.before)

        print_remote_step('emccbuild.py build')

        l = "python emccbuild.py -l build -v %s -p" % (' '.join(versions))
        if latest is not None:
            l += " -t %s" % (latest)

        s.sendline(l)
        s.prompt(timeout=1200)
        log(s.before)
        s.logout()
    except pexpect.TIMEOUT:
        print_remote_step('Expect Timeout reached, going interactive')
        s.interact()


def run(step, cmd, expect, bail, timeout=10):
    print_local_step(step)
    res = pexpect.run(cmd, timeout=timeout).decode('utf-8')
    log(res)
    res = ansi.sub('', res)
    if expect not in res:
        bail_out(bail, res)

    return res


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
    Pexpect scritp to build emscripten docker images
    on ec2 and push them to docker hub'''),
        epilog=textwrap.dedent('''\
    Example:
        runit.py 1.36 '''),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--verbose', help='be verbose mode',
                        action='store_true', default=False)
    parser.add_argument('-t', '--latest',
                        help='which version to tag as a latest',
                        metavar="VERSION", nargs='?',
                        type=str, default=None)
    parser.add_argument('versions',
                        help='what emscripten versions to build',
                        metavar="VERSIONS", nargs='+', type=str)
    args = parser.parse_args()

    if args.verbose:
        global VERBOSE
        VERBOSE = True

    if not os.path.isfile('terraform.tfvars'):
        with open('terraform.tfvars', 'w') as tf:
            tf.write('aws_access = "%s"\n' % (aws_access))
            tf.write('aws_secret = "%s"\n' % (aws_secret))
            tf.write('aws_instance_type = "%s"\n' % (aws_instance_type))
            tf.write('aws_subnet_id = "%s"\n' % (aws_subnet_id))
            tf.write('key_path = "%s"\n' % (ssh_key))
            tf.write('key_name = "%s"\n\n' % (key_name))

    run("Terraform plan",
        'terraform plan',
        'Plan: 1 to add, 0 to change, 0 to destroy.',
        'terraform plan failed')

    run('Terraform apply',
        'terraform apply',
        'Apply complete! Resources: 1 added, 0 changed, 0 destroyed.',
        'terraform apply failed.\nRun terraform destroy to stop everything.',
        timeout=300)

    tf_show = run('Terraform show',
                  'terraform show',
                  'public_ip',
                  'terraform show failed.\nRun terraform destroy to stop everything.')

    m = re.search(r'public_ip = (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', tf_show)
    if m:
        ec2ip = m.group(1)
    else:
        bail_out('Could not get the ec2 instance public IP.',
                 'Run terraform destroy to stop everything.')

    log("EC2 Instance Public IP: %s" % (ec2ip))

    # SSH part comes in
    print_local_step("Starting ssh session to ec2-user@%s" % (ec2ip))
    ssh_session(ec2ip, args.versions, args.latest)

    # Teardown everything
    print_local_step("Terraform destroy")
    tf_destroy = pexpect.spawn('terraform destroy', encoding='utf-8')
    i = tf_destroy.expect([r'.*Enter a value:.*', pexpect.TIMEOUT])
    if i is 0:
        tf_destroy.sendline('yes')
        log(tf_destroy.after)
        tf_destroy.expect(pexpect.EOF, timeout=300)
        log(tf_destroy.before)
    else:
        log('terraform destroy failed, timeout')
    tf_destroy.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
