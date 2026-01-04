# K8S-Installer Skill Research Findings

## 1. Paramiko SSH Best Practices

### Decision: Use `paramiko.SSHClient` with AutoAddPolicy for MVP

### Rationale
- `SSHClient` is a high-level wrapper that handles most complexity (Transport, Channel, authentication)
- Provides a simple, clean API: `connect()` → `exec_command()` → `close()`
- Built-in support for password authentication and timeout handling
- Can be used as context manager for automatic cleanup

### Implementation Pattern

```python
import paramiko
from paramiko import SSHClient, AutoAddPolicy

class SSHConnection:
    def __init__(self, hostname: str, username: str, password: str, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def connect(self, timeout: float = 30.0):
        """Establish SSH connection with timeout handling."""
        self.client = SSHClient()
        # For MVP: auto-add unknown hosts (production would verify keys)
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.connect(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=timeout,           # TCP connect timeout
            banner_timeout=timeout,    # SSH banner timeout
            auth_timeout=timeout       # Authentication timeout
        )
    
    def execute(self, command: str, timeout: int = 300) -> tuple[str, str, int]:
        """Execute command with timeout, return (stdout, stderr, exit_code)."""
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), exit_code
    
    def close(self):
        """Close connection - MUST be called to prevent hangs."""
        if self.client:
            self.client.close()
```

### Error Handling Patterns

```python
from paramiko.ssh_exception import (
    SSHException,
    AuthenticationException,
    NoValidConnectionsError
)
import socket

try:
    ssh.connect(...)
except AuthenticationException:
    # Wrong username/password
    raise SSHError(f"Authentication failed for {hostname}")
except NoValidConnectionsError:
    # Host unreachable (connection refused, etc.)
    raise SSHError(f"Cannot connect to {hostname}")
except socket.timeout:
    # Connection timed out
    raise SSHError(f"Connection to {hostname} timed out")
except SSHException as e:
    # Other SSH errors
    raise SSHError(f"SSH error: {e}")
```

### Connection Pooling for Multiple Hosts

**Decision: Simple sequential connections for MVP**

```python
class SSHConnectionManager:
    """Manage connections to multiple hosts."""
    
    def __init__(self, hosts: list[dict], username: str, password: str):
        self.hosts = hosts
        self.username = username
        self.password = password
        self.connections: dict[str, SSHConnection] = {}
    
    def connect_all(self):
        """Connect to all hosts sequentially."""
        for host in self.hosts:
            conn = SSHConnection(host['ip'], self.username, self.password)
            conn.connect()
            self.connections[host['ip']] = conn
    
    def execute_on_all(self, command: str) -> dict[str, tuple]:
        """Execute command on all connected hosts."""
        results = {}
        for ip, conn in self.connections.items():
            results[ip] = conn.execute(command)
        return results
    
    def close_all(self):
        """Close all connections."""
        for conn in self.connections.values():
            conn.close()
```

### Alternatives Considered
| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Fabric | Higher-level, easier API | Extra dependency, abstracts too much | Not for MVP |
| asyncssh | Async support, better concurrency | Complexity for MVP | Consider for v2 |
| subprocess + ssh | No dependencies | Harder error handling, no password auth | Rejected |

---

## 2. Kubernetes Installation Automation

### Decision: Use kubeadm with containerd runtime

### Rationale
- `kubeadm` is the official Kubernetes bootstrapping tool
- `containerd` is the recommended CRI runtime (Docker Engine requires extra cri-dockerd)
- Well-documented, stable installation path

### Pre-requisites (All Nodes)

```bash
# 1. Disable swap (required by kubelet)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# 2. Load required kernel modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

# 3. Set required sysctl params
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system
```

### Packages to Install

**Debian/Ubuntu Installation:**

```bash
# 1. Install container runtime (containerd)
sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
# Enable systemd cgroup driver
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd

# 2. Add Kubernetes apt repository
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | \
    sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | \
    sudo tee /etc/apt/sources.list.d/kubernetes.list

# 3. Install kubelet, kubeadm, kubectl
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable --now kubelet
```

