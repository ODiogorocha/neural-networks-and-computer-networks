#include <core.p4>
#include <v1model.p4>

typedef bit<48> mac_addr_t;
typedef bit<32> ip4_addr_t;

header ethernet_t {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16>   ether_type;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   total_len;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   frag_offset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdr_checksum;
    ip4_addr_t src_addr;
    ip4_addr_t dst_addr;
}

struct headers {
    ethernet_t ethernet;
    ipv4_t     ipv4;
}

struct metadata { }

parser MyParser(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type) {
            0x0800: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }
}

control MyVerifyChecksum(inout headers hdr, inout metadata meta) { apply { } }

control MyIngress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop(standard_metadata);
    }
    action ipv4_forward(bit<9> port) {
        standard_metadata.egress_spec = port;
    }
    table dscp_table {
        key = { hdr.ipv4.dst_addr: exact; }
        actions = { ipv4_forward; drop; }
        default_action = drop();
    }
    apply {
        if (hdr.ipv4.isValid()) {
            dscp_table.apply();
        }
    }
}

control MyEgress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) { apply { } }
control MyComputeChecksum(inout headers hdr, inout metadata meta) { apply { } }

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
    }
}

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;