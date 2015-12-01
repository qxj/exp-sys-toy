

pb: proto/experiment.proto
	protoc -I=proto --python_out=src/python $^
	protoc -I=proto --plugin=/usr/bin/protoc-gen-php --php_out=src/php $^
