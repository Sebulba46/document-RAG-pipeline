# Guide for making RAG document pipeline for Open-WebUI 
This guide is made to help you deploy your own pipline with Open-WebUI and Local LLM.
## Setup:
  - VLLM running in docker
  - Open-WebUI and pipelines container running in docker
  - Local small 7B Mistral
  - All docker compose
    
  All docker composes are included
## To deploy pipelines use this steps:
  Deploy pipelines container using docker-compose
  
  List all containers:
  ```bash
  docker ps --format '{{.Names}}' 
  ```
  Find your pipeline container.
  Then enter into it, change name of the container if needed:
  ```bash
  docker exec -it open-webui-pipelines-1 /bin/bash
  ```
  Then install all neseccary libraries:
  ```bash
  pip install llama-index llama-index-core llama-index-llms-openai-like llama-index-readers-file pymupdf
  ```
  Then edit your valves:
  
  ![image](https://github.com/user-attachments/assets/1943feb5-9ed9-4cda-a65c-e2b5fb4da8d6)
  
  Edit PATH for your pdf document:
  
  ![image](https://github.com/user-attachments/assets/890e51b7-c1d3-449a-b948-b1347d40c23c)

  
  Choose embeddings that suit your needs:

  ![image](https://github.com/user-attachments/assets/19adb992-6ff9-419c-bde0-526e5d50500a)

  Edit model prompt as you like:

  ![Uploading Screenshot_20250307_170526.png…]()




  


  
