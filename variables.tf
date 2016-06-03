variable "aws_access" {}
variable "aws_secret" {}
variable "aws_subnet_id" {}
variable "aws_instance_type" {
    default = "t2.micro"
}
variable "aws_region" {
    default = "us-east-1"
}

variable "user" {
    default = "ec2-user"
}
variable "key_path" {}
variable "key_name" {}
