version development

workflow sfkit {
  input {
    String study_id
    Directory? data
    Int num_threads = 2
    String api_url = "https://sfkit.dsde.broadinstitute.org/api"
    String docker = "us-central1-docker.pkg.dev/dsp-artifact-registry/sfkit/sfkit"
  }

  call cli {
    input:
      study_id = study_id,
      data = data,
      num_threads = num_threads,
      api_url = api_url,
      docker = docker,
  }
}

task cli {
  input {
    String study_id
    Directory? data
    Int num_threads
    String api_url
    String docker
  }

  command <<<
      set -xeu

      export PYTHONUNBUFFERED=TRUE
      export SFKIT_PROXY_ON=true
      export SFKIT_API_URL="~{api_url}"
      cd /sfkit

      sfkit auth --study_id "~{study_id}"
      sfkit networking
      sfkit generate_keys

      if [ -n "~{data}" ]; then
        sfkit register_data --data_path "~{data}"
      fi

      sfkit run_protocol
  >>>

  runtime {
    docker: docker
    cpu: num_threads
    memory: "~{num_threads * 8} GB"
  }

  output {
    String out = read_string(stdout())
  }
}
