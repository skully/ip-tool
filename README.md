# IP-Tool

**IP-Tool** is a Python-based utility designed for Kubernetes environments to:
- Detect the container's IP network.
- Check for IP range collisions in a given file.

## 🐍 Running the Script in Python

### **Detect the container’s network**
```sh
python ip_tool.py
```

### **Collect subnets from Kubernetes pods using a specific image: ip-tool:latest**
```sh
python ip_tool.py --collect subnets.txt
```

### **Check for IP range collisions in a given file**
```sh
python ip_tool.py --check-collision subnets.txt
```
---

## 🧪 Running Tests
```sh
pytest tests.py -v
```
