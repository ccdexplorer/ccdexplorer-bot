ARG python_image_tag="3.11-slim-buster"
FROM python:${python_image_tag}
WORKDIR /root/code
RUN cd /root/code

# Install Python dependencies.
COPY ./requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
# Copy application files.
COPY . .

CMD ["python3", "/root/code/main.py"]