### Cluster Initialization (Control Plane Node)

```bash
# Initialize control plane
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Configure kubectl for regular user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install CNI (Flannel for simplicity)
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

### Worker Node Join

```bash
# Join command is output by kubeadm init, format:
sudo kubeadm join <control-plane-ip>:6443 \
    --token <token> \
    --discovery-token-ca-cert-hash sha256:<hash>

# If token expired, regenerate on control plane:
kubeadm token create --print-join-command
```

### Installation Sequence

```
1. Prepare ALL nodes (prerequisites + packages)
   ├── Disable swap
   ├── Load kernel modules
   ├── Set sysctl params
   ├── Install containerd
   └── Install kubeadm, kubelet, kubectl

2. Initialize CONTROL PLANE
   ├── kubeadm init
   ├── Configure kubectl
   └── Install CNI (Flannel)

3. Join WORKER nodes
   └── kubeadm join (using token from step 2)
```

### Alternatives Considered
| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| k3s | Lightweight, single binary | Not standard K8s, different tooling | For edge use cases |
| microk8s | Snap-based, easy | Ubuntu-specific, snap limitations | Not for production |
| Manual installation | Full control | Complex, error-prone | Rejected |
| kubeadm (selected) | Official, well-supported | Some complexity | Selected for MVP |

---

## 3. Python CLI with Click

### Decision: Use Click with interactive prompts and loop-based host collection

### Rationale
- Click provides built-in prompt support with type validation
- Simple decorator-based API
- Supports both interactive and non-interactive usage
- Well-documented, actively maintained

### Basic CLI Structure

```python
import click

@click.command()
@click.option('--master-ip', prompt='Master node IP', help='IP address of the K8S master node')
@click.option('--username', prompt='SSH Username', default='root', help='SSH username for all nodes')
@click.option('--password', prompt='SSH Password', hide_input=True, help='SSH password for all nodes')
def install_k8s(master_ip: str, username: str, password: str):
    """Install Kubernetes cluster on specified nodes."""
    click.echo(f"Installing K8S with master: {master_ip}")

if __name__ == '__main__':
    install_k8s()
```

### Collecting Multiple Hosts Interactively

```python
import click

def collect_worker_nodes() -> list[str]:
    """Interactively collect worker node IPs."""
    workers = []
    click.echo("\nEnter worker node IPs (empty line to finish):")
    
    while True:
        ip = click.prompt(
            f"  Worker {len(workers) + 1} IP",
            default='',
            show_default=False
        )
        if not ip:
            break
        # Basic IP validation
        if not validate_ip(ip):
            click.echo(click.style("  Invalid IP format, try again", fg='red'))
            continue
        workers.append(ip)
    
    return workers

def validate_ip(ip: str) -> bool:
    """Simple IP validation."""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False

@click.command()
@click.option('--master-ip', prompt='Master node IP', help='Control plane node IP')
@click.option('--username', prompt='SSH Username', default='root')
@click.option('--password', prompt='SSH Password', hide_input=True, confirmation_prompt=True)
def setup_cluster(master_ip: str, username: str, password: str):
    """Set up a Kubernetes cluster."""
    
    # Validate master IP
    if not validate_ip(master_ip):
        raise click.BadParameter("Invalid IP format", param_hint='master-ip')
    
    # Collect worker nodes interactively
    workers = collect_worker_nodes()
    
    if not workers:
        click.echo(click.style("\nNo workers specified - single node cluster", fg='yellow'))
    
    # Confirm before proceeding
    click.echo(f"\n{click.style('Cluster Configuration:', bold=True)}")
    click.echo(f"  Master: {master_ip}")
    click.echo(f"  Workers: {', '.join(workers) if workers else 'None'}")
    click.echo(f"  SSH User: {username}")
    
    if not click.confirm('\nProceed with installation?'):
        raise click.Abort()
    
    # Proceed with installation...
    click.echo(click.style("\nStarting installation...", fg='green'))
