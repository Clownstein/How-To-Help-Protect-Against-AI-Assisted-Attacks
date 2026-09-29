# 7. Preventing proxy bypass

A proxy deny provides little protection if a compromised process can connect around the proxy.

At the perimeter firewall, permit workloads to reach only the proxy and explicitly approved services:

```text
workload VLAN -> proxy IP:3128      ALLOW
workload VLAN -> approved services  ALLOW
workload VLAN -> Internet TCP/443   DENY
workload VLAN -> Internet TCP/80    DENY
workload VLAN -> Internet UDP/443   DENY
```

Only the proxy is granted direct Internet access. Denying UDP/443 prevents QUIC (HTTP/3) connections that would otherwise leave without passing through a TCP proxy.

In cloud environments, apply the same separation using:

- Separate subnets for workloads and egress infrastructure
- NAT and firewall gateways
- Route tables
- Security groups
- Network ACLs
- Service endpoints and private endpoints for approved cloud services

This makes the proxy the single policy enforcement point.

Destination-IP rules for CDN addresses do not replace this control. A process permitted to open raw TCP/443 connections can reach whichever address `api.openai.com` currently resolves to, including addresses shared with unrelated customers, and so regains access to Claude, GPT, Gemini, or a hosted frontier open-weight model. Closing that path does not depend on preventing the process from running a small local model. It depends on preventing the process from reaching the APIs that are the only practical source of frontier capability on ordinary servers.

## Encrypted Client Hello

Encrypted Client Hello (ECH) hides the SNI from network inspection. Where a proxy or firewall relies on SNI, clients that negotiate ECH through a CDN front end can evade hostname matching. Mitigations are to require clients to use the explicit proxy (which sees the `CONNECT` hostname), to deny DNS HTTPS/SVCB lookups that carry ECH configurations at your resolver, and to disable ECH in managed browsers through policy.
