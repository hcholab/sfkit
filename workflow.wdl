version development

workflow sfkit {
  input {
    String study_id
    Int num_threads = 2
    Int num_parties = 2
    String api_url = "https://sfkit.dsde.broadinstitute.org/api"
    Directory? data
  }

  call cli {
    input:
      study_id = study_id,
      num_threads = num_threads,
      num_parties = num_parties,
      api_url = api_url,
      data = data,
  }
}

task cli {
  input {
    String study_id
    Int num_threads
    Int num_parties
    String api_url
    Directory? data
  }

  command <<<
      set -xeu

      export PYTHONUNBUFFERED=TRUE
      export SKFIT_PROXY_ON=true
      export SFKIT_API_URL="~{api_url}"
      cd /sfkit

      python >ports.txt <<CODE
      print(','.join([str(8100 + ~{num_threads} * p) for p in range(~{num_parties})]))
      CODE

      sfkit auth --study_id "~{study_id}"
      sfkit networking --ports "$(<ports.txt)"
      sfkit generate_keys

      if [ -n "~{data}" ]; then
        sfkit register_data --data_path "~{data}"
      fi

      # NOTE: we can't set sysctl in WDL environment, so just leave it alone
      sfkit run_protocol
  >>>

  output {
    String out = read_string(stdout())
  }

  runtime {
    docker: "us-central1-docker.pkg.dev/dsp-artifact-registry/sfkit/sfkit"
    cpu: num_threads
    memory: "~{num_threads * 8} GB"
  }
}
