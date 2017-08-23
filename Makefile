docker_build:
	docker build -t journald-2-cloudwatch -f Dockerfile .

docker_build_test: docker_build
	docker build -t journald-2-cloudwatch-test -f Dockerfile.test .

docker_test: docker_build_test
	docker run --rm -v "$$PWD:$$PWD" -w "$$PWD" \
	  -e AWS_DEFAULT_REGION=eu-west-1 \
	  -e AWS_ACCESS_KEY_ID=abc \
	  -e AWS_SECRET_ACCESS_KEY=abc \
	  journald-2-cloudwatch-test
