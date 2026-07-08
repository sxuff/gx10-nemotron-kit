# GX10 Setup Notes

First-pass checklist:

```bash
sudo usermod -aG docker "$USER"
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Log out and back in after adding your user to the docker group.

Useful checks:

```bash
./scripts/doctor.sh
docker info
nvidia-smi
```