```

### Progress Output Pattern

```python
def show_progress(message: str, status: str = 'running'):
    """Display progress with status indicators."""
    icons = {
        'running': click.style('⏳', fg='yellow'),
        'success': click.style('✓', fg='green'),
        'error': click.style('✗', fg='red'),
    }
    click.echo(f"{icons.get(status, '')} {message}")

# Usage in installation
show_progress("Connecting to master node...", 'running')
# ... do work ...
show_progress("Connected to master node", 'success')
```

### Full CLI Example

```python
#!/usr/bin/env python3
import click
import sys

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """K8S-Installer: Deploy Kubernetes clusters via SSH."""
    pass

@cli.command()
@click.option('--master-ip', prompt='Master node IP address')
@click.option('--username', prompt='SSH username', default='root', show_default=True)
@click.option('--password', prompt='SSH password', hide_input=True)
@click.option('--workers', '-w', multiple=True, help='Worker node IPs (can specify multiple)')
@click.option('--k8s-version', default='1.31', show_default=True, help='Kubernetes version')
def install(master_ip, username, password, workers, k8s_version):
    """Install a new Kubernetes cluster."""
    
    # If no workers provided via CLI, prompt interactively
    if not workers:
        workers = collect_worker_nodes()
    
    click.echo(f"\n{'='*50}")
    click.echo(f"Installing Kubernetes {k8s_version}")
    click.echo(f"Master: {master_ip}")
    click.echo(f"Workers: {list(workers)}")
    click.echo(f"{'='*50}\n")
    
    if not click.confirm('Proceed?', default=True):
        raise click.Abort()
    
    # Installation logic here...

@cli.command()
@click.argument('node_ip')
@click.option('--master-ip', required=True, help='Master node IP to join')
def join(node_ip, master_ip):
    """Join a new worker node to existing cluster."""
    click.echo(f"Joining {node_ip} to cluster at {master_ip}")

if __name__ == '__main__':
    cli()
```

### Alternatives Considered
| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| argparse | Standard library, no deps | Verbose, no prompts | Too basic for interactive |
| Typer | Modern, type hints | Less mature, Click wrapper | Consider for v2 |
| Rich prompts | Beautiful output | Overkill for MVP | Not for MVP |
| Click (selected) | Balanced, stable, prompts | Slight learning curve | Selected |

---

## Summary: MVP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     K8S-Installer CLI                        │
│                     (Click-based CLI)                        │
├─────────────────────────────────────────────────────────────┤
│  Commands:                                                   │
│  - install: Full cluster installation                        │
│  - join: Add worker to existing cluster                      │
│  - status: Check cluster status                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SSH Connection Layer                       │
│                   (Paramiko SSHClient)                       │
├─────────────────────────────────────────────────────────────┤
│  - Password-based authentication                             │
│  - Timeout handling (connect, command)                       │
│  - Error handling (auth, connection, execution)              │
│  - Sequential execution on multiple hosts                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 K8S Installation Scripts                     │
│                    (Shell commands)                          │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Prerequisites (all nodes)                          │
│  Phase 2: Package installation (all nodes)                   │
│  Phase 3: Control plane init (master only)                   │
│  Phase 4: CNI installation (master only)                     │
│  Phase 5: Worker join (workers only)                         │
└─────────────────────────────────────────────────────────────┘
```

### Dependencies for MVP

```
# requirements.txt
paramiko>=3.0.0
click>=8.0.0
```

### Key Design Decisions

1. **SSH**: Use Paramiko SSHClient with AutoAddPolicy for simplicity
2. **Authentication**: Password-only for MVP (SSH keys for v2)
3. **K8S Runtime**: containerd (standard, no extra components needed)
4. **K8S Installer**: kubeadm (official, well-supported)
5. **CNI**: Flannel (simple, works everywhere)
6. **CLI**: Click with interactive prompts
7. **Host Collection**: Loop-based interactive prompts for workers
8. **Concurrency**: Sequential execution (parallel for v2)
