### This is a complete installation guide to replicate this project in your local using necessary libraries and tools assuming you have python installed and a Linux distribution (Ubuntu24.04 used here) either in **WSL** or **DualBoot**.



# Setup Docker
    1. sudo apt-get install ca-certificates curl
    2. sudo install -m 0755 -d /etc/apt/keyrings
    3. sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    4. sudo chmod a+r /etc/apt/keyrings/docker.asc
    5. echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    6. sudo apt-get update
    7. sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

### ✅Now docker is installed in your linux system



# Pull required images
## Configuring any nvidia related packages so our linux identifies the GPU
    1. curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    2. sudo apt-get update
    3. sudo apt-get install -y nvidia-container-toolkit
    4. sudo nvidia-ctk runtime configure --runtime=docker
    5. docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi



## Pulling OLLAMA image and configuring it to run on NVIDIA GPU (if you want to run on CPU only, remove "--gpu=all" parameter)
    6. docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    7. docker exec -it ollama ollama pull deepseek-r1:7b
### ✅Now OLLAMA is running in your background



## Pulling elastic search image and running it on 9200 port with **disabled authentication**
    8. docker pull elasticsearch:8.0.0
    9. docker run -d -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.0.0
### ✅Now ElasticSearch is running in your background



## Install Python requirements
    pip install -r requirements.txt



## Run the code
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload 




#### If you want to see your system specs while running this code execute this in a new terminal
    sudo apt install btop -y
    and run **btop**




