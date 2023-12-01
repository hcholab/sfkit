version 1.0

workflow sfkit {
  input {
    String study_id
    Int pid = 0
  }

  call cli {
    input:
      study_id = study_id,
      pid = pid
  }
}

task cli {
  input {
    String study_id
    Int pid = 0
  }

  command <<<
      echo "Study ID: ~{study_id}, PID: ~{pid}"
  >>>

  output {
    String out = read_string(stdout())
  }

  runtime {
    docker: "us-central1-docker.pkg.dev/dsp-artifact-registry/sfkit/sfkit"
  }
}
