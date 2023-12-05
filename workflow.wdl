version 1.0

workflow sfkit {
  input {
    String study_id
    Int pid = 0
    Array[Int]+ ports = [8020, 8040]
    String api_url = "https://sfkit.dsde-dev.broadinstitute.org/api"
  }

  call cli {
    input:
      study_id = study_id,
      pid = pid,
      ports = ports,
      api_url = api_url
  }
}

task cli {
  input {
    String study_id
    Int pid
    Array[Int]+ ports
    String api_url
  }

  command <<<
      echo "Study ID: ~{study_id}, PID: ~{pid}"
      grep -rH . /proc/sys/net/core

      set -euv
      pwd

      export PYTHONUNBUFFERED=TRUE
      export SKFIT_PROXY_ON=true
      export SFKIT_API_URL="~{api_url}"

      sfkit auth
      sfkit networking --ports "~{sep=',' ports}"
      sfkit generate_keys
      sfkit run_protocol
  >>>

  output {
    String out = read_string(stdout())
  }

  Int cpu = 2

  runtime {
    docker: "us-central1-docker.pkg.dev/dsp-artifact-registry/sfkit/sfkit"
    cpu: cpu
    memory: "~{cpu * 8} GB"
  }
}
