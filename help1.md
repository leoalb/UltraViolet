# Container Help

## Expose multiple ports on container


> addhost("d1", ip="10.0.0.1", cls=Docker, dimage="ubuntu:trusty", ports=[(1111, 'udp'), 2222], port_bindings={'1111/udp':4567, 2222:2222}, publish_all_ports=True)


## Add Shared Volumes inside the container


> addhost("d1", ip="10.0.0.1", cls=Docker, dimage="ubuntu:trusty", volumes=["/host/directory:/container/directory", "/container/directory:/container/directory"])


## Set Maximum memory limit of containers


> addhost("d1", ip="10.0.0.1", cls=Docker, dimage="ubuntu:trusty", mem_limit="512m", memswap_limit="1024m")

