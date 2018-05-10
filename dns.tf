resource "null_resource" "update_dns" {
  depends_on = ["openstack_compute_floatingip_associate_v2.fip_master"]

  provisioner "local-exec" {
    command = "docker run -v `pwd`/scripts:/scripts craigwillis/wt-python python scripts/godaddy-update-dns.py -k ${var.godaddy_api_key} -s ${var.godaddy_api_secret} -d ${var.domain} -n ${var.subdomain} -a ${openstack_networking_floatingip_v2.swarm_master_ip.address}"
  }

}