#!/bin/sh

# setup collector
sudo docker run -it --network=host -e SPAN_STORAGE_TYPE=cassandra  -e CASSANDRA_SERVERS=127.0.0.1 -e CASSANDRA_PORT=9042  jaegertracing/jaeger-collector:1.8 &

# setup query
sudo docker run --rm -it --network=host  -e CASSANDRA_SERVERS=10.197.103.143 -e CASSANDRA_PORT=9042 -p 16686:16686 jaegertracing/jaeger-query &

#setup agent
sudo docker run   --rm -it --network=host  -p 5775:5775/udp   -p 6831:6831/udp   -p 6832:6832/udp   -p 5778:5778/tcp   jaegertracing/jaeger-agent:1.8  --reporter.tchannel.host-port=10.197.103.140:14267

MODE=test ./plugin/storage/cassandra/schema/create.sh | cqlsh
