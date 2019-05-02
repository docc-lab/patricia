#!/bin/sh

#Patricia: Provenance, Auditing and Tracing in CEPH
#
#Copyright 2019 NetApp Inc.
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
#to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR 
#THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
#Contributor(s): Peter Macko, Mania Abdi


# setup collector
sudo docker run -it --network=host -e SPAN_STORAGE_TYPE=cassandra  -e CASSANDRA_SERVERS=127.0.0.1 -e CASSANDRA_PORT=9042  jaegertracing/jaeger-collector:1.8 &

# setup query
sudo docker run --rm -it --network=host  -e CASSANDRA_SERVERS=10.197.103.143 -e CASSANDRA_PORT=9042 -p 16686:16686 jaegertracing/jaeger-query &

#setup agent
sudo docker run   --rm -it --network=host  -p 5775:5775/udp   -p 6831:6831/udp   -p 6832:6832/udp   -p 5778:5778/tcp   jaegertracing/jaeger-agent:1.8  --reporter.tchannel.host-port=10.197.103.140:14267

MODE=test ./plugin/storage/cassandra/schema/create.sh | cqlsh
