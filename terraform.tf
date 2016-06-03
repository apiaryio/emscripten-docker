provider "aws" {
    access_key = "${var.aws_access}"
    secret_key = "${var.aws_secret}"
    region = "${var.aws_region}"
}

resource "aws_instance" "emscripten-builder" {
    ami = "ami-67a3a90d"
    instance_type = "${var.aws_instance_type}"
    ebs_optimized = "false"
    instance_initiated_shutdown_behavior = "terminate"
    subnet_id="${var.aws_subnet_id}"

    tags {
        name = "emscripten-builder"
    }

    connection {
        user = "${var.user}"
        key_file = "${var.key_path}"
    }
    key_name = "${var.key_name}"


    provisioner "file" {
        source = "./"
        destination = "~/"
    }
}
