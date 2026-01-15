# Multi-cloud example intended for diagram generation tests.
# This is not meant to be applied as-is.

# --- AWS ---
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.10.1.0/24"
  map_public_ip_on_launch = true
}

resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id
}

resource "aws_instance" "web" {
  ami                    = "ami-00000000000000000" # example only
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
}

resource "aws_eks_cluster" "k8s" {
  name     = "example-eks"
  role_arn = "arn:aws:iam::123456789012:role/example" # example only

  vpc_config {
    subnet_ids = [aws_subnet.public.id]
  }

  depends_on = [aws_vpc.main]
}

# --- Azure ---
resource "azurerm_resource_group" "rg" {
  name     = "rg-example"
  location = "eastus"
}

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-example"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.20.0.0/16"]
}

resource "azurerm_subnet" "subnet" {
  name                 = "subnet-example"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.20.1.0/24"]
}

resource "azurerm_network_security_group" "nsg" {
  name                = "nsg-example"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_linux_virtual_machine" "vm" {
  name                = "vm-example"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  size                = "Standard_B2s"

  admin_username = "azureuser"

  network_interface_ids = ["${azurerm_subnet.subnet.id}"] # example only

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-example"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "aks"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_B2s"
  }

  identity {
    type = "SystemAssigned"
  }

  depends_on = [azurerm_virtual_network.vnet]
}

# --- GCP ---
resource "google_compute_network" "vpc" {
  name = "gcp-vpc"
}

resource "google_compute_firewall" "web" {
  name    = "allow-web"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
}

resource "google_compute_instance" "vm" {
  name         = "gce-vm"
  machine_type = "e2-micro"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = google_compute_network.vpc.name
  }

  depends_on = [google_compute_firewall.web]
}

resource "google_container_cluster" "gke" {
  name     = "gke-example"
  location = "us-central1"

  network = google_compute_network.vpc.name

  depends_on = [google_compute_network.vpc]
}

# --- Oracle (OCI) ---
resource "oci_core_vcn" "vcn" {
  cidr_block = "10.30.0.0/16"
  compartment_id = "ocid1.compartment.oc1..example" # example only
  display_name   = "vcn-example"
}

resource "oci_core_subnet" "subnet" {
  cidr_block     = "10.30.1.0/24"
  compartment_id = "ocid1.compartment.oc1..example" # example only
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "subnet-example"
}

resource "oci_core_instance" "vm" {
  compartment_id = "ocid1.compartment.oc1..example" # example only
  availability_domain = "AD-1" # example only
  display_name = "oci-vm"

  create_vnic_details {
    subnet_id = oci_core_subnet.subnet.id
  }
}

# --- IBM Cloud ---
resource "ibm_is_vpc" "vpc" {
  name = "ibm-vpc"
}

resource "ibm_is_instance" "vm" {
  name   = "ibm-vm"
  vpc    = ibm_is_vpc.vpc.id
  profile = "bx2-2x8" # example only
}
