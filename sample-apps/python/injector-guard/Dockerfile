# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
ARG PYTHON_VERSION=3.9
FROM public.ecr.aws/docker/library/python:${PYTHON_VERSION}-slim
RUN pip install --no-cache-dir urllib3==1.26.20
COPY app.py /app.py
EXPOSE 8080
CMD ["python", "/app.py"]
