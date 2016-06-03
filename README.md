# Emscripten dockerized

This image serves as convenient way how to have emscripten at hand
without the need to build it for yourself, which takes a long time as
you need to build clang from source.

## Versioning

The docker image version is the same as emscrpten version so
`apiaryio/emcc:1.33` corresponds to emscripten version `1.33`.

In the respective subdirectories you can find Dockerfiles for all
currently maintaned emscripten versions. Each of them is building the
latest patch version.

## Usage

Once `pulled` the usage is simple either invoke simple commands for
interactive use

```sh
$> docker run --rm -v $(pwd):/src -t apiaryio/emcc emconfigure ./configure
```

or if working on non-trivial project have a build script run that, see
the `emcc` direcotry in drafter
[repo](https://github.com/apiaryio/drafter).

```sh
$> docker run --rm -v $(pwd):/src -t apiaryio/emcc emcc/emcbuild.sh
```

Both examples assume you are in the root directory of your project
where is your `configure` or `Makefile`.


## Automated building of the images

To ease the maintenance there are few python 3 scripts to help and
[terraform](https://www.terraform.io/) settings.

### emccbuild.py

This script updates and build the images automatically.

`./emccbuild.py -h` for usage


### runit.py

This is a
[pexpect](http://pexpect.readthedocs.io/en/stable/index.html) script
which builds and pushes given versions on AWS EC2 instance. It
utilizes [terraform](https://www.terraform.io/) for the EC2 instance
setup and teardown.

The script calls terraform and then over ssh runs `docker login` and
`emccbuild.py` and if it finishes succesfully then it tears down the
ec2 instance as well, making the whole process simple.

`runit.py -h` for usage

It needs a configuration file `runitconfig.py` to proceed. If it does not exists it
will create a template so that you can just edit it and run it again.

#### Configuration (runitconfig.py)

```
aws_access = "<AWS ACCESS CODE>"
aws_secret = "<AWS SECRET>"
aws_instance_type = "c4.2xlarge"
aws_subnet_id = "<AWS SUBNET ID>"
key_name = "<AWS KEY NAME>"
ssh_key = "<PATH TO AWS KEY FILE>"
user = "<DOCKER USERNAME>"
passwd = "<DOCKER PASSWORD>"
email = "<DOCKER EMAIL>"
```

