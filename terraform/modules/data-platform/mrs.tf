resource "huaweicloud_mapreduce_cluster" "ayco" {
  name               = "ayco-mrs"
  availability_zone  = "la-north-2a"
  version            = var.mrs_version
  type               = "ANALYSIS"
  safe_mode          = true
  vpc_id             = var.vpc_id
  subnet_id          = var.subnet_id
  manager_admin_pass = var.dws_admin_password
  node_key_pair      = var.keypair_name

  component_list = [
    "Hadoop", "Spark", "Hive", "HBase", "Loader"
  ]

  master_nodes {
    flavor            = "c6.2xlarge.4.linux.bigdata"
    node_number       = 2
    root_volume_type  = "GPSSD"
    root_volume_size  = 100
    data_volume_count = 1
    data_volume_type  = "GPSSD"
    data_volume_size  = 200
  }

  analysis_core_nodes {
    flavor            = "c6.4xlarge.4.linux.bigdata"
    node_number       = 3
    root_volume_type  = "GPSSD"
    root_volume_size  = 100
    data_volume_count = 1
    data_volume_type  = "GPSSD"
    data_volume_size  = 500
  }

  tags = {
    project = "ayco"
    role    = "big-data"
  }
}
