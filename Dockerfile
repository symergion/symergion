# Use docker image of your preference with git, Python>=3.10.13, PyTorchi>=2.2.1, Transformers>=4.50.3 installed
ARG BASE_CONTAINER
FROM ${BASE_CONTAINER}

# Copy Symergion code into container
WORKDIR /app
COPY ./README.md /app
COPY ./start.py /app
COPY ./observer.py /app
COPY ./git /app/git
COPY ./handler /app/handler
COPY ./symergion /app/symergion
COPY ./symerg /app/symerg
COPY ./ergon /app/ergon
COPY ./utils /app/utils

# Copy unit tests into container
RUN mkdir /test
COPY ./test/model /test/model
COPY ./test/test_ergon_base.py /test
COPY ./test/test_ergon_code.py /test
COPY ./test/test_ergon_prompt.py /test
COPY ./test/test_git_branches.py /test
COPY ./test/test_git_repository.py /test
COPY ./test/test_handler_base.py /test
COPY ./test/test_handler_coding.py /test
COPY ./test/test_symerg_base.py /test
COPY ./test/test_symerg_coder.py /test
COPY ./test/test_symerg_reasoner.py /test
COPY ./test/test_symergion_base.py /test
COPY ./test/test_symergion_coding.py /test
COPY ./test/test_symergion_config.py /test
COPY ./test/test_utils_cache.py /test
COPY ./test/test_utils_capture_output.py /test
COPY ./test/test_utils_create_test_ergon.py /test
COPY ./test/test_utils_file_exists.py /test
COPY ./test/test_utils_flatten.py /test
COPY ./test/test_utils_read_text_file.py /test
COPY ./test/test_utils_verified_file_name.py /test


# Run tests
RUN python -m unittest discover /test

# Remove unit tests from the container
RUN rm -rf /test

# Start symergion
ENTRYPOINT ["python", "-i", "/app/start.py"]

