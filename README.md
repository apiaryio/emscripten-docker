# Emscripten dockerized

This image serves as convenient way how to have emscripten at hand
without the need to build it for yourself, which takes a long time as
you need to build clang from source.

See the [docker hub](https://hub.docker.com/r/apiaryio/emcc/) for more details.

## Versioning

The docker image version (tag) is the same as emscripten version so
`apiaryio/emcc:1.38.11` corresponds to emscripten version `1.38.11`. Older
images used to ignore the patch version but it we hit an issue along the way and
started tagging even patch versions.

In the respective subdirectories you can find Dockerfiles for all emscripten
versions ever built. Each of them is building the latest patch version.

## Usage

Once `pulled` the usage is simple either invoke simple commands for
interactive use

```sh
$> docker run --rm -v $(pwd):/src -t apiaryio/emcc emconfigure ./configure
```

or if working on non-trivial project have a build script run that, see
the `scripts` directory in drafter.js
[repo](https://github.com/apiaryio/drafter.js).

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
